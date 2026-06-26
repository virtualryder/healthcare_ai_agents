# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Utilization-Management agent.
#
# Every system-of-record call (clinical criteria, coding/coverage, payer, EHR,
# KB) goes through the MCP authorization gateway: deny-by-default authorization on
# the UM nurse's claims, a human gate on the one write (draft a UM recommendation),
# short-lived scoped tokens, and a PHI-masked audit. The agent is NOT granted
# payer.issue_determination — issuing a coverage determination is the medical
# director's decision, withheld from every agent.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "05-utilization-management"

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
def evaluate_criteria(claims: Dict[str, Any], service: str, meets: bool = True) -> Dict[str, Any]:
    res = _invoke(claims, "clinicalcriteria.evaluate", {"service": service, "meets": meets})
    return res.result if res.allowed else {}


def get_guideline(claims: Dict[str, Any], guideline_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "clinicalcriteria.get_guideline", {"guideline_id": guideline_id})
    return res.result if res.allowed else {}


def check_medical_necessity(claims: Dict[str, Any], cpt: List[str], icd10: List[str]) -> Dict[str, Any]:
    res = _invoke(claims, "coding.check_medical_necessity", {"cpt": cpt, "icd10": icd10})
    return res.result if res.allowed else {}


def check_pa_status(claims: Dict[str, Any], pa_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "payer.check_pa_status", {"pa_ref": pa_ref})
    return res.result if res.allowed else {}


def get_clinical_docs(claims: Dict[str, Any], encounter_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "ehr.get_clinical_docs", {"encounter_ref": encounter_ref})
    return res.result if res.allowed else {}


def search_policy(claims: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "kb.search_policy", {"query": query})
    return res.result if res.allowed else []


# ── High-risk write (human-approval gated) — a RECOMMENDATION, not a determination ──
def draft_um_recommendation(claims: Dict[str, Any], payload: Dict[str, Any],
                            approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): record a UM recommendation for the medical director."""
    return _invoke(claims, "payer.draft_um_recommendation", payload, approval=approval)
