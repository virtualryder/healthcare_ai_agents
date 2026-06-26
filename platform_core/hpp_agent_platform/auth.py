"""
Auth helpers — extract verified IdP claims for the acting workforce user.

In production, identity is established at the edge (Cognito User Pool / Identity
Center federating the organization IdP — SAML 2.0 / OIDC, e.g. Epic/Workday SSO)
and the verified JWT claims are forwarded to the agent. The gateway authorizes
against these claims. This module normalizes claim shapes so the gateway sees a
consistent dict. No identity is established here — that is the IdP's job; this
only reads what was verified.
"""
from __future__ import annotations

from typing import Any, Dict, List

ROLE_CLAIM_KEYS = ("custom:hpp_role", "roles", "cognito:groups")


def claims_from_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Return a normalized claims dict from a request/runtime context."""
    claims = dict(ctx.get("claims") or ctx.get("authorizer") or {})
    if "sub" not in claims and "sub" in ctx:
        claims["sub"] = ctx["sub"]
    return claims


def roles(claims: Dict[str, Any]) -> List[str]:
    for k in ROLE_CLAIM_KEYS:
        raw = claims.get(k)
        if isinstance(raw, str):
            return [r.strip() for r in raw.split(",") if r.strip()]
        if isinstance(raw, (list, tuple)):
            return [str(r) for r in raw]
    return []
