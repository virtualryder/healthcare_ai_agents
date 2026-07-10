# agent/nodes.py
# ============================================================
# Node logic for the Payment Integrity & Coding workflow.
#
# Pure functions (state -> partial state update). Runs in EXTRACT_MODE=demo with
# no LLM call (deterministic edit/necessity comparison + templated finding), and
# uses the LLM factory + gateway tools in live mode (reference agents 03-08 are deterministic by design; the live LLM path is NOT wired here — see agents 01/02. EXTRACT_MODE=live raises NotImplementedError). The agent FLAGS for human
# review; it never recoups, adjusts payment, or submits. langgraph-free so nodes
# are unit-testable.
# ============================================================
from __future__ import annotations

import os
from typing import Any, Dict, List

from governance.grounding import verify_grounding
from hpp_agent_platform.phi import mask

from tools import gateway_tools as gw
from agent.state import RecommendedAction

# Illustrative E/M ordering so an overpayment/upcoding mismatch is detectable.
_EM_LEVEL = {"99211": 1, "99212": 2, "99213": 3, "99214": 4, "99215": 5}


def _demo() -> bool:
    return os.getenv("EXTRACT_MODE", "demo").strip().lower() == "demo"


def intake(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "current_step": "intake",
        "completed_steps": state.get("completed_steps", []) + ["intake"],
        "duplicate": bool(state.get("duplicate", False)),
        "simulate_ncci": bool(state.get("simulate_ncci", False)),
        "necessity_supported": bool(state.get("necessity_supported", True)),
        "revision_count": state.get("revision_count", 0),
        "case_status": "INTAKE",
    }


