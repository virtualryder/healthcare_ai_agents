# agent/state.py
# ============================================================
# MemberServicesState — state for the Contact Center / Member Services workflow.
#
# Context of use: the agent answers member inquiries (claim status via X12 276/277,
# benefits/eligibility via 270/271), logs interactions, and intakes grievances —
# drafting tone-matched, health-literate, Section 1557-accessible responses. It
# verifies member identity before any account-specific disclosure; grievance
# creation and interaction logging are gated writes. Amazon Connect is the CCaaS
# substrate.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class InquiryType(str, Enum):
    CLAIM_STATUS = "claim_status"
    BENEFITS = "benefits"
    GRIEVANCE = "grievance"


class RecommendedAction(str, Enum):
    ANSWER_AND_LOG = "ANSWER_AND_LOG"     # answer + gated interaction log
    FILE_GRIEVANCE = "FILE_GRIEVANCE"     # intake a grievance (gated write)
    VERIFY_IDENTITY = "VERIFY_IDENTITY"   # account data requested; verify first
    ESCALATE = "ESCALATE"                 # inactive coverage / complex: route to staff
    REVISE = "REVISE"                     # grounding/literacy issue: bounded revision


class MemberServicesState(TypedDict, total=False):
    # ── Intake ────────────────────────────────────────────────────────────────
    interaction_id: str
    inquiry_type: str            # one of InquiryType
    member_ref: str
    claim_ref: str
    grievance_text: str
    channel: str                 # voice | chat | web
    identity_assertion: str      # verified-IdP assertion (absent => not verified)
    acting_user_claims: Dict[str, Any]

    # ── Identity ──────────────────────────────────────────────────────────────
    needs_identity: bool
    identity_verified: bool

    # ── Retrieved data ────────────────────────────────────────────────────────
    member: Dict[str, Any]
    claim_status: Dict[str, Any]
    eligibility: Dict[str, Any]
    coverage_active: bool
    retrieved_sources: List[Dict[str, Any]]

    # ── Member-facing response ────────────────────────────────────────────────
    response: str
    citations: List[Dict[str, str]]
    drafted_by: str              # bedrock | anthropic | demo-stub

    # ── Compliance check ──────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    literacy_report: Dict[str, Any]
    phi_ok: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    interaction_logged: Optional[str]
    grievance_ref: Optional[str]
    case_status: str             # INTAKE | PENDING_REVIEW | ANSWERED_LOGGED | GRIEVANCE_FILED | PENDING_IDENTITY | ESCALATED
    revision_count: int

    # ── Infra / audit ─────────────────────────────────────────────────────────
    human_approval: Dict[str, Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
