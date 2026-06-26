# agent/state.py
# ============================================================
# PaymentIntegrityState — state for the Payment Integrity & Coding workflow.
#
# Context of use: the agent suggests and validates codes (ICD-10, CPT/HCPCS),
# runs NCCI/MUE edits and a medical-necessity check, and FLAGS overpayments,
# duplicates, and coding errors for a human payment-integrity reviewer. The agent
# FLAGS; it never recoups, adjusts payment, or submits a claim. The only write is
# a gated review flag/note (pas.update_case).
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    CLEAN = "CLEAN"                        # no issue found; no action
    FLAG_CODING = "FLAG_CODING"            # NCCI/MUE/modifier edit
    FLAG_OVERPAYMENT = "FLAG_OVERPAYMENT"  # billed code not supported by documentation (upcoding risk)
    FLAG_DUPLICATE = "FLAG_DUPLICATE"      # duplicate claim/line
    REQUEST_DOCS = "REQUEST_DOCS"          # medical necessity not supported / docs missing
    REVISE = "REVISE"                      # grounding/quality issue: bounded revision


class PaymentIntegrityState(TypedDict, total=False):
    # ── Intake ────────────────────────────────────────────────────────────────
    case_id: str
    claim_ref: str
    encounter_ref: str
    billed_cpt: List[str]
    billed_icd10: List[str]
    duplicate: bool              # known duplicate signal (e.g. from a dedupe pre-pass)
    simulate_ncci: bool          # review scenario: NCCI edit present
    necessity_supported: bool    # review scenario: coverage supports necessity
    acting_user_claims: Dict[str, Any]

    # ── Loaded claim / docs ───────────────────────────────────────────────────
    claim: Dict[str, Any]
    clinical_docs: Dict[str, Any]

    # ── Coding analysis ───────────────────────────────────────────────────────
    suggested: Dict[str, Any]
    code_validation: Dict[str, Any]
    medical_necessity: Dict[str, Any]
    claim_scrub: Dict[str, Any]

    # ── Findings ──────────────────────────────────────────────────────────────
    issues: List[str]
    finding: str                 # CLEAN | CODING | OVERPAYMENT | DUPLICATE | NEEDS_DOCS
    rationale: str
    citations: List[Dict[str, str]]
    drafted_by: str              # bedrock | anthropic | demo-stub

    # ── Compliance check ──────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    phi_ok: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    flag_ref: Optional[str]
    case_status: str             # INTAKE | PENDING_REVIEW | FLAGGED_FOR_REVIEW | CLEAN_NO_ACTION
    revision_count: int

    # ── Infra / audit ─────────────────────────────────────────────────────────
    human_approval: Dict[str, Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
