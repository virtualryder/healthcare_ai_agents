"""
Sandbox connector tests — prove the production controls (auth, idempotency, retries,
timeout/circuit breaker, reconciliation, lineage) with an injected transport (no network).
"""
import json

import pytest

from hpp_agent_platform.connectors.sandbox import (
    CircuitOpenError, ConnectorHTTPError, SandboxHttpConnector, StaticBearerAuth,
    _CircuitBreaker, _idempotency_key,
)


class FakeTransport:
    """Scripts responses per connector method; records every request."""
    def __init__(self, script):
        self.script = {k: list(v) for k, v in script.items()}   # method -> [(status, dict), ...]
        self.calls = []

    def __call__(self, url, *, method_http, headers, body, timeout):
        method = url.rsplit("/", 1)[-1]
        self.calls.append({"method": method, "headers": dict(headers),
                           "body": json.loads(body or b"{}")})
        queue = self.script.get(method) or [(200, {"ok": True, "method": method})]
        status, payload = queue.pop(0) if len(queue) > 1 else queue[0]
        return status, json.dumps(payload).encode()


def _conn(transport, **kw):
    return SandboxHttpConnector("payer", "https://sandbox.example/payer", auth=StaticBearerAuth("k-123"),
                                transport=transport, backoff_base=0.0, sleep=lambda s: None, **kw)


def test_auth_and_idempotency_headers():
    t = FakeTransport({"submit_appeal": [(200, {"appeal_ref": "APL-1", "claim_ref": "CLM-1"})],
                       "check_claim_status": [(200, {"status": "Denied"})],
                       "get_claim": [(200, {"claim_ref": "CLM-1"})]})
    c = _conn(t)
    c.get_claim(claim_ref="CLM-1")                                   # read
    c.submit_appeal(claim_ref="CLM-1", level=1)                      # write
    read = next(x for x in t.calls if x["method"] == "get_claim")
    write = next(x for x in t.calls if x["method"] == "submit_appeal")
    assert read["headers"]["Authorization"] == "Bearer k-123"
    assert "Idempotency-Key" not in read["headers"]                 # reads are not keyed
    assert write["headers"]["Idempotency-Key"] == _idempotency_key("payer", "submit_appeal",
                                                                    {"claim_ref": "CLM-1", "level": 1})


def test_idempotency_key_is_stable_across_retries():
    k1 = _idempotency_key("payer", "submit_appeal", {"claim_ref": "CLM-1", "level": 1})
    k2 = _idempotency_key("payer", "submit_appeal", {"level": 1, "claim_ref": "CLM-1"})  # arg order
    assert k1 == k2


def test_retries_then_succeeds_and_records_lineage():
    t = FakeTransport({"get_claim": [(503, {}), (503, {}), (200, {"claim_ref": "CLM-1"})]})
    c = _conn(t)
    res = c.get_claim(claim_ref="CLM-1")
    assert res["claim_ref"] == "CLM-1"
    assert c.last_lineage["attempts"] == 3
    assert c.last_lineage["http_status"] == 200
    assert c.last_lineage["request_id"]
    assert c.last_lineage["system"] == "payer"


def test_non_retryable_4xx_fails_closed():
    t = FakeTransport({"get_claim": [(404, {"error": "not found"})]})
    c = _conn(t)
    with pytest.raises(ConnectorHTTPError):
        c.get_claim(claim_ref="CLM-X")


def test_circuit_breaker_opens_then_recovers():
    clock = {"t": 1000.0}
    t = FakeTransport({"get_claim": [(503, {})]})  # always failing
    c = _conn(t, breaker=_CircuitBreaker(threshold=2, cooldown=30.0),
              clock=lambda: clock["t"], max_attempts=1)
    for _ in range(2):
        with pytest.raises(ConnectorHTTPError):
            c.get_claim(claim_ref="CLM-1")
    # breaker now open -> fail fast without calling the transport
    before = len(t.calls)
    with pytest.raises(CircuitOpenError):
        c.get_claim(claim_ref="CLM-1")
    assert len(t.calls) == before
    # after cooldown a trial is allowed again
    clock["t"] += 31
    t.script["get_claim"] = [(200, {"claim_ref": "CLM-1"})]
    assert c.get_claim(claim_ref="CLM-1")["claim_ref"] == "CLM-1"


def test_write_reconciliation_captured():
    t = FakeTransport({"submit_appeal": [(200, {"appeal_ref": "APL-1", "claim_ref": "CLM-1"})],
                       "check_claim_status": [(200, {"status": "Denied", "claim_ref": "CLM-1"})]})
    c = _conn(t)
    c.submit_appeal(claim_ref="CLM-1", level=1)
    rec = c.last_lineage["reconciliation"]
    assert rec and rec["read"] == "check_claim_status" and rec["confirmed"] is True
    assert rec["status"] == "Denied"


def test_factory_sandbox_mode(monkeypatch):
    from hpp_agent_platform.connectors import get_connector
    monkeypatch.setenv("PAYER_BASE_URL", "https://sandbox.example/payer")
    conn = get_connector("payer", "sandbox")
    assert isinstance(conn, SandboxHttpConnector)
