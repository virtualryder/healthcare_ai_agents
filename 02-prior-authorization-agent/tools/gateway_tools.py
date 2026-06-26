# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Prior-Authorization agent.
#
# Every system-of-record call (payer portal / Da Vinci, clinical criteria, EHR,
# encoder, knowledge base) goes through the MCP authorization gateway: the acting
# user's verified claims are authorized against a deny-by-default policy, the
# high-risk write (submit a PA request) requires human approval, a short-lived
# scoped token is minted, and the attempt is audited (PHI-masked). The agent is
# NOT granted any determination authority — the coverage decision is the payer's.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "02-prior-authorization"

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
def check_pa_requirement(claims: Dict[str, Any], service: str) -> Dict[str, Any]:
    res = _invoke(claims, "payer.check_pa_requirement", {"service": service})
    return res.result if res.allowed else {}


def check_pa_status(claims: Dict[str, Any], pa_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "payer.check_pa_status", {"pa_ref": pa_ref})
    return res.result if res.allowed else {}


def get_patient_summary(claims: Dict[str, Any], patient_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "ehr.get_patient_summary", {"patient_ref": patient_ref})
    return res.result if res.allowed else {}


def get_clinical_docs(claims: Dict[str, Any], encounter_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "ehr.get_clinical_docs", {"encounter_ref": encounter_ref})
    return res.result if res.allowed else {}


def check_medical_necessity(claims: Dict[str, Any], cpt: List[str], icd10: List[str]) -> Dict[str, Any]:
    res = _invoke(claims, "coding.check_medical_necessity", {"cpt": cpt, "icd10": icd10})
    return res.result if res.allowed else {}


def evaluate_criteria(claims: Dict[str, Any], service: str) -> Dict[str, Any]:
    res = _invoke(claims, "clinicalcriteria.evaluate", {"service": service})
    return res.result if res.allowed else {}


def get_guideline(claims: Dict[str, Any], guideline_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "clinicalcriteria.get_guideline", {"guideline_id": guideline_id})
    return res.result if res.allowed else {}


def search_policy(claims: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "kb.search_policy", {"query": query})
    return res.result if res.allowed else []


# ── High-risk write (human-approval gated) ────────────────────────────────────
def submit_pa(claims: Dict[str, Any], payload: Dict[str, Any],
              approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): submit a prior-authorization request to the payer."""
    return _invoke(claims, "payer.submit_pa", payload, approval=approval)
