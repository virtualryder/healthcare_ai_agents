"""
Bound, single-use, separation-of-duties approval tokens.

A high-risk write (submit an appeal, file a grievance, draft a note for signing)
does not execute on a bare "approved: true". It executes only against an approval
token that is:

  * **Bound** — cryptographically tied to the exact agent, tool, and a hash of the
    call arguments. A token minted to approve "submit appeal for CLM-A" cannot be
    replayed to submit an appeal for CLM-B, or to call a different tool.
  * **Separation-of-duties** — the reviewer (`sub`) must differ from the requester.
    Minting fails if approver == requester; verification re-checks it.
  * **Single-use** — each token carries a unique `jti`; a seen-jti store rejects
    replays. In production the store is a DynamoDB conditional PutItem on `jti`.
  * **Expiring** — short TTL; an old approval cannot be reused.

The token is HMAC-signed by the **reviewer service** (server-side mint), so a
symmetric key is correct here — the agent never mints its own approval. Dev uses
APPROVAL_SIGNING_SECRET (or an ephemeral per-process key); production resolves the
key from Secrets Manager / KMS. Fail-closed: any defect raises `ApprovalError`.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional, Set

_SECRET = os.getenv("APPROVAL_SIGNING_SECRET", secrets.token_hex(32)).encode()
_TTL = int(os.getenv("APPROVAL_TTL_SECONDS", "900"))  # 15 minutes


class ApprovalError(Exception):
    """Approval minting/verification failed — fail closed."""


def binding_hash(agent_id: str, tool: str, args: Optional[Dict[str, Any]]) -> str:
    """Stable hash of (agent, tool, canonical args) the token is bound to."""
    canon = json.dumps({"agent_id": agent_id, "tool": tool, "args": args or {}},
                       sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(canon).hexdigest()


def _sign(payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    sig = hmac.new(_SECRET, body, hashlib.sha256).hexdigest()
    b = body.decode()
    return f"{b}.{sig}"


def mint_approval(*, reviewer_sub: str, requester_sub: str, agent_id: str, tool: str,
                  args: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None) -> str:
    """Reviewer service mints a bound, single-use approval. SoD enforced at mint."""
    if not reviewer_sub:
        raise ApprovalError("approval requires a verified reviewer identity")
    if reviewer_sub == requester_sub:
        raise ApprovalError("separation of duties: reviewer must differ from requester")
    now = int(time.time())
    payload = {
        "jti": str(uuid.uuid4()),
        "reviewer_sub": reviewer_sub,
        "requester_sub": requester_sub,
        "binding": binding_hash(agent_id, tool, args),
        "iat": now,
        "exp": now + (ttl or _TTL),
    }
    return _sign(payload)


def verify_approval(token: str, *, agent_id: str, tool: str, requester_sub: str,
                    args: Optional[Dict[str, Any]] = None,
                    seen_jti: Optional[Set[str]] = None,
                    now: Optional[int] = None) -> Dict[str, Any]:
    """Verify a bound approval token for this exact call. Returns the reviewer record."""
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError as exc:
        raise ApprovalError("malformed approval token") from exc
    expected = hmac.new(_SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ApprovalError("approval signature invalid (tampered or wrong key)")
    p = json.loads(body)
    now = int(time.time()) if now is None else now
    if now > int(p.get("exp", 0)):
        raise ApprovalError("approval expired")
    if p.get("binding") != binding_hash(agent_id, tool, args):
        raise ApprovalError("approval not bound to this exact tool + arguments (replay/retarget blocked)")
    if p.get("requester_sub") != requester_sub:
        raise ApprovalError("approval requester mismatch")
    if not p.get("reviewer_sub") or p.get("reviewer_sub") == requester_sub:
        raise ApprovalError("separation of duties violated")
    jti = p.get("jti")
    if seen_jti is not None:
        if jti in seen_jti:
            raise ApprovalError("approval already used (single-use replay blocked)")
        seen_jti.add(jti)
    return {"sub": p["reviewer_sub"], "jti": jti}
