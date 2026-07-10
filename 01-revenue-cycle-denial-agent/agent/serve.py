# agent/serve.py — minimal AgentCore Runtime contract (/invocations + /ping).
#
# SECURE BY DEFAULT. The shipped image sets AUTH_REQUIRE_JWT=1 and
# AUTH_REQUIRE_BOUND_APPROVAL=1. When AUTH_REQUIRE_JWT is on, this endpoint is the
# edge authorizer: it requires a cryptographically verified JWT (a Bearer token,
# verified against a configured JWKS) and DERIVES the acting user's identity from
# that token. Caller-supplied ``acting_user_claims`` in the request body are NEVER
# trusted — they are replaced by the verified claims, and any defect fails closed
# (HTTP 401). This is what keeps a bare ALB from letting a caller assert its own
# roles/approvals in the body.
#
# Behind Amazon Bedrock AgentCore this pairs with AgentCore Identity; behind a raw
# ALB / API Gateway it REQUIRES an OIDC/JWT authorizer in front (which forwards the
# verified token). The Streamlit/CLI demo (EXTRACT_MODE=demo) needs an explicit
# AUTH_REQUIRE_JWT=0 override — see this agent's README ("Container auth contract").
from __future__ import annotations
import json, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "01-revenue-cycle-denial-agent")]
from agent.core import run_until_gate, resume  # noqa: E402
from hpp_agent_platform import jwt_verify  # noqa: E402


class AuthError(Exception):
    """Edge authorization failed — fail closed (HTTP 401)."""


def _auth_required() -> bool:
    return os.getenv("AUTH_REQUIRE_JWT", "").strip().lower() in ("1", "true", "yes")


def load_jwks() -> Optional[Dict[str, Any]]:
    """Verification JWKS supplied out-of-band: AUTH_JWKS (inline JSON) or
    AUTH_JWKS_PATH (a file). Returns None when neither is configured."""
    raw = os.getenv("AUTH_JWKS")
    if raw:
        return json.loads(raw)
    path = os.getenv("AUTH_JWKS_PATH")
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return None


def _bearer(auth_header: Optional[str]) -> Optional[str]:
    if auth_header and auth_header.strip().lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


def resolve_identity(payload: Dict[str, Any], auth_header: Optional[str] = None) -> Dict[str, Any]:
    """Return the acting user's claims to run the workflow with.

    * AUTH_REQUIRE_JWT off (demo/fixture posture): the body's ``acting_user_claims``
      are used as presented.
    * AUTH_REQUIRE_JWT on (the shipped image default): identity MUST come from a
      verified JWT. A Bearer token — from the ``Authorization`` header, or a ``jwt``
      an upstream authorizer placed inside the body claims — is verified against the
      configured JWKS and its claims REPLACE whatever the caller put in
      ``acting_user_claims``. A missing/invalid token, or a missing JWKS, raises
      AuthError (fail closed): a body with caller-supplied claims and no verified
      token is rejected, so claims can never be spoofed through the request body.
    """
    if not _auth_required():
        return payload.get("acting_user_claims") or {}
    token = _bearer(auth_header) or (payload.get("acting_user_claims") or {}).get("jwt")
    if not token:
        raise AuthError("AUTH_REQUIRE_JWT=1 but no verified JWT presented; "
                        "body-supplied acting_user_claims are not trusted")
    jwks = load_jwks()
    if not jwks:
        raise AuthError("AUTH_REQUIRE_JWT=1 but no JWKS configured "
                        "(set AUTH_JWKS or AUTH_JWKS_PATH)")
    try:
        claims = jwt_verify.verify_jwt(
            token, jwks=jwks,
            issuer=os.getenv("AUTH_JWT_ISSUER") or None,
            audience=os.getenv("AUTH_JWT_AUDIENCE") or None,
        )
    except jwt_verify.JWTError as exc:
        raise AuthError(f"JWT verification failed: {exc}") from exc
    # Carry the raw token forward so the gateway re-verifies (defense in depth) and
    # never relies on caller-asserted roles.
    return {**claims, "jwt": token}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.end_headers(); self.wfile.write(json.dumps(body).encode())

    def do_GET(self):
        if self.path == "/ping":
            self._send(200, {"status": "healthy"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/invocations":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        try:
            # Fail closed: derive verified identity; never trust body-supplied claims.
            payload["acting_user_claims"] = resolve_identity(
                payload, self.headers.get("Authorization"))
        except AuthError as exc:
            return self._send(401, {"error": "unauthorized", "detail": str(exc)})
        state = run_until_gate(payload)
        if payload.get("human_approval"):
            state = resume(state, approval=payload["human_approval"])
        state.pop("_paused_at_gate", None)
        self._send(200, state)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
