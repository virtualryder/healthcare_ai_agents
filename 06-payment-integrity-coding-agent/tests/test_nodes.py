import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "06-payment-integrity-coding-agent")]

from agent.core import run_until_gate, resume
from agent.state import RecommendedAction

CLAIMS = {"sub": "coder-1", "custom:hpp_role": "CODING_SPECIALIST"}
APPROVAL = {"approved": True, "reviewer": {"sub": "pi-1"}}
BASE = {"claim_ref": "CLM-2026-55810", "encounter_ref": "ENC-88231", "acting_user_claims": CLAIMS}


def test_clean_claim_no_action():
    s = run_until_gate({**BASE, "billed_cpt": ["99214"], "billed_icd10": ["E11.9"]})
    assert s["finding"] == "CLEAN"
    assert s["grounding_report"]["grounded"]
    assert s["recommended_action"] == RecommendedAction.CLEAN
    final = resume(s, APPROVAL)
    assert final["case_status"] == "CLEAN_NO_ACTION" and final.get("flag_ref") is None


def test_upcoding_flags_overpayment():
    s = run_until_gate({**BASE, "billed_cpt": ["99215"], "billed_icd10": ["E11.9"]})
    assert s["finding"] == "OVERPAYMENT"
    assert s["recommended_action"] == RecommendedAction.FLAG_OVERPAYMENT
    final = resume(s, APPROVAL)
    assert final["case_status"] == "FLAGGED_FOR_REVIEW" and final["flag_ref"]


def test_ncci_edit_flags_coding():
    s = run_until_gate({**BASE, "billed_cpt": ["99214"], "billed_icd10": ["E11.9"], "simulate_ncci": True})
    assert s["finding"] == "CODING"
    assert s["recommended_action"] == RecommendedAction.FLAG_CODING


def test_duplicate_flags_duplicate():
    s = run_until_gate({**BASE, "billed_cpt": ["99214"], "billed_icd10": ["E11.9"], "duplicate": True})
    assert s["finding"] == "DUPLICATE"
    assert s["recommended_action"] == RecommendedAction.FLAG_DUPLICATE


def test_unsupported_necessity_requests_docs():
    s = run_until_gate({**BASE, "billed_cpt": ["99214"], "billed_icd10": ["Z00.00"], "necessity_supported": False})
    assert s["finding"] == "NEEDS_DOCS"
    assert s["recommended_action"] == RecommendedAction.REQUEST_DOCS


def test_flag_not_recorded_without_approval():
    s = run_until_gate({**BASE, "billed_cpt": ["99215"], "billed_icd10": ["E11.9"]})
    final = resume(s, approval=None)
    assert final.get("flag_ref") is None and final["case_status"] == "PENDING_REVIEW"
