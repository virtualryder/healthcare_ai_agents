# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Patient Access agent.
#
# Every system-of-record call (scheduling, registration, payer eligibility,
# identity, consent, KB) goes through the MCP authorization gateway: deny-by-
# default authorization on the rep's claims, a human gate on writes (book an
# appointment, create a registration), short-lived scoped tokens, and a PHI-
# masked audit. Cost estimates use the deterministic estimate_cost tool (Good
# Faith Estimate) — never an LLM.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "04-patient-access"

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
def verify_patient(claims: Dict[str, Any], assertion: str) -> Dict[str, Any]:
    res = _invoke(claims, "identity.verify_patient", {"assertion": assertion})
    return res.result if res.allowed else {"verified": False}


def check_eligibility(claims: Dict[str, Any], member_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "payer.check_eligibility", {"member_ref": member_ref})
    return res.result if res.allowed else {}


def estimate_cost(claims: Dict[str, Any], service: str) -> Dict[str, Any]:
    res = _invoke(claims, "registration.estimate_cost", {"service": service})
    return res.result if res.allowed else {}


def get_availability(claims: Dict[str, Any], service: str) -> Dict[str, Any]:
    res = _invoke(claims, "scheduling.get_availability", {"service": service})
    return res.result if res.allowed else {}


def get_registration(claims: Dict[str, Any], patient_ref: str) -> Dict[str, Any]:
    res = _invoke(claims, "registration.get_registration", {"patient_ref": patient_ref})
    return res.result if res.allowed else {}


def search_policy(claims: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "kb.search_policy", {"query": query})
    return res.result if res.allowed else []


# ── High-risk writes (human-approval gated) ───────────────────────────────────
def book_appointment(claims: Dict[str, Any], payload: Dict[str, Any],
                     approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): book a patient appointment."""
    return _invoke(claims, "scheduling.book_appointment", payload, approval=approval)


def create_registration(claims: Dict[str, Any], payload: Dict[str, Any],
                        approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): create a patient registration."""
    return _invoke(claims, "registration.create_registration", payload, approval=approval)
