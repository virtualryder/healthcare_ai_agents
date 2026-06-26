# agent/nodes.py
# ============================================================
# Node logic for the Prior-Authorization workflow.
#
# Pure functions (state -> partial state update). Runs in EXTRACT_MODE=demo with
# no LLM call (deterministic requirement check + templated, grounded rationale),
# and uses the LLM factory + gateway tools in live mode. langgraph-free so the
# nodes are unit-testable; graph.py wires them with a framework-enforced HITL
# interrupt before submission.
# ============================================================
from __future__ import annotations

import os
from typing import Any, Dict

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
        "urgent": bool(state.get("urgent", False)),
        "revision_count": state.get("revision_count", 0),
        "case_status": "INTAKE",
        "pa_status": "not requested",
    }


def check_requirement(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    res = gw.check_pa_requirement(claims, state.get("service", ""))
    return {"pa_required": bool(res.get("pa_required")),
            "requirement_source": res.get("source", ""),
            "current_step": "check_requirement",
            "completed_steps": state.get("completed_steps", []) + ["check_requirement"]}


def gather_evidence(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("pa_required"):
        return {"current_step": "gather_evidence",
                "completed_steps": state.get("completed_steps", []) + ["gather_evidence"]}
    claims = state.get("acting_user_claims", {})
    summary = gw.get_patient_summary(claims, state.get("patient_ref", "PT-40012"))
    docs = gw.get_clinical_docs(claims, state.get("encounter_ref", "ENC-88231"))
    necessity = gw.check_medical_necessity(claims, [state.get("service", "")], state.get("diagnosis", []))
    sources = gw.search_policy(claims, f"prior authorization {state.get('service', '')}")
    missing = []
    if not docs.get("documents"):
        missing.append("supporting clinical documentation")
    if not state.get("diagnosis"):
        missing.append("supporting diagnosis (ICD-10)")
    return {"patient_summary": summary, "clinical_docs": docs, "medical_necessity": necessity,
            "retrieved_sources": sources, "missing_info": missing,
            "current_step": "gather_evidence",
            "completed_steps": state.get("completed_steps", []) + ["gather_evidence"]}


def evaluate_criteria(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("pa_required"):
        return {"current_step": "evaluate_criteria",
                "completed_steps": state.get("completed_steps", []) + ["evaluate_criteria"]}
    claims = state.get("acting_user_claims", {})
    result = gw.evaluate_criteria(claims, state.get("service", ""))
    guideline = gw.get_guideline(claims, "MCG-IMAGING")
    return {"criteria_result": result, "guideline": guideline,
            "current_step": "evaluate_criteria",
            "completed_steps": state.get("completed_steps", []) + ["evaluate_criteria"]}


def assemble_packet(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("pa_required"):
        return {"pa_rationale": "", "citations": [], "drafted_by": "n/a",
                "current_step": "assemble_packet",
                "completed_steps": state.get("completed_steps", []) + ["assemble_packet"]}
    sources = state.get("retrieved_sources", [])
    crit = state.get("criteria_result", {})
    guideline = state.get("guideline", {})
    service = state.get("service", "the requested service")
    if _demo() or not sources:
        indications = ", ".join(crit.get("matched_indications", []) or ["documented clinical indications"])
        rationale = (
            f"Prior authorization is requested for {service}. Applying {crit.get('criteria_set', 'clinical')} "
            f"criteria, the case meets the required indications ({indications}). Medical necessity is "
            f"supported per {state.get('medical_necessity', {}).get('source', 'coverage policy')}. "
            f"See guideline {guideline.get('title', '')}."
        )
        citations = [{"title": guideline.get("title", "Clinical guideline"), "url": guideline.get("url", "")}]
        for s in sources:
            citations.append({"title": s.get("title", ""), "url": s.get("url", "")})
        drafted_by = "demo-stub"
    else:  # pragma: no cover - live LLM path
        from hpp_agent_platform.llm_factory import get_llm
        from agent.prompts import PA_RATIONALE_PROMPT
        llm = get_llm("narrative")
        ctx = (f"SERVICE: {service}\nCRITERIA: {crit}\nNECESSITY: {state.get('medical_necessity')}\n"
               f"GUIDELINE: {guideline}\nPATIENT SUMMARY: {state.get('patient_summary')}")
        msg = llm.invoke(f"{PA_RATIONALE_PROMPT}\n\n{ctx}")
        rationale = getattr(msg, "content", str(msg))
        citations = [{"title": guideline.get("title", ""), "url": guideline.get("url", "")}]
        drafted_by = "bedrock"
    return {"pa_rationale": rationale, "citations": citations, "drafted_by": drafted_by,
            "current_step": "assemble_packet",
            "completed_steps": state.get("completed_steps", []) + ["assemble_packet"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    rationale = state.get("pa_rationale", "")
    grounding = verify_grounding(rationale, {"criteria": state.get("criteria_result", {}),
                                             "necessity": state.get("medical_necessity", {}),
                                             "guideline": state.get("guideline", {}),
                                             "service": state.get("service", "")})
    phi_ok = mask(rationale) == rationale
    findings = []
    if state.get("pa_required") and not grounding.grounded:
        findings.append("ungrounded claims present in PA rationale")
    if not phi_ok:
        findings.append("PHI detected in PA rationale")
    if state.get("missing_info"):
        findings.append("missing evidence for the requested service")
    return {"grounding_report": grounding.to_audit_dict(), "phi_ok": phi_ok,
            "quality_findings": findings, "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    """Conditional edge target: bounded revision, or proceed to the human gate."""
    if not state.get("pa_required"):
        return "human_review_gate"
    ground_issue = not state.get("grounding_report", {}).get("grounded", True)
    if ground_issue and not state.get("missing_info") and state.get("revision_count", 0) < 1:
        return "assemble_packet"
    return "human_review_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("pa_required"):
        action = RecommendedAction.NO_PA_REQUIRED
    elif state.get("missing_info"):
        action = RecommendedAction.REQUEST_INFO
    elif state.get("urgent"):
        action = RecommendedAction.ESCALATE_URGENT
    else:
        action = RecommendedAction.SUBMIT_PA
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
    if action in (RecommendedAction.SUBMIT_PA, RecommendedAction.ESCALATE_URGENT) and approval:
        res = gw.submit_pa(claims, {"service": state.get("service"),
                                    "coordinator": (approval or {}).get("reviewer")}, approval=approval)
        if res.allowed:
            out["pa_ref"] = res.result.get("pa_ref")
            status = gw.check_pa_status(claims, out["pa_ref"])  # monitor immediately
            out["pa_status"] = status.get("status", "Submitted")
            out["case_status"] = "ESCALATED" if action == RecommendedAction.ESCALATE_URGENT else "PA_SUBMITTED"
        else:
            out["case_status"] = "PENDING_REVIEW"
    elif action == RecommendedAction.NO_PA_REQUIRED:
        out["case_status"] = "NO_PA"
    elif action == RecommendedAction.REQUEST_INFO:
        out["case_status"] = "PENDING_INFO"
    else:
        out["case_status"] = "PENDING_REVIEW"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "pa_required": state.get("pa_required"),
        "case_status": out["case_status"], "drafted_by": state.get("drafted_by"),
        "grounded": state.get("grounding_report", {}).get("grounded"),
    }]
    return out
