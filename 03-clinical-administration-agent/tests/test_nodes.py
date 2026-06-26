import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "03-clinical-administration-agent")]

from agent.core import run_until_gate, resume
from agent.state import RecommendedAction

CLAIMS = {"sub": "ma-1", "custom:hpp_role": "CLINICAL_STAFF"}
APPROVAL = {"approved": True, "reviewer": {"sub": "clinician-1"}}


def test_chart_summary_drafts_and_files_with_signoff():
    s = run_until_gate({"task_type": "chart_summary", "patient_ref": "PT-40012",
                        "encounter_ref": "ENC-88231", "acting_user_claims": CLAIMS})
    assert s["grounding_report"]["grounded"]
    assert s["recommended_action"] == RecommendedAction.FILE_DRAFT
    assert s["_paused_at_gate"] is True
    final = resume(s, APPROVAL)
    assert final["case_status"] == "FILED_FOR_SIGNOFF" and final["note_ref"]


def test_no_file_without_signoff():
    s = run_until_gate({"task_type": "chart_summary", "encounter_ref": "ENC-88231", "acting_user_claims": CLAIMS})
    final = resume(s, approval=None)
    assert final.get("note_ref") is None and final["case_status"] == "PENDING_REVIEW"


def test_visit_prep_is_read_only():
    s = run_until_gate({"task_type": "visit_prep", "patient_ref": "PT-40012",
                        "encounter_ref": "ENC-88231", "acting_user_claims": CLAIMS})
    assert s["recommended_action"] == RecommendedAction.VISIT_PREP_READY
    final = resume(s, APPROVAL)
    assert final["case_status"] == "VISIT_PREP_READY" and final.get("note_ref") is None


def test_discharge_is_patient_facing_and_plain_language():
    s = run_until_gate({"task_type": "discharge_summary", "patient_ref": "PT-40012",
                        "encounter_ref": "ENC-88231", "acting_user_claims": CLAIMS})
    assert s["patient_facing"] is True
    assert s["literacy_report"]["passes"]


def test_part2_without_consent_escalates():
    s = run_until_gate({"task_type": "chart_summary", "patient_ref": "PT-40012",
                        "encounter_ref": "ENC-88231", "part2_sensitive": True, "acting_user_claims": CLAIMS})
    assert s["consent_block"] is True
    assert s["recommended_action"] == RecommendedAction.ESCALATE
    final = resume(s, APPROVAL)
    assert final["case_status"] == "ESCALATED" and final.get("note_ref") is None
