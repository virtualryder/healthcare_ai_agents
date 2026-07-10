# agent/nodes.py
# ============================================================
# Node logic for the Utilization-Management workflow.
#
# Pure functions (state -> partial state update). Runs in EXTRACT_MODE=demo with
# no LLM call (deterministic, criteria-grounded recommendation), and uses the LLM
# factory + gateway tools in live mode (reference agents 03-08 are deterministic by design; the live LLM path is NOT wired here — see agents 01/02. EXTRACT_MODE=live raises NotImplementedError). A four-fifths fairness screen runs on any
# provided flag/rank cohort. langgraph-free so nodes are unit-testable.
# ============================================================
from __future__ import annotations

import os
from typing import Any, Dict

from governance.fairness.disparate_impact import four_fifths
from governance.grounding import verify_grounding
from hpp_agent_platform.phi import mask

from tools import gateway_tools as gw
from agent.state import RecommendedAction


def _demo() -> bool:
    return os.getenv("EXTRACT_MODE", "demo").strip().lower() == "demo"


def intake(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "current_step": "intake",
        "completed_steps": state.get("completed_steps", []) + ["intake"],
        "meets": bool(state.get("meets", True)),
        "missing_evidence": bool(state.get("missing_evidence", False)),
        "revision_count": state.get("revision_count", 0),
        "case_status": "INTAKE",
    }


