# agent/state.py
# ============================================================
# PriorAuthState — state for the Prior-Authorization workflow.
#
# Context of use: the agent DETERMINES whether a requested service needs prior
# authorization, GATHERS the medical evidence, EVALUATES clinical criteria
# (MCG/InterQual), ASSEMBLES the submission, MONITORS status, REQUESTS missing
# information, and ESCALATES urgent cases. It ASSEMBLES and (on approval) SUBMITS
# the request — but the coverage determination is ALWAYS the payer's; the agent
# never issues one, and it never submits without a PA nurse's approval.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    SUBMIT_PA = "SUBMIT_PA"                # assemble + human-approved submit
    NO_PA_REQUIRED = "NO_PA_REQUIRED"      # service does not require PA
    REQUEST_INFO = "REQUEST_INFO"          # missing evidence before submission
    ESCALATE_URGENT = "ESCALATE_URGENT"    # expedited/urgent: route to staff fast
    REVISE = "REVISE"                      # grounding/quality issue: bounded revision


class PriorAuthState(TypedDict, total=False):
    # ── Intake ────────────────────────────────────────────────────────────────
    case_id: str
    patient_ref: str
    encounter_ref: str
    service: str                 # requested service / CPT / HCPCS
    diagnosis: List[str]         # supporting ICD-10
    urgent: bool
    acting_user_claims: Dict[str, Any]

    # ── Requirement determination ─────────────────────────────────────────────
    pa_required: bool
    requirement_source: str      # Da Vinci CRD / payer policy

    # ── Evidence assembly ─────────────────────────────────────────────────────
    patient_summary: Dict[str, Any]
    clinical_docs: Dict[str, Any]
    medical_necessity: Dict[str, Any]
    retrieved_sources: List[Dict[str, Any]]
    missing_info: List[str]

    # ── Criteria evaluation ───────────────────────────────────────────────────
    criteria_result: Dict[str, Any]
    guideline: Dict[str, Any]

    # ── Assembled packet ──────────────────────────────────────────────────────
    pa_rationale: str
    citations: List[Dict[str, str]]
    drafted_by: str              # bedrock | anthropic | demo-stub

    # ── Compliance check ──────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    phi_ok: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    pa_ref: Optional[str]
    pa_status: str               # not requested | Submitted | Approved | ...
    case_status: str             # INTAKE | PENDING_REVIEW | PA_SUBMITTED | NO_PA | PENDING_INFO | ESCALATED
    revision_count: int

    # ── Infra / audit ─────────────────────────────────────────────────────────
    human_approval: Dict[str, Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
