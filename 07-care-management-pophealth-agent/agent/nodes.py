# agent/nodes.py
# ============================================================
# Node logic for the Care Management & Population Health workflow.
#
# Pure functions (state -> partial state update). Runs in EXTRACT_MODE=demo with
# no LLM call (deterministic, plan-grounded outreach), and uses the LLM factory +
# gateway tools in live mode (reference agents 03-08 are deterministic by design; the live LLM path is NOT wired here — see agents 01/02. EXTRACT_MODE=live raises NotImplementedError). A four-fifths fairness screen runs on any provided
# risk-stratification cohort. langgraph-free so nodes are unit-testable.
# ============================================================
from __future__ import annotations

import os
from typing import Any, Dict

from governance.accessibility.wcag import check_plain_language
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
        "part2_sensitive": bool(state.get("part2_sensitive", False)),
        "no_gaps": bool(state.get("no_gaps", False)),
        "revision_count": state.get("revision_count", 0),
        "case_status": "INTAKE",
    }


def load_patient(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    pref = state.get("patient_ref", "PT-40012")
    return {"patient_summary": gw.get_patient_summary(claims, pref),
            "care_plan": gw.get_care_plan(claims, pref),
            "current_step": "load_patient",
            "completed_steps": state.get("completed_steps", []) + ["load_patient"]}


def check_consent(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    consent = gw.check_consent(claims, state.get("patient_ref", "PT-40012"),
                               scope="care_management", part2_sensitive=state.get("part2_sensitive", False))
    return {"consent": consent, "consent_block": not bool(consent.get("granted", True)),
            "current_step": "check_consent",
            "completed_steps": state.get("completed_steps", []) + ["check_consent"]}


def identify_gaps(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    gaps = gw.identify_gaps(claims, state.get("patient_ref", "PT-40012"), no_gaps=state.get("no_gaps", False))
    return {"gaps": gaps, "open_gaps": gaps.get("open_gaps", []),
            "risk_score_hcc": gaps.get("risk_score_hcc", 0.0), "sdoh_flags": gaps.get("sdoh_flags", []),
            "current_step": "identify_gaps",
            "completed_steps": state.get("completed_steps", []) + ["identify_gaps"]}


def fairness_screen(state: Dict[str, Any]) -> Dict[str, Any]:
    cohort = state.get("cohort") or {}
    if cohort.get("selected") and cohort.get("totals"):
        rep = four_fifths(cohort["selected"], cohort["totals"])
        report = {"applied": True, "passes_four_fifths": rep.passes_four_fifths,
                  "impact_ratios": rep.impact_ratios, "flagged_groups": rep.flagged_groups}
    else:
        report = {"applied": False,
                  "note": "single-patient review; disparate-impact screen is applied at the population/model level"}
    return {"fairness_report": report, "current_step": "fairness_screen",
            "completed_steps": state.get("completed_steps", []) + ["fairness_screen"]}


def draft_artifacts(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("consent_block") or not state.get("open_gaps"):
        return {"outreach": "", "care_plan_update": "", "citations": [], "drafted_by": "n/a",
                "current_step": "draft_artifacts",
                "completed_steps": state.get("completed_steps", []) + ["draft_artifacts"]}
    gaps = ", ".join(state.get("open_gaps", []))
    sdoh = ", ".join(state.get("sdoh_flags", []) or [])
    plan = state.get("care_plan", {})
    if _demo():  # deterministic, plan-grounded, plain language
        outreach = ("Hi — we want to help you stay healthy. Our records show you are due for: "
                    f"{gaps}. Please call us to set this up. We can help with any barriers.")
        if sdoh:
            outreach += " Let us know if you need help with transportation or other needs."
        care_plan_update = (f"Proposed updates for {plan.get('program', 'the care plan')}: address open gaps "
                            f"({gaps}); SDOH factors: {sdoh or 'none noted'}; member is rising-risk. "
                            "Care-manager sign-off required.")
        citations = [{"title": plan.get("program", "Care plan"), "url": ""}]
        drafted_by = "demo-stub"
    else:
        # Live LLM drafting is a documented extension point, not wired in this reference
        # agent. Fail loud rather than silently pretend (agents 01/02 show the Bedrock path).
        raise NotImplementedError(
            "live LLM drafting is not implemented in this reference agent; run with "
            "EXTRACT_MODE=demo (deterministic reference workflow). See agents 01/02 "
            "for the wired Bedrock + gateway drafting path."
        )
    return {"outreach": outreach, "care_plan_update": care_plan_update, "citations": citations,
            "drafted_by": drafted_by, "current_step": "draft_artifacts",
            "completed_steps": state.get("completed_steps", []) + ["draft_artifacts"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    outreach = state.get("outreach", "")
    grounding = verify_grounding(outreach + " " + state.get("care_plan_update", ""),
                                 {"gaps": state.get("gaps", {}), "care_plan": state.get("care_plan", {}),
                                  "sdoh": state.get("sdoh_flags", [])})
    literacy = check_plain_language(outreach, max_grade=8.0) if outreach else check_plain_language("ok")
    phi_ok = mask(outreach) == outreach
    findings = []
    if outreach and not grounding.grounded:
        findings.append("ungrounded claim in outreach/care-plan update")
    if not phi_ok:
        findings.append("PHI detected in outreach")
    if outreach and not literacy.passes:
        findings.append("outreach exceeds health-literacy target")
    fr = state.get("fairness_report", {})
    if fr.get("applied") and not fr.get("passes_four_fifths", True):
        findings.append("fairness screen flagged a disparate risk-stratification rate")
    return {"grounding_report": grounding.to_audit_dict(),
            "literacy_report": {"passes": literacy.passes, "issues": literacy.issues},
            "phi_ok": phi_ok, "quality_findings": findings,
            "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    """Conditional edge target: bounded revision, or proceed to the care-manager gate."""
    if state.get("consent_block") or not state.get("open_gaps"):
        return "care_manager_gate"
    findings = state.get("quality_findings", [])
    fixable = ("ungrounded claim in outreach/care-plan update" in findings
               or "outreach exceeds health-literacy target" in findings)
    if fixable and state.get("revision_count", 0) < 1:
        return "draft_artifacts"
    return "care_manager_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("consent_block"):
        action = RecommendedAction.ESCALATE
    elif not state.get("open_gaps"):
        action = RecommendedAction.NO_GAPS
    else:
        action = RecommendedAction.UPDATE_CARE_PLAN
    return {"recommended_action": action,
            "revision_count": state.get("revision_count", 0) + (1 if state.get("quality_findings") else 0),
            "current_step": "care_manager_gate",
            "completed_steps": state.get("completed_steps", []) + ["care_manager_gate"]}


def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    action = state.get("recommended_action")
    approval = state.get("human_approval")
    claims = state.get("acting_user_claims", {})
    out: Dict[str, Any] = {"current_step": "finalize",
                           "completed_steps": state.get("completed_steps", []) + ["finalize"]}
    if action == RecommendedAction.UPDATE_CARE_PLAN and approval:
        res = gw.update_care_plan(claims, {"patient_ref": state.get("patient_ref"),
                                           "gaps": state.get("open_gaps")}, approval=approval)
        out["plan_ref"] = state.get("patient_ref") if res.allowed else None
        out["case_status"] = "CARE_PLAN_UPDATED" if res.allowed else "PENDING_REVIEW"
    elif action == RecommendedAction.NO_GAPS:
        out["case_status"] = "NO_ACTION"
    elif action == RecommendedAction.ESCALATE:
        out["case_status"] = "ESCALATED"
    else:
        out["case_status"] = "PENDING_REVIEW"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "open_gaps": len(state.get("open_gaps", [])),
        "case_status": out["case_status"], "drafted_by": state.get("drafted_by"),
        "grounded": state.get("grounding_report", {}).get("grounded"),
        "fairness_applied": state.get("fairness_report", {}).get("applied"),
        "consent_block": state.get("consent_block"),
    }]
    return out
