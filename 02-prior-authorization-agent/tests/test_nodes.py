import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "02-prior-authorization-agent")]

from agent.core import run_until_gate, resume
from agent.state import RecommendedAction

CLAIMS = {"sub": "pa-1", "custom:hpp_role": "PA_COORDINATOR"}
APPROVAL = {"approved": True, "reviewer": {"sub": "nurse-1"}}


def test_imaging_requires_pa_and_is_grounded():
    s = run_until_gate({"service": "72148", "diagnosis": ["M54.16"], "patient_ref": "PT-40012",
                        "encounter_ref": "ENC-88231", "acting_user_claims": CLAIMS})
    assert s["pa_required"] is True
    assert s["grounding_report"]["grounded"]
    assert s["recommended_action"] == RecommendedAction.SUBMIT_PA
    assert s["_paused_at_gate"] is True


def test_pa_submits_only_with_approval():
    s = run_until_gate({"service": "72148", "diagnosis": ["M54.16"], "encounter_ref": "ENC-88231",
                        "acting_user_claims": CLAIMS})
    final = resume(s, APPROVAL)
    assert final["case_status"] == "PA_SUBMITTED" and final["pa_ref"]
    assert final["pa_status"] == "Approved"


def test_pa_not_submitted_without_approval():
    s = run_until_gate({"service": "72148", "diagnosis": ["M54.16"], "encounter_ref": "ENC-88231",
                        "acting_user_claims": CLAIMS})
    final = resume(s, approval=None)
    assert final.get("pa_ref") is None and final["case_status"] == "PENDING_REVIEW"


def test_office_visit_needs_no_pa():
    s = run_until_gate({"service": "99214", "diagnosis": ["E11.9"], "acting_user_claims": CLAIMS})
    assert s["pa_required"] is False
    assert s["recommended_action"] == RecommendedAction.NO_PA_REQUIRED
    final = resume(s, APPROVAL)
    assert final["case_status"] == "NO_PA"


def test_urgent_case_escalates():
    s = run_until_gate({"service": "70553", "diagnosis": ["G93.40"], "encounter_ref": "ENC-88231",
                        "urgent": True, "acting_user_claims": CLAIMS})
    assert s["recommended_action"] == RecommendedAction.ESCALATE_URGENT
    final = resume(s, APPROVAL)
    assert final["case_status"] == "ESCALATED" and final["pa_ref"]


def test_missing_diagnosis_requests_info():
    s = run_until_gate({"service": "72148", "encounter_ref": "ENC-88231", "acting_user_claims": CLAIMS})
    assert "supporting diagnosis (ICD-10)" in s["missing_info"]
    assert s["recommended_action"] == RecommendedAction.REQUEST_INFO
    final = resume(s, APPROVAL)
    assert final["case_status"] == "PENDING_INFO"
