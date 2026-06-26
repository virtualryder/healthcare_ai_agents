# agent/nodes.py
# ============================================================
# Node logic for the Revenue-Cycle & Denial workflow.
#
# Each node is a pure function (state -> partial state update). The logic runs in
# EXTRACT_MODE=demo with no LLM call (deterministic denial classification +
# templated, grounded appeal from retrieved policy), and uses the LLM factory +
# gateway tools in live mode. Keeping nodes langgraph-free makes them unit-
# testable without the framework; graph.py wires them into a StateGraph with a
# framework-enforced HITL interrupt.
# ============================================================
from __future__ import annotations

import os
from typing import Any, Dict

from governance.accessibility.wcag import check_plain_language
from governance.grounding import verify_grounding
from hpp_agent_platform.phi import mask

from tools import gateway_tools as gw
from agent.state import RecommendedAction

# Payer remittance (CARC) codes -> root-cause category and appealability.
_CARC_ROOT_CAUSE = {
    "CO-197": ("authorization", True),    # precert/authorization absent
    "CO-50": ("medical_necessity", True), # not deemed medically necessary
    "CO-16": ("coding", True),            # claim/service lacks information
    "CO-11": ("coding", True),            # diagnosis inconsistent with procedure
    "CO-27": ("eligibility", False),      # expired/terminated coverage
    "CO-29": ("timely_filing", False),    # time limit for filing expired
}


def _demo() -> bool:
    return os.getenv("EXTRACT_MODE", "demo").strip().lower() == "demo"


def intake(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "current_step": "intake",
        "completed_steps": state.get("completed_steps", []) + ["intake"],
        "mode": state.get("mode", "POST_DENIAL"),
        "revision_count": state.get("revision_count", 0),
        "case_status": "INTAKE",
    }


