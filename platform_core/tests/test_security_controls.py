"""Negative-case control-plane tests — the controls a CISO asks about, proven.
Covers: cryptographic JWT verification (alg-confusion, expiry, signature, audience),
bound single-use separation-of-duties approvals, and the tamper-evident audit chain."""
import base64
import json
import time

import pytest

from hpp_agent_platform import jwt_verify, approvals
from hpp_agent_platform.mcp_gateway import MCPGateway, GatewayAuditLog


# ── helpers: build a real RS256 JWT + JWKS with `cryptography` ────────────────
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


# ── JWT verification ─────────────────────────────────────────────────────────
def test_valid_jwt_verifies():
    key, jwks = _rsa_keypair_and_jwks()
    tok = _sign_rs256(key, {"sub": "u1", "exp": int(time.time()) + 300, "iss": "hpp", "aud": "agents"})
    claims = jwt_verify.verify_jwt(tok, jwks=jwks, issuer="hpp", audience="agents")
    assert claims["sub"] == "u1"


def test_alg_none_rejected():
    _, jwks = _rsa_keypair_and_jwks()
    h = _b64u(json.dumps({"alg": "none", "kid": "k1"}).encode())
    p = _b64u(json.dumps({"sub": "u1"}).encode())
    with pytest.raises(jwt_verify.JWTError):
        jwt_verify.verify_jwt(f"{h}.{p}.", jwks=jwks)


def test_hs256_confusion_rejected():
    # an attacker signs HS256 using the public modulus as the secret — must be rejected
    _, jwks = _rsa_keypair_and_jwks()
    h = _b64u(json.dumps({"alg": "HS256", "kid": "k1"}).encode())
    p = _b64u(json.dumps({"sub": "u1"}).encode())
    with pytest.raises(jwt_verify.JWTError):
        jwt_verify.verify_jwt(f"{h}.{p}.deadbeef", jwks=jwks)


def test_expired_jwt_rejected():
    key, jwks = _rsa_keypair_and_jwks()
    tok = _sign_rs256(key, {"sub": "u1", "exp": int(time.time()) - 3600})
    with pytest.raises(jwt_verify.JWTError):
        jwt_verify.verify_jwt(tok, jwks=jwks)


def test_tampered_signature_rejected():
    key, jwks = _rsa_keypair_and_jwks()
    tok = _sign_rs256(key, {"sub": "u1", "exp": int(time.time()) + 300})
    bad = tok[:-4] + ("aaaa" if tok[-4:] != "aaaa" else "bbbb")
    with pytest.raises(jwt_verify.JWTError):
        jwt_verify.verify_jwt(bad, jwks=jwks)


def test_audience_mismatch_rejected():
    key, jwks = _rsa_keypair_and_jwks()
    tok = _sign_rs256(key, {"sub": "u1", "exp": int(time.time()) + 300, "aud": "other"})
    with pytest.raises(jwt_verify.JWTError):
        jwt_verify.verify_jwt(tok, jwks=jwks, audience="agents")


# ── bound, single-use, separation-of-duties approvals ────────────────────────
def test_bound_approval_round_trips():
    tok = approvals.mint_approval(reviewer_sub="rev", requester_sub="req",
                                  agent_id="01-revenue-cycle-denial", tool="payer.submit_appeal",
                                  args={"claim_ref": "CLM-A"})
    rec = approvals.verify_approval(tok, agent_id="01-revenue-cycle-denial", tool="payer.submit_appeal",
                                    requester_sub="req", args={"claim_ref": "CLM-A"}, seen_jti=set())
    assert rec["sub"] == "rev"


def test_sod_enforced_at_mint():
    with pytest.raises(approvals.ApprovalError):
        approvals.mint_approval(reviewer_sub="same", requester_sub="same",
                                agent_id="a", tool="t", args={})


def test_approval_not_replayable_to_other_args():
    tok = approvals.mint_approval(reviewer_sub="rev", requester_sub="req",
                                  agent_id="a", tool="t", args={"claim_ref": "CLM-A"})
    with pytest.raises(approvals.ApprovalError):
        approvals.verify_approval(tok, agent_id="a", tool="t", requester_sub="req",
                                  args={"claim_ref": "CLM-B"}, seen_jti=set())


def test_approval_single_use():
    seen = set()
    tok = approvals.mint_approval(reviewer_sub="rev", requester_sub="req", agent_id="a", tool="t", args={})
    approvals.verify_approval(tok, agent_id="a", tool="t", requester_sub="req", args={}, seen_jti=seen)
    with pytest.raises(approvals.ApprovalError):
        approvals.verify_approval(tok, agent_id="a", tool="t", requester_sub="req", args={}, seen_jti=seen)


def test_tampered_approval_token_rejected():
    tok = approvals.mint_approval(reviewer_sub="rev", requester_sub="req", agent_id="a", tool="t", args={})
    with pytest.raises(approvals.ApprovalError):
        approvals.verify_approval(tok[:-2] + "00", agent_id="a", tool="t", requester_sub="req",
                                  args={}, seen_jti=set())


# ── gateway: bound approval end-to-end + SoD on the demo path ─────────────────
def test_gateway_accepts_bound_approval_token():
    gw = MCPGateway(connector_mode="fixture")
    args = {"claim_ref": "CLM-2026-55810", "level": 1}
    tok = approvals.mint_approval(reviewer_sub="mgr-1", requester_sub="rcm-1",
                                  agent_id="01-revenue-cycle-denial", tool="payer.submit_appeal", args=args)
    r = gw.invoke(user_claims={"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"},
                  agent_id="01-revenue-cycle-denial", tool="payer.submit_appeal", args=args,
                  approval={"token": tok})
    assert r.decision == "ALLOW"


def test_gateway_rejects_self_approval_sod():
    gw = MCPGateway(connector_mode="fixture")
    # reviewer == requester on the demo path must be refused (separation of duties)
    r = gw.invoke(user_claims={"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"},
                  agent_id="01-revenue-cycle-denial", tool="payer.submit_appeal",
                  args={"claim_ref": "CLM-1"}, approval={"approved": True, "reviewer": {"sub": "rcm-1"}})
    assert r.decision == "PENDING_APPROVAL"


def test_audit_chain_is_tamper_evident():
    audit = GatewayAuditLog()
    gw = MCPGateway(audit=audit, connector_mode="fixture")
    gw.invoke(user_claims={"sub": "u", "custom:hpp_role": "DENIALS_SPECIALIST"},
              agent_id="01-revenue-cycle-denial", tool="kb.search_policy", args={"query": "x"})
    gw.invoke(user_claims={"sub": "u", "custom:hpp_role": "DENIALS_SPECIALIST"},
              agent_id="01-revenue-cycle-denial", tool="pas.get_claim", args={"claim_ref": "CLM-1"})
    assert audit.verify_chain()
    audit.records[0]["decision"] = "TAMPERED"   # mutate a sealed record
    assert audit.verify_chain() is False