def gather_clinical(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    docs = gw.get_clinical_docs(claims, state.get("encounter_ref", "ENC-88231"))
    pa_status = gw.check_pa_status(claims, state["pa_ref"]) if state.get("pa_ref") else {}
    return {"clinical_docs": docs, "pa_status": pa_status,
            "current_step": "gather_clinical",
            "completed_steps": state.get("completed_steps", []) + ["gather_clinical"]}


def evaluate_criteria(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    result = gw.evaluate_criteria(claims, state.get("service", "inpatient admission"),
                                  meets=state.get("meets", True))
    guideline = gw.get_guideline(claims, "MCG-IP-DM")
    necessity = gw.check_medical_necessity(claims, state.get("cpt", []), state.get("diagnosis", []))
    return {"criteria_result": result, "guideline": guideline, "medical_necessity": necessity,
            "current_step": "evaluate_criteria",
            "completed_steps": state.get("completed_steps", []) + ["evaluate_criteria"]}


def fairness_screen(state: Dict[str, Any]) -> Dict[str, Any]:
    cohort = state.get("cohort") or {}
    if cohort.get("selected") and cohort.get("totals"):
        rep = four_fifths(cohort["selected"], cohort["totals"])
        report = {"applied": True, "passes_four_fifths": rep.passes_four_fifths,
                  "impact_ratios": rep.impact_ratios, "flagged_groups": rep.flagged_groups}
    else:
        report = {"applied": False,
                  "note": "single-case review; disparate-impact screen is applied at the batch/model level"}
    return {"fairness_report": report, "current_step": "fairness_screen",
            "completed_steps": state.get("completed_steps", []) + ["fairness_screen"]}


def draft_recommendation(state: Dict[str, Any]) -> Dict[str, Any]:
    crit = state.get("criteria_result", {})
    necessity = state.get("medical_necessity", {})
    guideline = state.get("guideline", {})
    service = state.get("service", "the requested service")
    meets = bool(crit.get("meets_criteria")) and necessity.get("supported", True)
    if state.get("missing_evidence"):
        recommendation = "NEEDS_MORE_INFO"
    elif meets:
        recommendation = "MEETS_CRITERIA"
    else:
        recommendation = "DOES_NOT_MEET"
    if _demo():  # deterministic, criteria-grounded rationale
        if recommendation == "MEETS_CRITERIA":
            ind = ", ".join(crit.get("matched_indications", []) or ["documented indications"])
            rationale = (f"Recommendation: evidence MEETS {crit.get('criteria_set', 'clinical')} criteria "
                         f"for {service}. Indications met: {ind}. Coverage supported per "
                         f"{necessity.get('source', 'coverage policy')}. Guideline {guideline.get('title', '')}.")
        elif recommendation == "DOES_NOT_MEET":
            unmet = ", ".join(crit.get("unmet_indications", []) or ["required indications not documented"])
            rationale = (f"Recommendation: evidence DOES NOT MEET {crit.get('criteria_set', 'clinical')} criteria "
                         f"for {service}. Unmet: {unmet}. Forwarded to the medical director for determination "
                         f"per guideline {guideline.get('title', '')}.")
        else:
            rationale = (f"Recommendation: insufficient evidence to apply criteria for {service}. "
                         "Requesting additional clinical documentation before review.")
        citations = [{"title": guideline.get("title", "Clinical guideline"), "url": guideline.get("url", "")}]
        drafted_by = "demo-stub"
    else:
        # Live LLM drafting is a documented extension point, not wired in this reference
        # agent. Fail loud rather than silently pretend (agents 01/02 show the Bedrock path).
        raise NotImplementedError(
            "live LLM drafting is not implemented in this reference agent; run with "
            "EXTRACT_MODE=demo (deterministic reference workflow). See agents 01/02 "
            "for the wired Bedrock + gateway drafting path."
        )
    return {"recommendation": recommendation, "rationale": rationale, "citations": citations,
            "drafted_by": drafted_by, "current_step": "draft_recommendation",
            "completed_steps": state.get("completed_steps", []) + ["draft_recommendation"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    rationale = state.get("rationale", "")
    grounding = verify_grounding(rationale, {"criteria": state.get("criteria_result", {}),
                                             "necessity": state.get("medical_necessity", {}),
                                             "guideline": state.get("guideline", {}),
                                             "service": state.get("service", "")})
    phi_ok = mask(rationale) == rationale
    findings = []
    if not grounding.grounded:
        findings.append("ungrounded claim in UM rationale")
    if not phi_ok:
        findings.append("PHI detected in UM rationale")
    fr = state.get("fairness_report", {})
    if fr.get("applied") and not fr.get("passes_four_fifths", True):
        findings.append("fairness screen flagged a disparate selection rate")
    return {"grounding_report": grounding.to_audit_dict(), "phi_ok": phi_ok,
            "quality_findings": findings, "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    """Conditional edge target: bounded revision, or proceed to the medical-director gate."""
    ground_issue = not state.get("grounding_report", {}).get("grounded", True)
    if ground_issue and state.get("revision_count", 0) < 1:
        return "draft_recommendation"
    return "medical_director_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    rec = state.get("recommendation")
    if rec == "NEEDS_MORE_INFO":
        action = RecommendedAction.REQUEST_INFO
    elif rec == "MEETS_CRITERIA":
        action = RecommendedAction.RECOMMEND_MEETS
    else:
        action = RecommendedAction.RECOMMEND_NOT_MEET
    return {"recommended_action": action,
            "revision_count": state.get("revision_count", 0) + (1 if state.get("quality_findings") else 0),
            "current_step": "medical_director_gate",
            "completed_steps": state.get("completed_steps", []) + ["medical_director_gate"]}


def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    action = state.get("recommended_action")
    approval = state.get("human_approval")
    claims = state.get("acting_user_claims", {})
    out: Dict[str, Any] = {"current_step": "finalize",
                           "completed_steps": state.get("completed_steps", []) + ["finalize"]}
    if action in (RecommendedAction.RECOMMEND_MEETS, RecommendedAction.RECOMMEND_NOT_MEET) and approval:
        res = gw.draft_um_recommendation(claims, {"case_ref": state.get("case_id", "UM-44120"),
                                                  "recommendation": state.get("recommendation")},
                                         approval=approval)
        out["um_case_ref"] = res.result.get("case_ref") if res.allowed else None
        # The recommendation is forwarded; the determination remains the medical director's.
        out["case_status"] = "RECOMMENDATION_FORWARDED" if res.allowed else "PENDING_REVIEW"
    elif action == RecommendedAction.REQUEST_INFO:
        out["case_status"] = "PENDING_INFO"
    else:
        out["case_status"] = "PENDING_REVIEW"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "recommendation": state.get("recommendation"),
        "case_status": out["case_status"], "drafted_by": state.get("drafted_by"),
        "grounded": state.get("grounding_report", {}).get("grounded"),
        "fairness_applied": state.get("fairness_report", {}).get("applied"),
        "note": "AI recommendation only; coverage determination is the medical director's decision.",
    }]
    return out
