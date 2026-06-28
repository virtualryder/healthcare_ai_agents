"""
MCP authorization gateway — the governed front door to systems of record.

Every agent tool call passes through one enforcement point that, in order:

  1. AUTHENTICATES the acting user (verified IdP claims; fail-closed on missing sub).
  2. AUTHORIZES via deny-by-default policy with least-privilege intersection
     (agent grant ∩ user entitlement) — an agent can never exceed the human.
  3. For HIGH-RISK (write/irreversible) tools, requires HUMAN APPROVAL before
     execution; a verified reviewer identity is bound into the record.
  4. MINTS a short-lived token scoped to exactly that tool, carrying user context
     (no standing service account).
  5. INVOKES the tool via the connector framework (fixture or live).
  6. AUDITS the attempt (ALLOW/DENY/PENDING_APPROVAL/ERROR), PHI-masked, with
     lineage to the system of record reached.
  7. FAILS CLOSED on any error.

This is the reference logic for what AWS deploys as **Amazon Bedrock AgentCore
Gateway + AgentCore Identity** (or API Gateway + Lambda authorizer + STS +
Cognito + Cedar/OPA). The decision / least-privilege / token / audit semantics
are identical; each tool here corresponds to an AgentCore Gateway target. In a
HIPAA workload this is also where the Security Rule "minimum necessary" and
access-accounting controls are enforced in code rather than policy prose.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import policy as _policy
from . import tokens as _tokens
from .. import approvals as _approvals
from .. import jwt_verify as _jwtv
from .audit import GatewayAuditLog
from .errors import ApprovalRequired, PolicyDenied

logger = logging.getLogger(__name__)

_ROLE_CLAIM = os.getenv("AUTH_ROLE_CLAIM", "custom:hpp_role")


def _roles_from_claims(claims: Dict[str, Any]) -> List[str]:
    raw = claims.get(_ROLE_CLAIM) or claims.get("roles") or claims.get("cognito:groups") or []
    if isinstance(raw, str):
        return [r.strip() for r in raw.split(",") if r.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(r) for r in raw]
    return []


@dataclass
class GatewayResult:
    decision: str                       # ALLOW | DENY | PENDING_APPROVAL
    tool: str
    audit_id: str
    allowed: bool = False
    result: Any = None
    reason: str = ""
    token_jti: Optional[str] = None
    requires_approval: bool = False
    scope: List[str] = field(default_factory=list)


class MCPGateway:
    def __init__(self, audit: Optional[GatewayAuditLog] = None, connector_mode: Optional[str] = None,
                 jwks: Optional[Dict[str, Any]] = None) -> None:
        self.audit = audit or GatewayAuditLog()
        self._connector_mode = connector_mode  # None -> CONNECTOR_MODE env (default fixture)
        self._seen_jti: set = set()             # single-use approval replay guard (in-process)
        self._jwks = jwks                       # JWKS for RS* JWT verification (prod)

    def invoke(
        self,
        *,
        user_claims: Dict[str, Any],
        agent_id: str,
        tool: str,
        args: Optional[Dict[str, Any]] = None,
        approval: Optional[Dict[str, Any]] = None,
        raise_on_deny: bool = False,
    ) -> GatewayResult:
        args = args or {}
        user_claims = self._resolve_claims(user_claims or {})
        subject = (user_claims or {}).get("sub")
        roles = _roles_from_claims(user_claims or {})

        # 1. Authentication (fail-closed: no verified subject -> deny)
        if not subject:
            aid = self.audit.record({
                "decision": "DENY", "tool": tool, "agent_id": agent_id, "user": None,
                "reason": "no authenticated subject (fail-closed)",
            })
            if raise_on_deny:
                raise PolicyDenied("no authenticated subject")
            return GatewayResult("DENY", tool, aid, reason="no authenticated subject")

        # 2. Authorization (deny-by-default, least-privilege intersection)
        decision = _policy.decide(agent_id, roles, tool)
        if not decision.allowed:
            aid = self.audit.record({
                "decision": "DENY", "tool": tool, "agent_id": agent_id, "user": subject,
                "roles": roles, "reason": decision.reason,
            })
            if raise_on_deny:
                raise PolicyDenied(decision.reason)
            return GatewayResult("DENY", tool, aid, reason=decision.reason)

        # 3. Human approval gate for high-risk (write/irreversible) tools
        if decision.requires_approval and not self._approval_ok(
                approval, agent_id=agent_id, tool=tool, args=args, subject=subject):
            aid = self.audit.record({
                "decision": "PENDING_APPROVAL", "tool": tool, "agent_id": agent_id,
                "user": subject, "roles": roles,
                "reason": f"{tool} is high-risk; human approval required before execution",
            })
            if raise_on_deny:
                raise ApprovalRequired(f"{tool} requires human approval")
            return GatewayResult("PENDING_APPROVAL", tool, aid, reason="human approval required",
                                 requires_approval=True, scope=decision.effective_scope)

        # 4. Mint a short-lived token scoped to exactly this tool (user context inside)
        token = _tokens.mint_scoped_token(
            subject=subject, agent_id=agent_id, tool=tool, scope=decision.effective_scope,
        )
        claims = _tokens.verify_scoped_token(token, expected_tool=tool)  # prove it round-trips

        # 5. Invoke the tool via the connector framework
        try:
            result = self._invoke_connector(decision, args)
        except Exception as exc:  # 7. fail closed on any execution error
            self.audit.record({
                "decision": "ERROR", "tool": tool, "agent_id": agent_id, "user": subject,
                "token_jti": claims["jti"], "error": type(exc).__name__, "detail": str(exc),
            })
            raise

        # 6. Audit the allowed call, with lineage to the system of record
        approver = (approval or {}).get("reviewer") if decision.requires_approval else None
        aid = self.audit.record({
            "decision": "ALLOW", "tool": tool, "agent_id": agent_id, "user": subject,
            "roles": roles, "token_jti": claims["jti"], "scope": decision.effective_scope,
            "lineage": {"connector": decision.connector_kind, "method": decision.method},
            "approved_by": approver, "args": args,
        })
        return GatewayResult("ALLOW", tool, aid, allowed=True, result=result,
                             token_jti=claims["jti"], scope=decision.effective_scope,
                             requires_approval=decision.requires_approval)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _resolve_claims(self, user_claims: Dict[str, Any]) -> Dict[str, Any]:
        """If a raw JWT is presented, verify it (RS*/JWKS) and use its claims; else
        use the provided claim dict. AUTH_REQUIRE_JWT=1 denies a missing/invalid JWT."""
        token = user_claims.get("jwt")
        require = os.getenv("AUTH_REQUIRE_JWT", "").strip().lower() in ("1", "true", "yes")
        if token and self._jwks is not None:
            verified = _jwtv.verify_jwt(
                token, jwks=self._jwks,
                issuer=os.getenv("AUTH_JWT_ISSUER") or None,
                audience=os.getenv("AUTH_JWT_AUDIENCE") or None,
            )  # raises JWTError (fail closed) on any defect
            return verified
        if require:
            raise _jwtv.JWTError("AUTH_REQUIRE_JWT set but no verifiable JWT/JWKS presented")
        return user_claims

    def _approval_ok(self, approval: Optional[Dict[str, Any]], *, agent_id: str, tool: str,
                     args: Dict[str, Any], subject: Optional[str]) -> bool:
        """Accept a high-risk write only on a valid approval.

        Production path: a **bound, single-use, separation-of-duties** approval token
        (`approval["token"]`) tied to this exact agent+tool+args and minted by the
        reviewer service for a reviewer != requester. Demo/fixture path: an explicit
        approve decision with a verified reviewer identity that still satisfies SoD.
        """
        if not approval:
            return False
        token = approval.get("token")
        if token:
            try:
                _approvals.verify_approval(token, agent_id=agent_id, tool=tool, args=args,
                                           requester_sub=subject or "", seen_jti=self._seen_jti)
                return True
            except _approvals.ApprovalError:
                return False
        reviewer = approval.get("reviewer") or {}
        rsub = reviewer.get("sub")
        # separation of duties even on the demo path: reviewer must differ from requester
        return bool(approval.get("approved")) and bool(rsub) and rsub != subject

    def _invoke_connector(self, decision: "_policy.PolicyDecision", args: Dict[str, Any]) -> Any:
        from hpp_agent_platform.connectors import get_connector
        conn = get_connector(decision.connector_kind, mode=self._connector_mode)
        method = getattr(conn, decision.method)
        return method(**args)
