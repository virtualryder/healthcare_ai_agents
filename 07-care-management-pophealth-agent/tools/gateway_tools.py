# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Care Management & Population Health agent.
#
# Every system-of-record call (care management, EHR, consent, KB) goes through the
# MCP authorization gateway: deny-by-default authorization on the care manager's
# claims, a human gate on the one write (update the care plan), short-lived scoped
# tokens, and a PHI-masked audit. Risk stratification is screened for disparate
# impact; the care manager owns the plan.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "07-care-management-pophealth"

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
def get_patient_summary(claims: Dict[str, Any], patient_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "ehr.get_patient_summary", {"patient_ref": patient_ref})
    return res.result if res.allowed else {}


def get_care_plan(claims: Dict[str, Any], patient_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "careplan.get_care_plan", {"patient_ref": patient_ref})
    return res.result if res.allowed else {}


def identify_gaps(claims: Dict[str, Any], patient_ref: str, no_gaps: bool = False) -> Dict[str, Any]:
    res = _invoke(claims, "careplan.identify_gaps", {"patient_ref": patient_ref, "no_gaps": no_gaps})
    return res.result if res.allowed else {}


def check_consent(claims: Dict[str, Any], subject_ref: str, scope: str,
                  part2_sensitive: bool = False) -> Dict[str, Any]:
    res = _invoke(claims, "consent.check",
                  {"subject_ref": subject_ref, "scope": scope, "part2_sensitive": part2_sensitive})
    return res.result if res.allowed else {"granted": False}


def search_policy(claims: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "kb.search_policy", {"query": query})
    return res.result if res.allowed else []


# ── High-risk write (human-approval gated) ────────────────────────────────────
def update_care_plan(claims: Dict[str, Any], payload: Dict[str, Any],
                     approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): update the care plan (care-manager sign-off required)."""
    return _invoke(claims, "careplan.update_care_plan", payload, approval=approval)
