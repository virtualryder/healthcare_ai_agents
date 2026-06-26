# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Revenue-Cycle & Denial agent.
#
# Every system-of-record call (patient accounting, clearinghouse, payer portal,
# coding/encoder, EHR, knowledge base) goes through the MCP authorization gateway
# (reference logic for Bedrock AgentCore Gateway + Identity): the acting user's
# verified claims are authorized against a deny-by-default policy, high-risk
# writes (submit an appeal, update a case) require human approval, a short-lived
# scoped token is minted, and the attempt is audited (PHI-masked). The agent is
# deliberately NOT granted claim submission — a biller submits.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "01-revenue-cycle-denial"

try:
    from hpp_agent_platform.mcp_gateway import MCPGateway
    _GATEWAY: Optional[Any] = MCPGateway()
except Exception:  # pragma: no cover
    _GATEWAY = None


def _invoke(claims: Dict[str, Any], tool: str, args: Dict[str, Any],
            approval: Optional[Dict[str, Any]] = None) -> Any:
    if _GATEWAY is None:
        raise RuntimeError(
            "MCP gateway unavailable; install platform_core. Production access to "
            "patient accounting, the clearinghouse, payer portals, the encoder, and "
            "the EHR must flow through the gateway."
        )
    return _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool,
                           args=args, approval=approval)


# ── Reads ─────────────────────────────────────────────────────────────────────
def get_claim(claims: Dict[str, Any], claim_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "pas.get_claim", {"claim_ref": claim_ref})
    return res.result if res.allowed else {}


def get_account(claims: Dict[str, Any], account_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "pas.get_account", {"account_ref": account_ref})
    return res.result if res.allowed else {}


def validate_claim(claims: Dict[str, Any], claim_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "clearinghouse.validate_claim", {"claim_ref": claim_ref})
    return res.result if res.allowed else {}


def check_claim_status(claims: Dict[str, Any], claim_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "payer.check_claim_status", {"claim_ref": claim_ref})
    return res.result if res.allowed else {}


def get_clinical_docs(claims: Dict[str, Any], encounter_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "ehr.get_clinical_docs", {"encounter_ref": encounter_ref})
    return res.result if res.allowed else {}


def validate_codes(claims: Dict[str, Any], cpt: List[str], icd10: List[str]) -> Dict[str, Any]:
    res = _invoke(claims, "coding.validate_codes", {"cpt": cpt, "icd10": icd10})
    return res.result if res.allowed else {}


def check_medical_necessity(claims: Dict[str, Any], cpt: List[str], icd10: List[str]) -> Dict[str, Any]:
    res = _invoke(claims, "coding.check_medical_necessity", {"cpt": cpt, "icd10": icd10})
    return res.result if res.allowed else {}


def search_policy(claims: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "kb.search_policy", {"query": query})
    return res.result if res.allowed else []


# ── High-risk writes (human-approval gated) ───────────────────────────────────
def submit_appeal(claims: Dict[str, Any], payload: Dict[str, Any],
                  approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): submit a first-level appeal to the payer."""
    return _invoke(claims, "payer.submit_appeal", payload, approval=approval)


def update_case(claims: Dict[str, Any], payload: Dict[str, Any],
                approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): update the case-management system."""
    return _invoke(claims, "pas.update_case", payload, approval=approval)
