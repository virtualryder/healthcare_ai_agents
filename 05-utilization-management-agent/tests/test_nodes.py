import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "05-utilization-management-agent")]

from agent.core import run_until_gate, resume
from agent.state import RecommendedAction

CLAIMS = {"sub": "um-nurse-1", "custom:hpp_role": "UM_NURSE"}
APPROVAL = {"approved": True, "reviewer": {"sub": "med-director-1"}}


def test_meets_criteria_recommends_and_forwards():
    s = run_until_gate({"service": "inpatient admission", "cpt": ["99223"], "diagnosis": ["I50.9"],
                        "encounter_ref": "ENC-88231", "meets": True, "acting_user_claims": CLAIMS})
    assert s["recommendation"] == "MEETS_CRITERIA"
    assert s["grounding_report"]["grounded"]
    assert s["recommended_action"] == RecommendedAction.RECOMMEND_MEETS
    final = resume(s, APPROVAL)
    assert final["case_status"] == "RECOMMENDATION_FORWARDED" and final["um_case_ref"]


def test_does_not_meet_is_forwarded_never_auto_denied():
    s = run_until_gate({"service": "inpatient admission", "cpt": ["99223"], "diagnosis": ["I50.9"],
                        "encounter_ref": "ENC-88231", "meets": False, "acting_user_claims": CLAIMS})
    assert s["recommendation"] == "DOES_NOT_MEET"
    assert s["recommended_action"] == RecommendedAction.RECOMMEND_NOT_MEET
    final = resume(s, APPROVAL)
    # even an adverse recommendation is forwarded for a human determination, never auto-denied
    assert final["case_status"] == "RECOMMENDATION_FORWARDED"


def test_recommendation_not_recorded_without_approval():
    s = run_until_gate({"service": "inpatient admission", "cpt": ["99223"], "diagnosis": ["I50.9"],
                        "encounter_ref": "ENC-88231", "meets": True, "acting_user_claims": CLAIMS})
    final = resume(s, approval=None)
    assert final.get("um_case_ref") is None and final["case_status"] == "PENDING_REVIEW"


def test_missing_evidence_requests_info():
    s = run_until_gate({"service": "observation", "cpt": ["99224"], "diagnosis": ["R07.9"],
                        "encounter_ref": "ENC-88231", "missing_evidence": True, "acting_user_claims": CLAIMS})
    assert s["recommendation"] == "NEEDS_MORE_INFO"
    assert s["recommended_action"] == RecommendedAction.REQUEST_INFO
    final = resume(s, APPROVAL)
    assert final["case_status"] == "PENDING_INFO"


def test_fairness_screen_flags_disparate_cohort():
    s = run_until_gate({"service": "inpatient admission", "cpt": ["99223"], "diagnosis": ["I50.9"],
                        "encounter_ref": "ENC-88231", "meets": True,
                        "cohort": {"selected": {"A": 80, "B": 30}, "totals": {"A": 100, "B": 100}},
                        "acting_user_claims": CLAIMS})
    assert s["fairness_report"]["applied"] is True
    assert s["fairness_report"]["passes_four_fifths"] is False
    assert "fairness screen flagged a disparate selection rate" in s["quality_findings"]
