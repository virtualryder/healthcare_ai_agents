# agent/nodes.py
# ============================================================
# Node logic for the Patient Access workflow.
#
# Pure functions (state -> partial state update). Runs in EXTRACT_MODE=demo with
# no LLM call (deterministic, state-grounded plain-language summary), and uses the
# LLM factory + gateway tools in live mode (reference agents 03-08 are deterministic by design; the live LLM path is NOT wired here — see agents 01/02. EXTRACT_MODE=live raises NotImplementedError). Cost estimates are ALWAYS the
# deterministic registration.estimate_cost tool (Good Faith Estimate), never the
# LLM. langgraph-free so nodes are unit-testable.
# ============================================================
from __future__ import annotations

import os
from typing import Any, Dict

from governance.accessibility.wcag import check_plain_language
from governance.grounding import verify_grounding
from hpp_agent_platform.phi import mask

from tools import gateway_tools as gw
from agent.state import RecommendedAction, TaskType

# Tasks that disclose account/benefit detail require a verified identity.
_NEEDS_IDENTITY = {TaskType.SCHEDULE.value, TaskType.BENEFITS.value}


def _demo() -> bool:
    return os.getenv("EXTRACT_MODE", "demo").strip().lower() == "demo"


def intake(state: Dict[str, Any]) -> Dict[str, Any]:
    task = state.get("task_type", TaskType.SCHEDULE.value)
    return {
        "current_step": "intake",
        "completed_steps": state.get("completed_steps", []) + ["intake"],
        "task_type": task,
        "needs_identity": task in _NEEDS_IDENTITY,
        "revision_count": state.get("revision_count", 0),
        "case_status": "INTAKE",
    }