def load_claim(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    claim = gw.get_claim(claims, state.get("claim_ref", "CLM-2026-55810"))
    docs = gw.get_clinical_docs(claims, state.get("encounter_ref", "ENC-88231"))
    billed_cpt = state.get("billed_cpt") or claim.get("cpt", [])
    billed_icd10 = state.get("billed_icd10") or claim.get("icd10", [])
    return {"claim": claim, "clinical_docs": docs,
            "billed_cpt": billed_cpt, "billed_icd10": billed_icd10,
            "current_step": "load_claim",
            "completed_steps": state.get("completed_steps", []) + ["load_claim"]}


def analyze_coding(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    suggested = gw.suggest_codes(claims, state.get("encounter_ref", "ENC-88231"))
    validation = gw.validate_codes(claims, state.get("billed_cpt", []), state.get("billed_icd10", []),
                                   ncci=state.get("simulate_ncci", False))
    necessity = gw.check_medical_necessity(claims, state.get("billed_cpt", []),
                                           state.get("billed_icd10", []),
                                           supported=state.get("necessity_supported", True))
    scrub = gw.validate_claim(claims, state.get("claim_ref", "CLM-2026-55810"))
    return {"suggested": suggested, "code_validation": validation, "medical_necessity": necessity,
            "claim_scrub": scrub, "current_step": "analyze_coding",
            "completed_steps": state.get("completed_steps", []) + ["analyze_coding"]}


def _overpayment(billed: List[str], supported: List[str]) -> bool:
    """True if a billed E/M level exceeds the documentation-supported level."""
    b = max((_EM_LEVEL.get(c, 0) for c in billed), default=0)
    s = max((_EM_LEVEL.get(c, 0) for c in supported), default=0)
    return b > 0 and s > 0 and b > s


def detect_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    validation = state.get("code_validation", {})
    necessity = state.get("medical_necessity", {})
    suggested = state.get("suggested", {}).get("suggested_cpt", [])
    billed = state.get("billed_cpt", [])
    issues: List[str] = []
    if validation.get("ncci_edits"):
        issues.append("NCCI bundling edit: a component service is billed separately")
    if validation.get("mue_violations"):
        issues.append("MUE violation: billed units exceed the medically unlikely edit")
    overpay = _overpayment(billed, suggested)
    if overpay:
        issues.append("Upcoding risk: billed E/M level exceeds the documentation-supported level")
    if state.get("duplicate"):
        issues.append("Duplicate claim/line detected")
    if not necessity.get("supported", True):
        issues.append("Medical necessity not supported by the documented diagnosis")

    if state.get("duplicate"):
        finding = "DUPLICATE"
    elif overpay:
        finding = "OVERPAYMENT"
    elif validation.get("ncci_edits") or validation.get("mue_violations"):
        finding = "CODING"
    elif not necessity.get("supported", True):
        finding = "NEEDS_DOCS"
    else:
        finding = "CLEAN"
    return {"issues": issues, "finding": finding, "current_step": "detect_issues",
            "completed_steps": state.get("completed_steps", []) + ["detect_issues"]}


def draft_finding(state: Dict[str, Any]) -> Dict[str, Any]:
    finding = state.get("finding", "CLEAN")
    billed = ", ".join(state.get("billed_cpt", []) or ["the billed codes"])
    supported = ", ".join(state.get("suggested", {}).get("suggested_cpt", []) or ["the documented codes"])
    necessity = state.get("medical_necessity", {})
    if _demo():  # deterministic, evidence-grounded finding
        if finding == "CLEAN":
            rationale = (f"Review complete: billed codes ({billed}) are consistent with the documentation "
                         f"and pass NCCI/MUE edits. No payment-integrity issue identified.")
        elif finding == "OVERPAYMENT":
            rationale = (f"Flag for review: billed E/M ({billed}) exceeds the documentation-supported level "
                         f"({supported}). Potential upcoding; a payment-integrity reviewer should confirm.")
        elif finding == "CODING":
            rationale = (f"Flag for review: a coding edit applies to the billed codes ({billed}). "
                         f"See the NCCI/MUE result; a coder should confirm bundling/units.")
        elif finding == "DUPLICATE":
            rationale = (f"Flag for review: this claim/line for {billed} appears to duplicate a prior "
                         f"submission. A reviewer should confirm before any action.")
        else:  # NEEDS_DOCS
            rationale = (f"Flag for review: medical necessity for {billed} is not supported per "
                         f"{necessity.get('source', 'coverage policy')}. Request supporting documentation.")
        citations = [{"title": necessity.get("source", "CMS LCD/NCD coverage database"), "url": ""}]
        drafted_by = "demo-stub"
    else:
        # Live LLM drafting is a documented extension point, not wired in this reference
        # agent. Fail loud rather than silently pretend (agents 01/02 show the Bedrock path).
        raise NotImplementedError(
            "live LLM drafting is not implemented in this reference agent; run with "
            "EXTRACT_MODE=demo (deterministic reference workflow). See agents 01/02 "
            "for the wired Bedrock + gateway drafting path."
        )
    return {"rationale": rationale, "citations": citations, "drafted_by": drafted_by,
            "current_step": "draft_finding",
            "completed_steps": state.get("completed_steps", []) + ["draft_finding"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    rationale = state.get("rationale", "")
    grounding = verify_grounding(rationale, {"validation": state.get("code_validation", {}),
                                             "necessity": state.get("medical_necessity", {}),
                                             "suggested": state.get("suggested", {}),
                                             "billed_cpt": state.get("billed_cpt", [])})
    phi_ok = mask(rationale) == rationale
    findings = []
    if not grounding.grounded:
        findings.append("ungrounded claim in coding finding")
    if not phi_ok:
        findings.append("PHI detected in coding finding")
    return {"grounding_report": grounding.to_audit_dict(), "phi_ok": phi_ok,
            "quality_findings": findings, "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    """Conditional edge target: bounded revision, or proceed to the review gate."""
    ground_issue = not state.get("grounding_report", {}).get("grounded", True)
    if ground_issue and state.get("revision_count", 0) < 1:
        return "draft_finding"
    return "review_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    finding = state.get("finding")
    action = {
        "CLEAN": RecommendedAction.CLEAN,
        "OVERPAYMENT": RecommendedAction.FLAG_OVERPAYMENT,
        "CODING": RecommendedAction.FLAG_CODING,
        "DUPLICATE": RecommendedAction.FLAG_DUPLICATE,
        "NEEDS_DOCS": RecommendedAction.REQUEST_DOCS,
    }.get(finding, RecommendedAction.CLEAN)
    return {"recommended_action": action,
            "revision_count": state.get("revision_count", 0) + (1 if state.get("quality_findings") else 0),
            "current_step": "review_gate",
            "completed_steps": state.get("completed_steps", []) + ["review_gate"]}


def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    action = state.get("recommended_action")
    approval = state.get("human_approval")
    claims = state.get("acting_user_claims", {})
    flag_actions = {RecommendedAction.FLAG_OVERPAYMENT, RecommendedAction.FLAG_CODING,
                    RecommendedAction.FLAG_DUPLICATE, RecommendedAction.REQUEST_DOCS}
    out: Dict[str, Any] = {"current_step": "finalize",
                           "completed_steps": state.get("completed_steps", []) + ["finalize"]}
    if action in flag_actions and approval:
        res = gw.update_case(claims, {"case_ref": state.get("case_id", "CASE-30021"),
                                      "status": f"PAYMENT_INTEGRITY_{state.get('finding')}"},
                             approval=approval)
        out["flag_ref"] = res.result.get("case_ref") if res.allowed else None
        out["case_status"] = "FLAGGED_FOR_REVIEW" if res.allowed else "PENDING_REVIEW"
    elif action == RecommendedAction.CLEAN:
        out["case_status"] = "CLEAN_NO_ACTION"
    else:
        out["case_status"] = "PENDING_REVIEW"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "finding": state.get("finding"),
        "case_status": out["case_status"], "drafted_by": state.get("drafted_by"),
        "grounded": state.get("grounding_report", {}).get("grounded"),
        "note": "AI flags for human review; no recoupment, payment adjustment, or submission is performed.",
    }]
    return out
