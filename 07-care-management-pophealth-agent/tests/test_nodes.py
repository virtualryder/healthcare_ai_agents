import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "07-care-management-pophealth-agent")]

from agent.core import run_until_gate, resume
from agent.state import RecommendedAction

CLAIMS = {"sub": "care-mgr-1", "custom:hpp_role": "CARE_MANAGER"}
APPROVAL = {"approved": True, "reviewer": {"sub": "lead-1"}}


def test_open_gaps_update_plan_with_signoff():
    s = run_until_gate({"patient_ref": "PT-40012", "acting_user_claims": CLAIMS})
    assert s["open_gaps"]
    assert s["grounding_report"]["grounded"] and s["literacy_report"]["passes"]
    assert s["recommended_action"] == RecommendedAction.UPDATE_CARE_PLAN
    final = resume(s, APPROVAL)
    assert final["case_status"] == "CARE_PLAN_UPDATED" and final["plan_ref"]


def test_no_update_without_signoff():
    s = run_until_gate({"patient_ref": "PT-40012", "acting_user_claims": CLAIMS})
    final = resume(s, approval=None)
    assert final.get("plan_ref") is None and final["case_status"] == "PENDING_REVIEW"


def test_no_gaps_no_action():
    s = run_until_gate({"patient_ref": "PT-40012", "no_gaps": True, "acting_user_claims": CLAIMS})
    assert s["open_gaps"] == []
    assert s["recommended_action"] == RecommendedAction.NO_GAPS
    final = resume(s, APPROVAL)
    assert final["case_status"] == "NO_ACTION" and final.get("plan_ref") is None


def test_part2_without_consent_escalates():
    s = run_until_gate({"patient_ref": "PT-40012", "part2_sensitive": True, "acting_user_claims": CLAIMS})
    assert s["consent_block"] is True
    assert s["recommended_action"] == RecommendedAction.ESCALATE
    final = resume(s, APPROVAL)
    assert final["case_status"] == "ESCALATED" and final.get("plan_ref") is None


def test_fairness_flags_disparate_risk_strat():
    s = run_until_gate({"patient_ref": "PT-40012",
                        "cohort": {"selected": {"A": 80, "B": 30}, "totals": {"A": 100, "B": 100}},
                        "acting_user_claims": CLAIMS})
    assert s["fairness_report"]["applied"] and s["fairness_report"]["passes_four_fifths"] is False
    assert "fairness screen flagged a disparate risk-stratification rate" in s["quality_findings"]
