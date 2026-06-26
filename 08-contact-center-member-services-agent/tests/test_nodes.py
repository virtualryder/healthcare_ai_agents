import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "08-contact-center-member-services-agent")]

from agent.core import run_until_gate, resume
from agent.state import RecommendedAction

CLAIMS = {"sub": "msr-1", "custom:hpp_role": "MEMBER_SERVICES_REP"}
APPROVAL = {"approved": True, "reviewer": {"sub": "lead-1"}}
VERIFIED = "verified-idp-token"


def test_claim_status_answers_and_logs():
    s = run_until_gate({"inquiry_type": "claim_status", "member_ref": "MBR-30551",
                        "claim_ref": "CLM-2026-55810", "identity_assertion": VERIFIED,
                        "acting_user_claims": CLAIMS})
    assert s["identity_verified"]
    assert s["grounding_report"]["grounded"] and s["literacy_report"]["passes"]
    assert s["recommended_action"] == RecommendedAction.ANSWER_AND_LOG
    final = resume(s, APPROVAL)
    assert final["case_status"] == "ANSWERED_LOGGED" and final["interaction_logged"]


def test_no_logging_without_approval():
    s = run_until_gate({"inquiry_type": "claim_status", "member_ref": "MBR-30551",
                        "claim_ref": "CLM-2026-55810", "identity_assertion": VERIFIED,
                        "acting_user_claims": CLAIMS})
    final = resume(s, approval=None)
    assert final.get("interaction_logged") is None and final["case_status"] == "PENDING_REVIEW"


def test_benefits_answer_is_grounded():
    s = run_until_gate({"inquiry_type": "benefits", "member_ref": "MBR-30551",
                        "identity_assertion": VERIFIED, "acting_user_claims": CLAIMS})
    assert s["coverage_active"] is True and s["grounding_report"]["grounded"]
    assert s["recommended_action"] == RecommendedAction.ANSWER_AND_LOG


def test_grievance_files_with_approval():
    s = run_until_gate({"inquiry_type": "grievance", "member_ref": "MBR-30551",
                        "grievance_text": "denied with no explanation", "identity_assertion": VERIFIED,
                        "acting_user_claims": CLAIMS})
    assert s["recommended_action"] == RecommendedAction.FILE_GRIEVANCE
    final = resume(s, APPROVAL)
    assert final["case_status"] == "GRIEVANCE_FILED" and final["grievance_ref"]


def test_unverified_identity_blocks_disclosure():
    s = run_until_gate({"inquiry_type": "claim_status", "member_ref": "MBR-30551",
                        "claim_ref": "CLM-2026-55810", "acting_user_claims": CLAIMS})  # no assertion
    assert not s["identity_verified"]
    assert s["recommended_action"] == RecommendedAction.VERIFY_IDENTITY
    assert "account detail requested without verified identity" in s["quality_findings"]
    final = resume(s, APPROVAL)
    assert final["case_status"] == "PENDING_IDENTITY"


def test_inactive_coverage_escalates():
    s = run_until_gate({"inquiry_type": "benefits", "member_ref": "MBR-INACTIVE",
                        "identity_assertion": VERIFIED, "acting_user_claims": CLAIMS})
    assert s["coverage_active"] is False
    assert s["recommended_action"] == RecommendedAction.ESCALATE
    final = resume(s, APPROVAL)
    assert final["case_status"] == "ESCALATED"
