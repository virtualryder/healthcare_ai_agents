import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "04-patient-access-agent")]

from agent.core import run_until_gate, resume
from agent.state import RecommendedAction

CLAIMS = {"sub": "access-1", "custom:hpp_role": "PATIENT_ACCESS_REP"}
APPROVAL = {"approved": True, "reviewer": {"sub": "lead-1"}}
VERIFIED = "verified-idp-token"


def test_schedule_books_and_registers_with_approval():
    s = run_until_gate({"task_type": "schedule", "patient_ref": "PT-40012", "member_ref": "MBR-30551",
                        "service": "99214", "identity_assertion": VERIFIED, "acting_user_claims": CLAIMS})
    assert s["identity_verified"] and s["coverage_active"]
    assert s["grounding_report"]["grounded"] and s["literacy_report"]["passes"]
    assert s["recommended_action"] == RecommendedAction.BOOK_AND_REGISTER
    final = resume(s, APPROVAL)
    assert final["case_status"] == "BOOKED" and final["appointment_ref"] and final["registration_ref"]


def test_no_booking_without_approval():
    s = run_until_gate({"task_type": "schedule", "member_ref": "MBR-30551", "patient_ref": "PT-40012",
                        "service": "99214", "identity_assertion": VERIFIED, "acting_user_claims": CLAIMS})
    final = resume(s, approval=None)
    assert final.get("appointment_ref") is None and final["case_status"] == "PENDING_REVIEW"


def test_benefits_is_read_only_estimate():
    s = run_until_gate({"task_type": "benefits", "member_ref": "MBR-30551", "patient_ref": "PT-40012",
                        "service": "99214", "identity_assertion": VERIFIED, "acting_user_claims": CLAIMS})
    assert s["recommended_action"] == RecommendedAction.PROVIDE_ESTIMATE
    final = resume(s, APPROVAL)
    assert final["case_status"] == "ESTIMATE_PROVIDED" and final.get("appointment_ref") is None


def test_estimate_only_needs_no_identity():
    s = run_until_gate({"task_type": "estimate", "service": "99214", "acting_user_claims": CLAIMS})
    assert s["needs_identity"] is False
    assert s["estimate"]["basis"].startswith("Good Faith Estimate")
    assert s["recommended_action"] == RecommendedAction.PROVIDE_ESTIMATE


def test_unverified_identity_blocks_disclosure():
    s = run_until_gate({"task_type": "schedule", "member_ref": "MBR-30551", "patient_ref": "PT-40012",
                        "service": "99214", "acting_user_claims": CLAIMS})  # no assertion
    assert s["needs_identity"] and not s["identity_verified"]
    assert s["recommended_action"] == RecommendedAction.VERIFY_IDENTITY
    assert "account detail requested without verified identity" in s["quality_findings"]
    final = resume(s, APPROVAL)
    assert final["case_status"] == "PENDING_IDENTITY"


def test_inactive_coverage_escalates():
    s = run_until_gate({"task_type": "benefits", "member_ref": "MBR-INACTIVE", "patient_ref": "PT-40012",
                        "service": "99214", "identity_assertion": VERIFIED, "acting_user_claims": CLAIMS})
    assert s["coverage_active"] is False
    assert s["recommended_action"] == RecommendedAction.ESCALATE
    final = resume(s, APPROVAL)
    assert final["case_status"] == "ESCALATED"
