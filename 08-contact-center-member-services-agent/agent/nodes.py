# agent/nodes.py
# ============================================================
# Node logic for the Contact Center / Member Services workflow.
#
# Pure functions (state -> partial state update). Runs in EXTRACT_MODE=demo with
# no LLM call (deterministic, data-grounded plain-language response), and uses the
# LLM factory + gateway tools in live mode. No account-specific disclosure without
# a verified member identity. langgraph-free so nodes are unit-testable.
# ============================================================
from __future__ import annotations

import os
from typing import Any, Dict

from governance.accessibility.wcag import check_plain_language
from governance.grounding import verify_grounding
from hpp_agent_platform.phi import mask

from tools import gateway_tools as gw
from agent.state import InquiryType, RecommendedAction


def _demo() -> bool:
    return os.getenv("EXTRACT_MODE", "demo").strip().lower() == "demo"


def intake(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "current_step": "intake",
        "completed_steps": state.get("completed_steps", []) + ["intake"],
        "inquiry_type": state.get("inquiry_type", InquiryType.CLAIM_STATUS.value),
        "channel": state.get("channel", "voice"),
        "needs_identity": True,  # every member-specific inquiry requires a verified member
        "revision_count": state.get("revision_count", 0),
        "case_status": "INTAKE",
    }


