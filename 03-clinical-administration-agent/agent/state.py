# agent/state.py
# ============================================================
# ClinicalAdminState — state for the Clinical-Administration workflow.
#
# Context of use: the agent SUMMARIZES charts, PREPARES visits, COORDINATES
# referrals, DRAFTS discharge documentation, handles INBOX/follow-up, and
# coordinates CARE TRANSITIONS. Every clinical artifact is a DRAFT for a licensed
# clinician to review and sign — the agent holds ehr.draft_note (a draft write,
# human-gated) but no order-entry or signing authority, and it checks consent
# (incl. 42 CFR Part 2) before producing anything from a sensitive record.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class TaskType(str, Enum):
    CHART_SUMMARY = "chart_summary"
    VISIT_PREP = "visit_prep"
    REFERRAL = "referral"
    DISCHARGE_SUMMARY = "discharge_summary"
    INBOX_FOLLOWUP = "inbox_followup"


class RecommendedAction(str, Enum):
    FILE_DRAFT = "FILE_DRAFT"              # draft note/doc -> clinician signs (gated write)
    VISIT_PREP_READY = "VISIT_PREP_READY"  # read-only prep brief, no write
    ESCALATE = "ESCALATE"                  # consent block / sensitive: route to staff
    REVISE = "REVISE"                      # grounding/literacy issue: bounded revision


class ClinicalAdminState(TypedDict, total=False):
    # ── Intake ────────────────────────────────────────────────────────────────
    task_id: str
    task_type: str               # one of TaskType
    patient_ref: str
    encounter_ref: str
    part2_sensitive: bool        # is the source record 42 CFR Part 2 (SUD) data?
    acting_user_claims: Dict[str, Any]

    # ── Chart load ────────────────────────────────────────────────────────────
    patient_summary: Dict[str, Any]
    encounter: Dict[str, Any]
    clinical_docs: Dict[str, Any]
    care_plan: Dict[str, Any]

    # ── Consent ───────────────────────────────────────────────────────────────
    consent: Dict[str, Any]
    consent_block: bool

    # ── Produced artifact ─────────────────────────────────────────────────────
    patient_facing: bool
    artifact: str
    citations: List[Dict[str, str]]
    drafted_by: str              # bedrock | anthropic | demo-stub

    # ── Compliance check ──────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    literacy_report: Dict[str, Any]
    phi_ok: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    note_ref: Optional[str]
    case_status: str             # INTAKE | PENDING_REVIEW | FILED_FOR_SIGNOFF | VISIT_PREP_READY | ESCALATED
    revision_count: int

    # ── Infra / audit ─────────────────────────────────────────────────────────
    human_approval: Dict[str, Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
