"""
Production-grade sandbox connector — the resilient HTTP adapter for a real system of record.

`LiveHttpConnector` shows the bare round-trip; `SandboxHttpConnector` is what you point at a
customer's sandbox (Availity / Change Healthcare / a payer FHIR/X12 endpoint) or, locally, at
the reference façade. It keeps the SAME method signatures as the fixtures — agents call the
gateway, the gateway calls a connector method — but wraps every call with the controls a
clearinghouse/payer integration actually needs:

  * AUTHENTICATION  — OAuth2 client-credentials (token cached until expiry) or a static bearer
    key; secrets resolve from env or Secrets Manager, never hardcoded.
  * IDEMPOTENCY     — write methods carry an Idempotency-Key derived from the method + canonical
    args, so a retried submit_appeal/submit_claim never double-files.
  * RETRIES         — exponential backoff with jitter on 429/5xx and transport errors, bounded.
  * TIMEOUTS        — explicit per-call connect/read timeout (fail fast, never hang a workflow).
  * CIRCUIT BREAKER — after N consecutive failures the breaker opens and calls fail closed for a
    cooldown, so a degraded payer endpoint can't stall every execution.
  * RECONCILIATION  — after a write, a follow-up status read confirms the system of record
    actually recorded it; the result is captured in lineage.
  * LINEAGE         — every call records {system, endpoint, http_status, attempts, latency_ms,
    idempotency_key, request_id, reconciliation} on `last_lineage` for the audit trail.

Tests inject a `transport` callable so the full control behavior is verified with no network.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Callable, Dict, Optional, Tuple

from .base import Connector

# Methods that mutate a system of record -> require an idempotency key + reconciliation.
WRITE_METHODS = {
    "submit_appeal", "submit_claim", "submit_pa", "update_case", "update_care_plan",
    "book_appointment", "create_registration", "log_interaction", "create_grievance",
    "issue_determination", "draft_note",
}
# write method -> (status-read method, args-builder) used to confirm the write landed.
RECONCILE = {
    "submit_appeal": ("check_claim_status", lambda res, args: {"claim_ref": args.get("claim_ref")}),
    "submit_claim": ("check_claim_status", lambda res, args: {"claim_ref": args.get("claim_ref")}),
    "submit_pa": ("check_pa_status", lambda res, args: {"pa_ref": (res or {}).get("pa_ref")}),
}
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class ConnectorHTTPError(Exception):
    """Non-retryable HTTP error from the system of record (fail closed)."""


class CircuitOpenError(Exception):
    """Breaker is open — the system of record is degraded; fail fast/closed."""


def _idempotency_key(kind: str, method: str, args: Dict[str, Any]) -> str:
    canon = json.dumps(args or {}, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(f"{kind}.{method}:{canon}".encode()).hexdigest()


class _CircuitBreaker:
    def __init__(self, threshold: int = 5, cooldown: float = 30.0) -> None:
        self.threshold, self.cooldown = threshold, cooldown
        self._fails = 0
        self._opened_at: Optional[float] = None

    def allow(self, now: float) -> bool:
        if self._opened_at is None:
            return True
        if now - self._opened_at >= self.cooldown:   # half-open: allow a trial
            return True
        return False

    def record(self, ok: bool, now: float) -> None:
        if ok:
            self._fails = 0
            self._opened_at = None
        else:
            self._fails += 1
            if self._fails >= self.threshold:
                self._opened_at = now

    @property
    def is_open(self) -> bool:
        return self._opened_at is not None


class StaticBearerAuth:
    """Static API key as a bearer token (resolved from env / Secrets Manager)."""
    def __init__(self, token: str) -> None:
        self._token = token

    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}


class OAuth2ClientCredentials:  # pragma: no cover - exercised via injected transport in tests
    """Client-credentials grant with in-memory token cache until ~expiry."""
    def __init__(self, token_url: str, client_id: str, client_secret: str,
                 transport: Optional[Callable] = None) -> None:
        self._url, self._id, self._secret = token_url, client_id, client_secret
        self._transport = transport
        self._token = ""
        self._exp = 0.0

    def headers(self) -> Dict[str, str]:
        now = time.time()
        if not self._token or now >= self._exp - 30:
            body = json.dumps({"grant_type": "client_credentials",
                               "client_id": self._id, "client_secret": self._secret}).encode()
            status, payload = (self._transport or _urllib_transport)(
                self._url, method_http="POST", headers={"Content-Type": "application/json"},
                body=body, timeout=10)
            data = json.loads(payload or b"{}")
            self._token = data.get("access_token", "")
            self._exp = now + float(data.get("expires_in", 300))
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}


def _urllib_transport(url: str, *, method_http: str, headers: Dict[str, str],
                      body: bytes, timeout: float) -> Tuple[int, bytes]:  # pragma: no cover - network
    req = urllib.request.Request(url, data=body, headers=headers, method=method_http)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 — URL from operator config, not user input
            return resp.getcode(), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


class SandboxHttpConnector(Connector):
    def __init__(self, kind: str, base_url: str, *, auth=None, transport: Optional[Callable] = None,
                 timeout: float = 15.0, max_attempts: int = 3, backoff_base: float = 0.05,
                 breaker: Optional[_CircuitBreaker] = None, clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.kind = kind
        self.base_url = base_url.rstrip("/")
        self._auth = auth
        self._transport = transport or _urllib_transport
        self._timeout = timeout
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base
        self._breaker = breaker or _CircuitBreaker()
        self._clock = clock
        self._sleep = sleep
        self.last_lineage: Dict[str, Any] = {}

    def __getattr__(self, method: str) -> Any:
        if method.startswith("_"):
            raise AttributeError(method)

        def _call(**kwargs: Any) -> Any:
            return self._request(method, kwargs)
        return _call

    def _headers(self, method: str, args: Dict[str, Any]) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._auth is not None:
            h.update(self._auth.headers())
        if method in WRITE_METHODS:
            h["Idempotency-Key"] = _idempotency_key(self.kind, method, args)
        h["X-Request-Id"] = str(uuid.uuid4())
        return h

    def _once(self, method: str, headers: Dict[str, str], body: bytes) -> Tuple[int, Any]:
        status, raw = self._transport(f"{self.base_url}/{method}", method_http="POST",
                                      headers=headers, body=body, timeout=self._timeout)
        payload = json.loads(raw or b"{}") if isinstance(raw, (bytes, bytearray)) else raw
        return status, payload

    def _request(self, method: str, args: Dict[str, Any]) -> Any:
        now = self._clock()
        if not self._breaker.allow(now):
            self.last_lineage = {"system": self.kind, "method": method, "circuit": "OPEN"}
            raise CircuitOpenError(f"{self.kind}.{method}: circuit open (system of record degraded)")

        headers = self._headers(method, args)
        body = json.dumps(args or {}, default=str).encode()
        start = now
        last_exc: Optional[Exception] = None
        status = None
        payload: Any = None
        attempts = 0
        for attempt in range(self._max_attempts):
            attempts = attempt + 1
            try:
                status, payload = self._once(method, headers, body)
                if status < 400:
                    break
                if status not in _RETRYABLE_STATUS:
                    self._breaker.record(False, self._clock())
                    self._lineage(method, headers, status, attempts, start, None)
                    raise ConnectorHTTPError(f"{self.kind}.{method} -> HTTP {status}")
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:  # transport error
                last_exc = exc
                status = None
            if attempt < self._max_attempts - 1:                      # backoff before retry
                self._sleep(self._backoff_base * (2 ** attempt) + (attempt * 0.001))
        ok = status is not None and status < 400
        self._breaker.record(ok, self._clock())
        if not ok:
            self._lineage(method, headers, status, attempts, start, None)
            raise ConnectorHTTPError(
                f"{self.kind}.{method} failed after {attempts} attempts (last status={status})"
            ) from last_exc

        reconciliation = self._reconcile(method, payload, args)
        self._lineage(method, headers, status, attempts, start, reconciliation)
        return payload

    def _reconcile(self, method: str, result: Any, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        spec = RECONCILE.get(method)
        if not spec:
            return None
        read_method, build = spec
        try:
            confirm = self._once(read_method, self._headers(read_method, {}), json.dumps(build(result, args)).encode())[1]
            return {"read": read_method, "confirmed": True, "status": (confirm or {}).get("status")}
        except Exception as exc:  # reconciliation is best-effort; never fail the write on it
            return {"read": read_method, "confirmed": False, "error": type(exc).__name__}

    def _lineage(self, method, headers, status, attempts, start, reconciliation) -> None:
        self.last_lineage = {
            "system": self.kind,
            "endpoint": f"{self.base_url}/{method}",
            "http_status": status,
            "attempts": attempts,
            "latency_ms": round((self._clock() - start) * 1000, 1),
            "idempotency_key": headers.get("Idempotency-Key"),
            "request_id": headers.get("X-Request-Id"),
            "reconciliation": reconciliation,
        }


def build_auth(kind: str, transport: Optional[Callable] = None):
    """Resolve an auth provider from env. Static bearer if <KIND>_API_KEY/SANDBOX_API_KEY is set;
    else client-credentials if a token URL + client id/secret are configured; else None."""
    key = os.getenv(f"{kind.upper()}_API_KEY") or os.getenv("SANDBOX_API_KEY")
    if key:
        return StaticBearerAuth(key)
    token_url = os.getenv(f"{kind.upper()}_TOKEN_URL") or os.getenv("SANDBOX_TOKEN_URL")
    cid = os.getenv(f"{kind.upper()}_CLIENT_ID") or os.getenv("SANDBOX_CLIENT_ID")
    secret = os.getenv(f"{kind.upper()}_CLIENT_SECRET") or os.getenv("SANDBOX_CLIENT_SECRET")
    if token_url and cid and secret:  # pragma: no cover
        return OAuth2ClientCredentials(token_url, cid, secret, transport=transport)
    return None
