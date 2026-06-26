# agent/state.py
# ============================================================
# UtilizationMgmtState — state for the Utilization-Management workflow (payer-side).
#
# Context of use: the agent APPLIES clinical criteria (MCG/InterQual), CHECKS
# coverage (LCD/NCD), runs a FAIRNESS screen on any flag/rank step, and PREPARES a
# RECOMMENDATION for a medical director. The adverse-determination authority
# (payer.issue_determination) is WITHHELD from every agent and held only by a
# UM_MEDICAL_DIRECTOR role — AI assists, a licensed human decides. Even a "does
# not meet" recommendation never auto-denies; it is forwarded for a human
# determination.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    RECOMMEND_MEETS = "RECOMMEND_MEETS"          # evidence meets criteria -> forward to director
    RECOMMEND_NOT_MEET = "RECOMMEND_NOT_MEET"    # evidence does not meet -> forward (never auto-deny)
    REQUEST_INFO = "REQUEST_INFO"                # insufficient evidence -> request more
    REVISE = "REVISE"                            # grounding/quality issue: bounded revision


class UtilizationMgmtState(TypedDict, total=False):
    # ── Intake ────────────────────────────────────────────────────────────────
    case_id: str
    service: str                 # requested service / level of care
    cpt: List[str]
    diagnosis: List[str]
    encounter_ref: str
    pa_ref: Optional[str]
    meets: bool                  # criteria outcome hint for review scenarios
    missing_evidence: bool
    cohort: Dict[str, Any]       # optional {selected:{}, totals:{}} for the fairness screen
    acting_user_claims: Dict[str, Any]

    # ── Clinical evidence ─────────────────────────────────────────────────────
    clinical_docs: Dict[str, Any]
    pa_status: Dict[str, Any]

    # ── Criteria + necessity ──────────────────────────────────────────────────
    criteria_result: Dict[str, Any]
    guideline: Dict[str, Any]
    medical_necessity: Dict[str, Any]

    # ── Fairness ──────────────────────────────────────────────────────────────
    fairness_report: Dict[str, Any]

    # ── Recommendation ────────────────────────────────────────────────────────
    recommendation: str          # MEETS_CRITERIA | DOES_NOT_MEET | NEEDS_MORE_INFO
    rationale: str
    citations: List[Dict[str, str]]
    drafted_by: str              # bedrock | anthropic | demo-stub

    # ── Compliance check ──────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    phi_ok: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    um_case_ref: Optional[str]
    case_status: str             # INTAKE | PENDING_REVIEW | RECOMMENDATION_FORWARDED | PENDING_INFO
    revision_count: int

    # ── Infra / audit ─────────────────────────────────────────────────────────
    human_approval: Dict[str, Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
