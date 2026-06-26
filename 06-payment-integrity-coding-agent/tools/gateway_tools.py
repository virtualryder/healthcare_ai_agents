# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Payment Integrity & Coding agent.
#
# Every system-of-record call (encoder/coding, patient accounting, clearinghouse,
# EHR, KB) goes through the MCP authorization gateway: deny-by-default
# authorization on the coder's claims, a human gate on the one write (record a
# payment-integrity flag via pas.update_case), short-lived scoped tokens, and a
# PHI-masked audit. The agent has NO recoupment, payment-adjustment, or claim-
# submission authority — it flags for a human reviewer.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "06-payment-integrity-coding"

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
def get_claim(claims: Dict[str, Any], claim_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "pas.get_claim", {"claim_ref": claim_ref})
    return res.result if res.allowed else {}


def get_clinical_docs(claims: Dict[str, Any], encounter_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "ehr.get_clinical_docs", {"encounter_ref": encounter_ref})
    return res.result if res.allowed else {}


def suggest_codes(claims: Dict[str, Any], encounter_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "coding.suggest_codes", {"encounter_ref": encounter_ref})
    return res.result if res.allowed else {}


def validate_codes(claims: Dict[str, Any], cpt: List[str], icd10: List[str],
                   ncci: bool = False, mue: bool = False) -> Dict[str, Any]:
    res = _invoke(claims, "coding.validate_codes", {"cpt": cpt, "icd10": icd10, "ncci": ncci, "mue": mue})
    return res.result if res.allowed else {}


def check_medical_necessity(claims: Dict[str, Any], cpt: List[str], icd10: List[str],
                            supported: bool = True) -> Dict[str, Any]:
    res = _invoke(claims, "coding.check_medical_necessity",
                  {"cpt": cpt, "icd10": icd10, "supported": supported})
    return res.result if res.allowed else {}


def validate_claim(claims: Dict[str, Any], claim_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "clearinghouse.validate_claim", {"claim_ref": claim_ref})
    return res.result if res.allowed else {}


def search_policy(claims: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "kb.search_policy", {"query": query})
    return res.result if res.allowed else []


# ── High-risk write (human-approval gated) — record a review flag, not a recoupment ──
def update_case(claims: Dict[str, Any], payload: Dict[str, Any],
                approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): record a payment-integrity flag for human review."""
    return _invoke(claims, "pas.update_case", payload, approval=approval)