def load_claim(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    claim = gw.get_claim(claims, state.get("claim_ref", ""))
    account = gw.get_account(claims, claim.get("account_ref", "")) if claim else {}
    return {"claim": claim, "account": account,
            # An explicitly provided denial set (e.g. from a 277 feed) wins;
            # otherwise take what the patient-accounting claim record carries.
            "denial_codes": state.get("denial_codes") or claim.get("denial_codes", []),
            "current_step": "load_claim",
            "completed_steps": state.get("completed_steps", []) + ["load_claim"]}


def analyze_denial(state: Dict[str, Any]) -> Dict[str, Any]:
    codes = state.get("denial_codes", []) or state.get("claim", {}).get("denial_codes", [])
    root_cause, appealable = "other", True
    for c in codes:
        if c in _CARC_ROOT_CAUSE:
            root_cause, appealable = _CARC_ROOT_CAUSE[c]
            break
    return {"root_cause": root_cause, "appealable": appealable,
            "current_step": "analyze_denial",
            "completed_steps": state.get("completed_steps", []) + ["analyze_denial"]}


def gather_evidence(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    claim = state.get("claim", {})
    docs = gw.get_clinical_docs(claims, claim.get("encounter_ref", "ENC-88231"))
    coding = gw.validate_codes(claims, claim.get("cpt", []), claim.get("icd10", []))
    necessity = gw.check_medical_necessity(claims, claim.get("cpt", []), claim.get("icd10", []))
    sources = gw.search_policy(claims, f"denial {' '.join(state.get('denial_codes', []))}")
    missing = list(docs.get("missing_for_billing", []))
    return {"clinical_docs": docs, "coding_validation": coding, "medical_necessity": necessity,
            "retrieved_sources": sources, "missing_documentation": missing,
            "current_step": "gather_evidence",
            "completed_steps": state.get("completed_steps", []) + ["gather_evidence"]}


def draft_appeal(state: Dict[str, Any]) -> Dict[str, Any]:
    sources = state.get("retrieved_sources", [])
    claim = state.get("claim", {})
    codes = ", ".join(state.get("denial_codes", []) or ["the cited denial code"])
    cpt = ", ".join(claim.get("cpt", []) or ["the billed service"])
    if _demo() or not sources:
        if sources:
            top = sources[0]
            letter = (
                f"Re: Claim {claim.get('claim_ref', '')} (CPT {cpt}). "
                f"This claim was denied under {codes}. Per {top.get('title')}, "
                f"{top.get('snippet')} We respectfully request reprocessing and payment."
            )
            citations = [{"title": s.get("title", ""), "url": s.get("url", "")} for s in sources]
            drafted_by = "demo-stub"
        else:
            letter = "Insufficient approved policy found to ground an appeal. Routing to a denials specialist."
            citations, drafted_by = [], "demo-stub"
    else:  # pragma: no cover - live LLM path
        from hpp_agent_platform.llm_factory import get_llm
        from agent.prompts import APPEAL_DRAFT_PROMPT
        llm = get_llm("narrative")
        ctx = "\n".join(f"- {s.get('title')}: {s.get('snippet')} ({s.get('url')})" for s in sources)
        payload = (f"{APPEAL_DRAFT_PROMPT}\n\nCLAIM: {claim}\nDENIAL CODES: {codes}\n"
                   f"APPROVED POLICY:\n{ctx}")
        msg = llm.invoke(payload)
        letter = getattr(msg, "content", str(msg))
        citations = [{"title": s.get("title", ""), "url": s.get("url", "")} for s in sources]
        drafted_by = "bedrock"
    return {"appeal_letter": letter, "citations": citations, "drafted_by": drafted_by,
            "current_step": "draft_appeal",
            "completed_steps": state.get("completed_steps", []) + ["draft_appeal"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    letter = state.get("appeal_letter", "")
    grounding = verify_grounding(letter, {"sources": state.get("retrieved_sources", []),
                                          "claim": state.get("claim", {})})
    literacy = check_plain_language(letter, max_grade=12.0)  # appeals are professional, not patient-facing
    phi_ok = mask(letter) == letter
    findings = []
    if not grounding.grounded:
        findings.append("ungrounded claims present in appeal")
    if not phi_ok:
        findings.append("PHI detected in appeal text")
    if state.get("missing_documentation"):
        findings.append("missing documentation for the billed service")
    return {"grounding_report": grounding.to_audit_dict(),
            "literacy_report": {"passes": literacy.passes, "issues": literacy.issues},
            "phi_ok": phi_ok, "quality_findings": findings,
            "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    """Conditional edge target: bounded revision, or proceed to the human gate."""
    findings = state.get("quality_findings", [])
    ground_issue = not state.get("grounding_report", {}).get("grounded", True)
    if (findings and ground_issue) and state.get("revision_count", 0) < 1:
        return "draft_appeal"
    return "human_review_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    root = state.get("root_cause")
    if state.get("missing_documentation"):
        action = RecommendedAction.REQUEST_DOCUMENTATION
    elif root == "coding":
        action = RecommendedAction.CORRECT_AND_RESUBMIT
    elif root in ("timely_filing", "eligibility") and not state.get("appealable", True):
        action = RecommendedAction.ESCALATE
    elif state.get("appealable", True):
        action = RecommendedAction.APPEAL
    else:
        action = RecommendedAction.ESCALATE
    return {"recommended_action": action,
            "revision_count": state.get("revision_count", 0) + (1 if state.get("quality_findings") else 0),
            "current_step": "human_review_gate",
            "completed_steps": state.get("completed_steps", []) + ["human_review_gate"]}


def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    action = state.get("recommended_action")
    approval = state.get("human_approval")
    claims = state.get("acting_user_claims", {})
    out: Dict[str, Any] = {"current_step": "finalize",
                           "completed_steps": state.get("completed_steps", []) + ["finalize"]}
    if action == RecommendedAction.APPEAL and approval:
        res = gw.submit_appeal(claims, {"claim_ref": state.get("claim_ref"), "level": 1,
                                        "reviewer": (approval or {}).get("reviewer")}, approval=approval)
        out["appeal_ref"] = getattr(res, "result", {}).get("appeal_ref") if res.allowed else None
        out["case_status"] = "APPEAL_SUBMITTED" if out["appeal_ref"] else "PENDING_REVIEW"
    elif action == RecommendedAction.CORRECT_AND_RESUBMIT:
        out["case_status"] = "RESUBMIT_QUEUED"  # a biller resubmits; agent cannot submit a claim
    elif action == RecommendedAction.REQUEST_DOCUMENTATION:
        out["case_status"] = "PENDING_REVIEW"
    elif action == RecommendedAction.ESCALATE:
        out["case_status"] = "ESCALATED"
    else:
        out["case_status"] = "PENDING_REVIEW"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "root_cause": state.get("root_cause"),
        "case_status": out["case_status"], "drafted_by": state.get("drafted_by"),
        "grounded": state.get("grounding_report", {}).get("grounded"),
    }]
    return out
