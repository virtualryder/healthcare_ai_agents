"""
Cryptographic JWT verification — the identity foundation of the gateway.

Client-supplied roles are NEVER trusted. In production the agent receives a JWT
minted by Amazon Cognito (federating the organization IdP); this module verifies
it before the gateway reads a single claim:

  * Signature — RSASSA-PKCS1-v1.5 (RS256/384/512) against the issuer's JWKS,
    selected by `kid`. (HMAC is intentionally unsupported here — a verifier that
    accepts both RS* and HS* is the classic algorithm-confusion vulnerability.)
  * **Algorithm allow-list** — only RS256/384/512. `alg: none` and any `HS*` are
    rejected before any key material is touched (alg-confusion / key-confusion guard).
  * Issuer / audience / expiry / not-before — checked with a small clock leeway.

Fail-closed: any defect raises `JWTError` and the gateway denies. `cryptography`
is a lazy import so `platform_core` stays dependency-free until JWT mode is used;
demo/fixture flows pass a verified-claims dict directly and never touch this path.
"""
from __future__ import annotations

import base64
import json
import os
import time
from typing import Any, Dict, Optional

_RSA_ALGS = {"RS256": "sha256", "RS384": "sha384", "RS512": "sha512"}
_LEEWAY = int(os.getenv("JWT_LEEWAY_SECONDS", "60"))


class JWTError(Exception):
    """JWT verification failed — fail closed."""


def _b64url_decode(seg: str) -> bytes:
    return base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4))


def _segments(token: str):
    try:
        h, p, s = token.split(".")
    except ValueError as exc:
        raise JWTError("malformed JWT (expected 3 dot-separated segments)") from exc
    return h, p, s


def _rsa_public_key_from_jwk(jwk: Dict[str, Any]):
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
    n = int.from_bytes(_b64url_decode(jwk["n"]), "big")
    e = int.from_bytes(_b64url_decode(jwk["e"]), "big")
    return RSAPublicNumbers(e, n).public_key()


def verify_jwt(
    token: str,
    *,
    jwks: Dict[str, Any],
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    now: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Verify a compact RS* JWT against a JWKS dict ({"keys": [...]}) and return its
    claims. Raises JWTError on any failure (fail closed).
    """
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.exceptions import InvalidSignature

    now = int(time.time()) if now is None else now
    h_seg, p_seg, s_seg = _segments(token)

    header = json.loads(_b64url_decode(h_seg))
    alg = header.get("alg")
    if alg not in _RSA_ALGS:  # rejects "none" and every HS* before any key use
        raise JWTError(f"disallowed JWT alg {alg!r} (allow-list: {sorted(_RSA_ALGS)})")
    kid = header.get("kid")

    keys = {k.get("kid"): k for k in jwks.get("keys", [])}
    jwk = keys.get(kid) or (jwks["keys"][0] if len(jwks.get("keys", [])) == 1 else None)
    if not jwk:
        raise JWTError(f"no JWKS key matches kid {kid!r}")
    if jwk.get("kty") != "RSA":
        raise JWTError("only RSA keys are supported")

    pub = _rsa_public_key_from_jwk(jwk)
    signing_input = f"{h_seg}.{p_seg}".encode()
    sig = _b64url_decode(s_seg)
    hash_alg = {"sha256": hashes.SHA256(), "sha384": hashes.SHA384(), "sha512": hashes.SHA512()}[_RSA_ALGS[alg]]
    try:
        pub.verify(sig, signing_input, padding.PKCS1v15(), hash_alg)
    except InvalidSignature as exc:
        raise JWTError("JWT signature verification failed") from exc

    claims = json.loads(_b64url_decode(p_seg))
    exp = claims.get("exp")
    if exp is not None and now > int(exp) + _LEEWAY:
        raise JWTError("JWT expired")
    nbf = claims.get("nbf")
    if nbf is not None and now + _LEEWAY < int(nbf):
        raise JWTError("JWT not yet valid (nbf)")
    if issuer is not None and claims.get("iss") != issuer:
        raise JWTError("JWT issuer mismatch")
    if audience is not None:
        aud = claims.get("aud")
        ok = audience == aud or (isinstance(aud, (list, tuple)) and audience in aud)
        if not ok:
            raise JWTError("JWT audience mismatch")
    if not claims.get("sub"):
        raise JWTError("JWT missing subject (sub)")
    return claims
