# agent/nodes.py
# ============================================================
# Node logic for the Clinical-Administration workflow.
#
# Pure functions (state -> partial state update). Runs in EXTRACT_MODE=demo with
# no LLM call (deterministic, chart-grounded templates), and uses the LLM factory
# + gateway tools in live mode. langgraph-free so nodes are unit-testable;
# graph.py wires them with a framework-enforced clinician sign-off interrupt.
# ============================================================
from __future__ import annotations

import os
from typing import Any, Dict

from governance.accessibility.wcag import check_plain_language
from governance.grounding import verify_grounding
from hpp_agent_platform.phi import mask

from tools import gateway_tools as gw
from agent.state import RecommendedAction, TaskType

# Patient-facing tasks must pass a stricter health-literacy bar.
_PATIENT_FACING = {TaskType.DISCHARGE_SUMMARY.value, TaskType.INBOX_FOLLOWUP.value}


def _demo() -> bool:
    return os.getenv("EXTRACT_MODE", "demo").strip().lower() == "demo"


def intake(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "current_step": "intake",
        "completed_steps": state.get("completed_steps", []) + ["intake"],
        "task_type": state.get("task_type", TaskType.CHART_SUMMARY.value),
        "part2_sensitive": bool(state.get("part2_sensitive", False)),
        "revision_count": state.get("revision_count", 0),
        "case_status": "INTAKE",
    }


