# agent/state.py
# ============================================================
# RevenueCycleState — state for the Revenue-Cycle & Denial workflow.
#
# Context of use: the agent REVIEWS a claim (before submission or after a
# denial), IDENTIFIES missing documentation, DETERMINES the likely root cause of
# a denial from the payer remittance, DRAFTS a grounded appeal, and TRACKS the
# payer response — updating the case-management system. It NEVER submits a claim
# (a biller does) and never submits an appeal without a denials specialist's
# approval at the gateway's human gate.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    APPEAL = "APPEAL"                          # draft appeal -> human-approved submit
    CORRECT_AND_RESUBMIT = "CORRECT_AND_RESUBMIT"  # coding/registration fix -> biller resubmits
    REQUEST_DOCUMENTATION = "REQUEST_DOCUMENTATION"  # missing docs before action
    WRITE_OFF = "WRITE_OFF"                    # recommend adjustment (human decides)
    REVISE = "REVISE"                          # grounding/quality issue: bounded revision
    ESCALATE = "ESCALATE"                      # complex/clinical: route to staff


class RevenueCycleState(TypedDict, total=False):
    # ── Intake ────────────────────────────────────────────────────────────────
    case_id: str
    claim_ref: str
    mode: str                    # PRE_SUBMISSION | POST_DENIAL
    acting_user_claims: Dict[str, Any]

    # ── Loaded claim / account ────────────────────────────────────────────────
    claim: Dict[str, Any]
    account: Dict[str, Any]

    # ── Denial analysis ───────────────────────────────────────────────────────
    denial_codes: List[str]
    root_cause: str              # authorization | medical_necessity | coding | eligibility | timely_filing | other
    appealable: bool

    # ── Evidence assembly ─────────────────────────────────────────────────────
    clinical_docs: Dict[str, Any]
    coding_validation: Dict[str, Any]
    medical_necessity: Dict[str, Any]
    retrieved_sources: List[Dict[str, Any]]
    missing_documentation: List[str]

    # ── Drafted appeal ────────────────────────────────────────────────────────
    appeal_letter: str
    citations: List[Dict[str, str]]
    drafted_by: str              # bedrock | anthropic | demo-stub

    # ── Compliance check ──────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    literacy_report: Dict[str, Any]
    phi_ok: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    appeal_ref: Optional[str]
    case_status: str             # INTAKE | PENDING_REVIEW | APPEAL_SUBMITTED | RESUBMIT_QUEUED | ESCALATED | CLOSED
    revision_count: int

    # ── Infra / audit ─────────────────────────────────────────────────────────
    human_approval: Dict[str, Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
