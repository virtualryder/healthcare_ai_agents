# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Contact Center / Member Services agent.
#
# Every system-of-record call (Amazon Connect contact center, payer status/
# eligibility, identity, consent, KB) goes through the MCP authorization gateway:
# deny-by-default authorization on the rep's claims, a human gate on writes (log
# an interaction, create a grievance), short-lived scoped tokens, and a PHI-masked
# audit. No account detail is disclosed without a verified member identity.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "08-contact-center-member-services"

try:
    from hpp_agent_platform.mcp_gateway import MCPGateway
    _GATEWAY: Optional[Any] = MCPGateway()
except Exception:  # pragma: no cover
    _GATEWAY = None


def _invoke(claims: Dict[str, Any], tool: str, args: Dict[str, Any],
            approval: Optional[Dict[str, Any]] = None) -> Any:
    if _GATEWAY is None:
        raise RuntimeError("MCP gateway unavailable; install platform_core.")
    return _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool,
                           args=args, approval=approval)


# ── Reads ─────────────────────────────────────────────────────────────────────
def verify_member(claims: Dict[str, Any], assertion: str) -> Dict[str, Any]:
    res = _invoke(claims, "identity.verify_member", {"assertion": assertion})
    return res.result if res.allowed else {"verified": False}


def get_member(claims: Dict[str, Any], member_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "contactcenter.get_member", {"member_ref": member_ref})
    return res.result if res.allowed else {}


def check_claim_status(claims: Dict[str, Any], claim_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "payer.check_claim_status", {"claim_ref": claim_ref})
    return res.result if res.allowed else {}


def check_eligibility(claims: Dict[str, Any], member_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "payer.check_eligibility", {"member_ref": member_ref})
    return res.result if res.allowed else {}


def search_policy(claims: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "kb.search_policy", {"query": query})
    return res.result if res.allowed else []


# ── High-risk writes (human-approval gated) ───────────────────────────────────
def log_interaction(claims: Dict[str, Any], payload: Dict[str, Any],
                    approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): log the member interaction."""
    return _invoke(claims, "contactcenter.log_interaction", payload, approval=approval)


def create_grievance(claims: Dict[str, Any], payload: Dict[str, Any],
                     approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): intake a member grievance."""
    return _invoke(claims, "contactcenter.create_grievance", payload, approval=approval)
