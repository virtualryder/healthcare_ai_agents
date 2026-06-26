# agent/state.py
# ============================================================
# CareManagementState — state for the Care Management & Population Health workflow.
#
# Context of use: the agent IDENTIFIES care gaps, STRATIFIES risk (HCC/RAF),
# surfaces SDOH factors, runs a FAIRNESS screen on the risk-stratification step,
# and PREPARES outreach + care-plan updates for a care manager. Care-plan writes
# are gated (care-manager sign-off); a 42 CFR Part 2 (SUD) record without consent
# never produces outreach — it escalates. The care manager owns the plan.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    UPDATE_CARE_PLAN = "UPDATE_CARE_PLAN"  # propose gaps/outreach -> care-manager sign-off (gated write)
    NO_GAPS = "NO_GAPS"                    # no open gaps; no action
    ESCALATE = "ESCALATE"                  # consent block / sensitive: route to staff
    REVISE = "REVISE"                      # grounding/literacy issue: bounded revision


class CareManagementState(TypedDict, total=False):
    # ── Intake ────────────────────────────────────────────────────────────────
    case_id: str
    patient_ref: str
    part2_sensitive: bool         # source is 42 CFR Part 2 (SUD) data?
    no_gaps: bool                 # review scenario: patient has no open gaps
    cohort: Dict[str, Any]        # optional {selected:{}, totals:{}} for the fairness screen
    acting_user_claims: Dict[str, Any]

    # ── Patient + plan ────────────────────────────────────────────────────────
    patient_summary: Dict[str, Any]
    care_plan: Dict[str, Any]

    # ── Consent ───────────────────────────────────────────────────────────────
    consent: Dict[str, Any]
    consent_block: bool

    # ── Gaps + risk + SDOH ────────────────────────────────────────────────────
    gaps: Dict[str, Any]
    open_gaps: List[str]
    risk_score_hcc: float
    sdoh_flags: List[str]

    # ── Fairness ──────────────────────────────────────────────────────────────
    fairness_report: Dict[str, Any]

    # ── Drafted artifacts ─────────────────────────────────────────────────────
    outreach: str
    care_plan_update: str
    citations: List[Dict[str, str]]
    drafted_by: str               # bedrock | anthropic | demo-stub

    # ── Compliance check ──────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    literacy_report: Dict[str, Any]
    phi_ok: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    plan_ref: Optional[str]
    case_status: str              # INTAKE | PENDING_REVIEW | CARE_PLAN_UPDATED | NO_ACTION | ESCALATED
    revision_count: int

    # ── Infra / audit ─────────────────────────────────────────────────────────
    human_approval: Dict[str, Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