def verify_identity(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("needs_identity"):
        return {"identity_verified": True, "current_step": "verify_identity",
                "completed_steps": state.get("completed_steps", []) + ["verify_identity"]}
    claims = state.get("acting_user_claims", {})
    assertion = state.get("identity_assertion", "")
    res = gw.verify_patient(claims, assertion) if assertion else {"verified": False}
    return {"identity_verified": bool(res.get("verified")),
            "current_step": "verify_identity",
            "completed_steps": state.get("completed_steps", []) + ["verify_identity"]}


def check_eligibility(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("task_type") == TaskType.ESTIMATE.value or not state.get("identity_verified"):
        return {"current_step": "check_eligibility",
                "completed_steps": state.get("completed_steps", []) + ["check_eligibility"]}
    claims = state.get("acting_user_claims", {})
    elig = gw.check_eligibility(claims, state.get("member_ref", "MBR-30551"))
    return {"eligibility": elig, "coverage_active": bool(elig.get("active", True)),
            "current_step": "check_eligibility",
            "completed_steps": state.get("completed_steps", []) + ["check_eligibility"]}


def estimate_cost(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    est = gw.estimate_cost(claims, state.get("service", "99214"))
    return {"estimate": est, "current_step": "estimate_cost",
            "completed_steps": state.get("completed_steps", []) + ["estimate_cost"]}


def get_availability(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("task_type") != TaskType.SCHEDULE.value:
        return {"current_step": "get_availability",
                "completed_steps": state.get("completed_steps", []) + ["get_availability"]}
    claims = state.get("acting_user_claims", {})
    avail = gw.get_availability(claims, state.get("service", "99214"))
    return {"availability": avail, "current_step": "get_availability",
            "completed_steps": state.get("completed_steps", []) + ["get_availability"]}


def prepare_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    # No member summary if identity is unverified or coverage is inactive.
    if (state.get("needs_identity") and not state.get("identity_verified")) \
            or state.get("coverage_active") is False:
        return {"summary": "", "citations": [], "drafted_by": "n/a",
                "current_step": "prepare_summary",
                "completed_steps": state.get("completed_steps", []) + ["prepare_summary"]}
    est = state.get("estimate", {})
    elig = state.get("eligibility", {})
    plan = elig.get("plan") or est.get("plan", "your plan")
    patient_cost = est.get("estimated_patient_responsibility")
    if _demo():  # deterministic, state-grounded, plain language
        parts = [f"Your plan is {plan}."]
        if patient_cost is not None:
            parts.append(f"Your estimated cost for this visit is ${patient_cost:.2f}. This is an estimate.")
        if state.get("task_type") == TaskType.SCHEDULE.value and state.get("availability"):
            parts.append("We have openings this week. We can book your visit and finish your sign-up.")
        elif state.get("task_type") == TaskType.BENEFITS.value:
            parts.append("Let us know if you would like to book a visit.")
        else:
            parts.append("This is a Good Faith Estimate. Final cost depends on the care you receive.")
        summary = " ".join(parts)
        citations = [{"title": est.get("basis", "Good Faith Estimate (No Surprises Act)"), "url": ""}]
        drafted_by = "demo-stub"
    else:
        # Live LLM drafting is a documented extension point, not wired in this reference
        # agent. Fail loud rather than silently pretend (agents 01/02 show the Bedrock path).
        raise NotImplementedError(
            "live LLM drafting is not implemented in this reference agent; run with "
            "EXTRACT_MODE=demo (deterministic reference workflow). See agents 01/02 "
            "for the wired Bedrock + gateway drafting path."
        )
    return {"summary": summary, "citations": citations, "drafted_by": drafted_by,
            "current_step": "prepare_summary",
            "completed_steps": state.get("completed_steps", []) + ["prepare_summary"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    summary = state.get("summary", "")
    grounding = verify_grounding(summary, {"eligibility": state.get("eligibility", {}),
                                           "estimate": state.get("estimate", {}),
                                           "availability": state.get("availability", {})})
    literacy = check_plain_language(summary, max_grade=8.0) if summary else check_plain_language("ok")
    phi_ok = mask(summary) == summary
    findings = []
    if summary and not grounding.grounded:
        findings.append("ungrounded figure in member summary")
    if not phi_ok:
        findings.append("PHI detected in member summary")
    if summary and not literacy.passes:
        findings.append("member summary exceeds health-literacy target")
    if state.get("needs_identity") and not state.get("identity_verified"):
        findings.append("account detail requested without verified identity")
    return {"grounding_report": grounding.to_audit_dict(),
            "literacy_report": {"passes": literacy.passes, "issues": literacy.issues},
            "phi_ok": phi_ok, "quality_findings": findings,
            "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    """Conditional edge target: bounded revision, or proceed to the human gate."""
    if (state.get("needs_identity") and not state.get("identity_verified")) \
            or state.get("coverage_active") is False:
        return "human_review_gate"
    findings = state.get("quality_findings", [])
    fixable = ("ungrounded figure in member summary" in findings
               or "member summary exceeds health-literacy target" in findings)
    if fixable and state.get("revision_count", 0) < 1:
        return "prepare_summary"
    return "human_review_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("needs_identity") and not state.get("identity_verified"):
        action = RecommendedAction.VERIFY_IDENTITY
    elif state.get("coverage_active") is False:
        action = RecommendedAction.ESCALATE
    elif state.get("task_type") == TaskType.SCHEDULE.value:
        action = RecommendedAction.BOOK_AND_REGISTER
    else:
        action = RecommendedAction.PROVIDE_ESTIMATE
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
    if action == RecommendedAction.BOOK_AND_REGISTER and approval:
        appt = gw.book_appointment(claims, {"service": state.get("service", "99214"),
                                            "slot": (state.get("availability", {}).get("slots") or [""])[0]},
                                   approval=approval)
        reg = gw.create_registration(claims, {"patient_ref": state.get("patient_ref")}, approval=approval)
        out["appointment_ref"] = appt.result.get("appointment_ref") if appt.allowed else None
        out["registration_ref"] = reg.result.get("patient_ref") if reg.allowed else None
        out["case_status"] = "BOOKED" if out["appointment_ref"] else "PENDING_REVIEW"
    elif action == RecommendedAction.PROVIDE_ESTIMATE:
        out["case_status"] = "ESTIMATE_PROVIDED"
    elif action == RecommendedAction.VERIFY_IDENTITY:
        out["case_status"] = "PENDING_IDENTITY"
    elif action == RecommendedAction.ESCALATE:
        out["case_status"] = "ESCALATED"
    else:
        out["case_status"] = "PENDING_REVIEW"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "task_type": state.get("task_type"),
        "case_status": out["case_status"], "drafted_by": state.get("drafted_by"),
        "grounded": state.get("grounding_report", {}).get("grounded"),
    }]
    return out
