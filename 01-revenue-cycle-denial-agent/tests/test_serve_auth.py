"""Container auth-contract tests for the shipped Agent-01 image.

The image sets AUTH_REQUIRE_JWT=1 + AUTH_REQUIRE_BOUND_APPROVAL=1 so the /invocations
runtime path is SECURE BY DEFAULT: it derives identity from a cryptographically verified
JWT and NEVER trusts caller-supplied ``acting_user_claims`` in the request body. These
tests prove the two halves of that contract:

  * with AUTH_REQUIRE_JWT=1 and no valid token, a body carrying caller-supplied claims
    is REJECTED (fail closed) — even claims that assert a privileged role;
  * a genuinely verified JWT is accepted and its claims REPLACE the body's;
  * demo mode (AUTH_REQUIRE_JWT off) still runs end-to-end.

They also confirm the gateway layer refuses body-asserted claims when AUTH_REQUIRE_JWT=1
without a JWKS (defense in depth behind serve.py).
"""
import base64
import json
import sys
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "01-revenue-cycle-denial-agent")]

from agent import serve  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402
from agent.state import RecommendedAction  # noqa: E402
from hpp_agent_platform import jwt_verify  # noqa: E402
from hpp_agent_platform.mcp_gateway import MCPGateway  # noqa: E402


# ── helpers: real RS256 JWT + JWKS (mirrors platform_core/tests) ─────────────
def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _rsa_keypair_and_jwks(kid="k1"):
    from cryptography.hazmat.primitives.asymmetric import rsa
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key().public_numbers()
    jwk = {"kty": "RSA", "kid": kid, "n": _b64u(pub.n.to_bytes(256, "big")),
           "e": _b64u(pub.e.to_bytes(3, "big"))}
    return key, {"keys": [jwk]}


def _sign_rs256(key, claims, kid="k1"):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    h = _b64u(json.dumps({"alg": "RS256", "kid": kid, "typ": "JWT"}).encode())
    p = _b64u(json.dumps(claims).encode())
    sig = key.sign(f"{h}.{p}".encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{h}.{p}.{_b64u(sig)}"


# A caller trying to assert a privileged role straight from the request body.
SPOOFED_BODY_CLAIMS = {"sub": "attacker", "custom:hpp_role": "DENIALS_MANAGER"}


def test_require_jwt_rejects_body_claims_without_token(monkeypatch):
    """The core finding: AUTH_REQUIRE_JWT=1, no Bearer token -> body claims are refused."""
    monkeypatch.setenv("AUTH_REQUIRE_JWT", "1")
    payload = {"claim_ref": "CLM-2026-55810", "acting_user_claims": SPOOFED_BODY_CLAIMS}
    with pytest.raises(serve.AuthError):
        serve.resolve_identity(payload, auth_header=None)


def test_require_jwt_rejects_body_supplied_jwt_key_without_jwks(monkeypatch):
    """Even a `jwt` in the body cannot be trusted with no verifier JWKS configured."""
    monkeypatch.setenv("AUTH_REQUIRE_JWT", "1")
    monkeypatch.delenv("AUTH_JWKS", raising=False)
    monkeypatch.delenv("AUTH_JWKS_PATH", raising=False)
    payload = {"acting_user_claims": {**SPOOFED_BODY_CLAIMS, "jwt": "not.a.jwt"}}
    with pytest.raises(serve.AuthError):
        serve.resolve_identity(payload, auth_header=None)


def test_require_jwt_rejects_invalid_signature(monkeypatch):
    """A token signed by a key that is NOT in the JWKS fails verification -> reject."""
    _, jwks = _rsa_keypair_and_jwks(kid="k1")
    wrong_key, _ = _rsa_keypair_and_jwks(kid="k1")  # different private key, same kid
    forged = _sign_rs256(wrong_key, {"sub": "attacker", "exp": int(time.time()) + 300})
    monkeypatch.setenv("AUTH_REQUIRE_JWT", "1")
    monkeypatch.setenv("AUTH_JWKS", json.dumps(jwks))
    payload = {"acting_user_claims": SPOOFED_BODY_CLAIMS}
    with pytest.raises(serve.AuthError):
        serve.resolve_identity(payload, auth_header=f"Bearer {forged}")


def test_require_jwt_accepts_verified_token_and_overrides_body(monkeypatch):
    """A valid JWT is accepted; its claims REPLACE the caller-supplied body claims."""
    key, jwks = _rsa_keypair_and_jwks()
    tok = _sign_rs256(key, {"sub": "rcm-rep-1", "custom:hpp_role": "DENIALS_SPECIALIST",
                            "exp": int(time.time()) + 300})
    monkeypatch.setenv("AUTH_REQUIRE_JWT", "1")
    monkeypatch.setenv("AUTH_JWKS", json.dumps(jwks))
    # Body tries to smuggle a privileged role; it must be ignored in favor of the token.
    payload = {"acting_user_claims": SPOOFED_BODY_CLAIMS}
    claims = serve.resolve_identity(payload, auth_header=f"Bearer {tok}")
    assert claims["sub"] == "rcm-rep-1"
    assert claims["custom:hpp_role"] == "DENIALS_SPECIALIST"
    assert claims.get("sub") != "attacker"
    assert claims["jwt"] == tok  # raw token carried forward for gateway re-verification


def test_demo_mode_passes_body_claims_through(monkeypatch):
    """AUTH_REQUIRE_JWT off (demo posture): body claims are used as-is."""
    monkeypatch.delenv("AUTH_REQUIRE_JWT", raising=False)
    claims = {"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"}
    out = serve.resolve_identity({"acting_user_claims": claims}, auth_header=None)
    assert out == claims


def test_demo_mode_still_runs_end_to_end(monkeypatch):
    """Demo mode still produces a grounded, human-gated appeal and submits on approval."""
    monkeypatch.delenv("AUTH_REQUIRE_JWT", raising=False)
    monkeypatch.setenv("EXTRACT_MODE", "demo")
    claims = {"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"}
    s = run_until_gate({"claim_ref": "CLM-2026-55810", "acting_user_claims": claims})
    assert s["recommended_action"] == RecommendedAction.APPEAL
    assert s["_paused_at_gate"] is True
    final = resume(s, {"approved": True, "reviewer": {"sub": "denials-mgr-1"}})
    assert final["case_status"] == "APPEAL_SUBMITTED" and final["appeal_ref"]


def test_gateway_denies_body_claims_when_require_jwt_and_no_jwks(monkeypatch):
    """Defense in depth: even if serve.py were bypassed, the gateway with
    AUTH_REQUIRE_JWT=1 and no JWKS refuses claims that lack a verifiable token."""
    monkeypatch.setenv("AUTH_REQUIRE_JWT", "1")
    gw = MCPGateway(connector_mode="fixture", jwks=None)
    with pytest.raises(jwt_verify.JWTError):
        gw.invoke(user_claims=SPOOFED_BODY_CLAIMS, agent_id="01-revenue-cycle-denial",
                  tool="pas.get_claim", args={"claim_ref": "CLM-2026-55810"})