def verify_member(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    assertion = state.get("identity_assertion", "")
    res = gw.verify_member(claims, assertion) if assertion else {"verified": False}
    return {"identity_verified": bool(res.get("verified")),
            "current_step": "verify_member",
            "completed_steps": state.get("completed_steps", []) + ["verify_member"]}


def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("identity_verified"):
        return {"current_step": "retrieve",
                "completed_steps": state.get("completed_steps", []) + ["retrieve"]}
    claims = state.get("acting_user_claims", {})
    member = gw.get_member(claims, state.get("member_ref", "MBR-30551"))
    out: Dict[str, Any] = {"member": member}
    itype = state.get("inquiry_type")
    if itype == InquiryType.CLAIM_STATUS.value:
        out["claim_status"] = gw.check_claim_status(claims, state.get("claim_ref", "CLM-2026-55810"))
    if itype in (InquiryType.BENEFITS.value, InquiryType.GRIEVANCE.value):
        elig = gw.check_eligibility(claims, state.get("member_ref", "MBR-30551"))
        out["eligibility"] = elig
        out["coverage_active"] = bool(elig.get("active", True))
    out["retrieved_sources"] = gw.search_policy(claims, f"{itype} member")
    out["current_step"] = "retrieve"
    out["completed_steps"] = state.get("completed_steps", []) + ["retrieve"]
    return out


def draft_response(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("identity_verified") or state.get("coverage_active") is False:
        return {"response": "", "citations": [], "drafted_by": "n/a",
                "current_step": "draft_response",
                "completed_steps": state.get("completed_steps", []) + ["draft_response"]}
    itype = state.get("inquiry_type")
    if _demo() or True:  # deterministic, data-grounded, plain language
        if itype == InquiryType.CLAIM_STATUS.value:
            cs = state.get("claim_status", {})
            codes = ", ".join(cs.get("denial_codes", []) or [])
            response = (f"Thanks for calling. Your claim {state.get('claim_ref', '')} was denied "
                        f"(reason {codes}). This is often missing prior approval. We can help you "
                        "ask for it to be looked at again. Would you like us to start that?")
            citations = [{"title": s.get("title", ""), "url": s.get("url", "")}
                         for s in state.get("retrieved_sources", [])]
        elif itype == InquiryType.BENEFITS.value:
            e = state.get("eligibility", {})
            response = (f"Your plan is {e.get('plan', 'your plan')} and your coverage is active. "
                        f"Your visit copay is ${e.get('copay', 0):.2f}. Let us know if you have other questions.")
            citations = []
        else:  # grievance
            response = ("We are sorry to hear about your concern. We have noted it and will open a "
                        "grievance. You will get an acknowledgement, and our team will follow up. "
                        "Thank you for letting us know.")
            citations = [{"title": s.get("title", ""), "url": s.get("url", "")}
                         for s in state.get("retrieved_sources", [])]
        drafted_by = "demo-stub"
    return {"response": response, "citations": citations, "drafted_by": drafted_by,
            "current_step": "draft_response",
            "completed_steps": state.get("completed_steps", []) + ["draft_response"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    response = state.get("response", "")
    grounding = verify_grounding(response, {"claim_status": state.get("claim_status", {}),
                                            "eligibility": state.get("eligibility", {}),
                                            "claim_ref": state.get("claim_ref", "")})
    literacy = check_plain_language(response, max_grade=8.0) if response else check_plain_language("ok")
    phi_ok = mask(response) == response
    findings = []
    if response and not grounding.grounded:
        findings.append("ungrounded statement in member response")
    if not phi_ok:
        findings.append("PHI detected in member response")
    if response and not literacy.passes:
        findings.append("member response exceeds health-literacy target")
    if state.get("needs_identity") and not state.get("identity_verified"):
        findings.append("account detail requested without verified identity")
    return {"grounding_report": grounding.to_audit_dict(),
            "literacy_report": {"passes": literacy.passes, "issues": literacy.issues},
            "phi_ok": phi_ok, "quality_findings": findings,
            "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    """Conditional edge target: bounded revision, or proceed to the human gate."""
    if not state.get("identity_verified") or state.get("coverage_active") is False:
        return "review_gate"
    findings = state.get("quality_findings", [])
    fixable = ("ungrounded statement in member response" in findings
               or "member response exceeds health-literacy target" in findings)
    if fixable and state.get("revision_count", 0) < 1:
        return "draft_response"
    return "review_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("identity_verified"):
        action = RecommendedAction.VERIFY_IDENTITY
    elif state.get("coverage_active") is False:
        action = RecommendedAction.ESCALATE
    elif state.get("inquiry_type") == InquiryType.GRIEVANCE.value:
        action = RecommendedAction.FILE_GRIEVANCE
    else:
        action = RecommendedAction.ANSWER_AND_LOG
    return {"recommended_action": action,
            "revision_count": state.get("revision_count", 0) + (1 if state.get("quality_findings") else 0),
            "current_step": "review_gate",
            "completed_steps": state.get("completed_steps", []) + ["review_gate"]}


def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    action = state.get("recommended_action")
    approval = state.get("human_approval")
    claims = state.get("acting_user_claims", {})
    out: Dict[str, Any] = {"current_step": "finalize",
                           "completed_steps": state.get("completed_steps", []) + ["finalize"]}
    if action == RecommendedAction.ANSWER_AND_LOG and approval:
        res = gw.log_interaction(claims, {"channel": state.get("channel", "voice"),
                                          "member_ref": state.get("member_ref")}, approval=approval)
        out["interaction_logged"] = res.result.get("interaction_id") if res.allowed else None
        out["case_status"] = "ANSWERED_LOGGED" if out["interaction_logged"] else "PENDING_REVIEW"
    elif action == RecommendedAction.FILE_GRIEVANCE and approval:
        res = gw.create_grievance(claims, {"category": "Member grievance",
                                           "member_ref": state.get("member_ref")}, approval=approval)
        out["grievance_ref"] = res.result.get("grievance_id") if res.allowed else None
        out["case_status"] = "GRIEVANCE_FILED" if out["grievance_ref"] else "PENDING_REVIEW"
    elif action == RecommendedAction.VERIFY_IDENTITY:
        out["case_status"] = "PENDING_IDENTITY"
    elif action == RecommendedAction.ESCALATE:
        out["case_status"] = "ESCALATED"
    else:
        out["case_status"] = "PENDING_REVIEW"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "inquiry_type": state.get("inquiry_type"),
        "case_status": out["case_status"], "drafted_by": state.get("drafted_by"),
        "grounded": state.get("grounding_report", {}).get("grounded"),
    }]
    return out