def load_chart(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    pref = state.get("patient_ref", "PT-40012")
    eref = state.get("encounter_ref", "ENC-88231")
    return {"patient_summary": gw.get_patient_summary(claims, pref),
            "encounter": gw.get_encounter(claims, eref),
            "clinical_docs": gw.get_clinical_docs(claims, eref),
            "care_plan": gw.get_care_plan(claims, pref),
            "current_step": "load_chart",
            "completed_steps": state.get("completed_steps", []) + ["load_chart"]}


def check_consent(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    consent = gw.check_consent(claims, state.get("patient_ref", "PT-40012"),
                               scope="clinical_admin", part2_sensitive=state.get("part2_sensitive", False))
    return {"consent": consent, "consent_block": not bool(consent.get("granted", True)),
            "current_step": "check_consent",
            "completed_steps": state.get("completed_steps", []) + ["check_consent"]}


def produce_artifact(state: Dict[str, Any]) -> Dict[str, Any]:
    task = state.get("task_type", TaskType.CHART_SUMMARY.value)
    patient_facing = task in _PATIENT_FACING
    if state.get("consent_block"):
        return {"artifact": "", "citations": [], "drafted_by": "n/a", "patient_facing": patient_facing,
                "current_step": "produce_artifact",
                "completed_steps": state.get("completed_steps", []) + ["produce_artifact"]}
    summary = state.get("patient_summary", {})
    enc = state.get("encounter", {})
    plan = state.get("care_plan", {})
    problems = ", ".join(summary.get("active_problems", []) or ["no active problems on file"])
    meds = ", ".join(summary.get("active_meds", []) or ["none"])
    goals = ", ".join(plan.get("goals", []) or [])
    if _demo() or True:  # deterministic, chart-grounded draft (demo default)
        if task == TaskType.VISIT_PREP.value:
            artifact = (f"Visit prep: active problems {problems}. Current medications {meds}. "
                        f"Open care-plan items: {goals}. Last encounter type {enc.get('type', 'n/a')}.")
        elif task == TaskType.DISCHARGE_SUMMARY.value:
            artifact = ("Discharge summary (draft): You were seen for your ongoing conditions. "
                        f"Keep taking your medicines: {meds}. Follow your care plan goals: {goals}. "
                        "Call the clinic if you feel worse. A nurse will review this with you.")
        elif task == TaskType.INBOX_FOLLOWUP.value:
            artifact = ("Reply (draft): Thank you for your message. Your records show active care for "
                        f"{problems}. Please keep your next visit and continue {meds}. We will follow up.")
        elif task == TaskType.REFERRAL.value:
            artifact = (f"Referral note (draft): Referring for specialty evaluation of {problems}. "
                        f"Current medications {meds}. Relevant care-plan goals: {goals}.")
        else:  # chart_summary
            artifact = (f"Chart summary (draft): Active problems {problems}. Medications {meds}. "
                        f"Recent encounter {enc.get('type', 'n/a')}. Open care-plan items: {goals}.")
        citations = [{"title": "Care plan", "url": ""}] if goals else []
        drafted_by = "demo-stub"
    return {"artifact": artifact, "citations": citations, "drafted_by": drafted_by,
            "patient_facing": patient_facing, "current_step": "produce_artifact",
            "completed_steps": state.get("completed_steps", []) + ["produce_artifact"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    artifact = state.get("artifact", "")
    grounding = verify_grounding(artifact, {"summary": state.get("patient_summary", {}),
                                            "encounter": state.get("encounter", {}),
                                            "care_plan": state.get("care_plan", {})})
    max_grade = 8.0 if state.get("patient_facing") else 14.0
    literacy = check_plain_language(artifact, max_grade=max_grade) if artifact else check_plain_language("ok")
    phi_ok = mask(artifact) == artifact
    findings = []
    if artifact and not grounding.grounded:
        findings.append("ungrounded clinical claim in artifact")
    if not phi_ok:
        findings.append("PHI detected in artifact")
    if state.get("patient_facing") and not literacy.passes:
        findings.append("patient-facing text exceeds health-literacy target")
    return {"grounding_report": grounding.to_audit_dict(),
            "literacy_report": {"passes": literacy.passes, "issues": literacy.issues},
            "phi_ok": phi_ok, "quality_findings": findings,
            "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    """Conditional edge target: bounded revision, or proceed to the clinician gate."""
    if state.get("consent_block"):
        return "clinician_review_gate"
    findings = state.get("quality_findings", [])
    fixable = ("ungrounded clinical claim in artifact" in findings
               or "patient-facing text exceeds health-literacy target" in findings)
    if fixable and state.get("revision_count", 0) < 1:
        return "produce_artifact"
    return "clinician_review_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("consent_block"):
        action = RecommendedAction.ESCALATE
    elif state.get("task_type") == TaskType.VISIT_PREP.value:
        action = RecommendedAction.VISIT_PREP_READY
    else:
        action = RecommendedAction.FILE_DRAFT
    return {"recommended_action": action,
            "revision_count": state.get("revision_count", 0) + (1 if state.get("quality_findings") else 0),
            "current_step": "clinician_review_gate",
            "completed_steps": state.get("completed_steps", []) + ["clinician_review_gate"]}


def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    action = state.get("recommended_action")
    approval = state.get("human_approval")
    claims = state.get("acting_user_claims", {})
    out: Dict[str, Any] = {"current_step": "finalize",
                           "completed_steps": state.get("completed_steps", []) + ["finalize"]}
    if action == RecommendedAction.FILE_DRAFT and approval:
        res = gw.draft_note(claims, {"encounter_ref": state.get("encounter_ref"),
                                     "task_type": state.get("task_type")}, approval=approval)
        out["note_ref"] = state.get("encounter_ref") if res.allowed else None
        out["case_status"] = "FILED_FOR_SIGNOFF" if res.allowed else "PENDING_REVIEW"
    elif action == RecommendedAction.VISIT_PREP_READY:
        out["case_status"] = "VISIT_PREP_READY"
    elif action == RecommendedAction.ESCALATE:
        out["case_status"] = "ESCALATED"
    else:
        out["case_status"] = "PENDING_REVIEW"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "task_type": state.get("task_type"),
        "case_status": out["case_status"], "drafted_by": state.get("drafted_by"),
        "grounded": state.get("grounding_report", {}).get("grounded"),
        "consent_block": state.get("consent_block"),
    }]
    return out
