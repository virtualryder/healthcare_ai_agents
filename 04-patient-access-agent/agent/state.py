# agent/state.py
# ============================================================
# PatientAccessState — state for the Patient Access workflow.
#
# Context of use: the agent handles SCHEDULING, REGISTRATION, BENEFITS
# VERIFICATION, COST ESTIMATES (No Surprises Act Good Faith Estimate —
# deterministic, never the LLM), REFERRAL STATUS, and FOLLOW-UP. It verifies
# patient identity before disclosing any account/benefit detail, and every write
# (book an appointment, create a registration) passes the human-approval gate.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class TaskType(str, Enum):
    SCHEDULE = "schedule"        # verify -> eligibility -> estimate -> book + register
    BENEFITS = "benefits"        # verify -> eligibility -> estimate (read-only)
    ESTIMATE = "estimate"        # Good Faith Estimate only (pre-service, no identity needed)


class RecommendedAction(str, Enum):
    BOOK_AND_REGISTER = "BOOK_AND_REGISTER"   # gated writes
    PROVIDE_ESTIMATE = "PROVIDE_ESTIMATE"     # read-only benefits/cost answer
    VERIFY_IDENTITY = "VERIFY_IDENTITY"       # account data requested; verify first
    ESCALATE = "ESCALATE"                     # inactive coverage / complex: route to staff
    REVISE = "REVISE"                         # grounding/literacy issue: bounded revision


class PatientAccessState(TypedDict, total=False):
    # ── Intake ────────────────────────────────────────────────────────────────
    request_id: str
    task_type: str               # one of TaskType
    patient_ref: str
    member_ref: str
    service: str                 # requested service / CPT
    identity_assertion: str      # verified-IdP assertion (absent => not verified)
    acting_user_claims: Dict[str, Any]

    # ── Identity ──────────────────────────────────────────────────────────────
    needs_identity: bool
    identity_verified: bool

    # ── Eligibility / estimate / availability ─────────────────────────────────
    eligibility: Dict[str, Any]
    coverage_active: bool
    estimate: Dict[str, Any]
    availability: Dict[str, Any]

    # ── Member-facing summary ─────────────────────────────────────────────────
    summary: str
    citations: List[Dict[str, str]]
    drafted_by: str              # bedrock | anthropic | demo-stub

    # ── Compliance check ──────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    literacy_report: Dict[str, Any]
    phi_ok: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    appointment_ref: Optional[str]
    registration_ref: Optional[str]
    case_status: str             # INTAKE | PENDING_REVIEW | BOOKED | ESTIMATE_PROVIDED | PENDING_IDENTITY | ESCALATED
    revision_count: int

    # ── Infra / audit ─────────────────────────────────────────────────────────
    human_approval: Dict[str, Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
