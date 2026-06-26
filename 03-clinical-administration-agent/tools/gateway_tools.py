# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Clinical-Administration agent.
#
# Every system-of-record call (EHR/FHIR, care plan, scheduling, consent, KB) goes
# through the MCP authorization gateway: deny-by-default authorization on the
# acting clinician's claims, a human gate on the one write (ehr.draft_note — a
# draft for a clinician to sign), short-lived scoped tokens, and a PHI-masked
# audit. The agent has no order-entry or note-signing authority.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "03-clinical-administration"

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


def get_encounter(claims: Dict[str, Any], encounter_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "ehr.get_encounter", {"encounter_ref": encounter_ref})
    return res.result if res.allowed else {}


def get_clinical_docs(claims: Dict[str, Any], encounter_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "ehr.get_clinical_docs", {"encounter_ref": encounter_ref})
    return res.result if res.allowed else {}


def get_care_plan(claims: Dict[str, Any], patient_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "careplan.get_care_plan", {"patient_ref": patient_ref})
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
def draft_note(claims: Dict[str, Any], payload: Dict[str, Any],
               approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): file a DRAFT note to the chart for clinician sign-off."""
    return _invoke(claims, "ehr.draft_note", payload, approval=approval)
