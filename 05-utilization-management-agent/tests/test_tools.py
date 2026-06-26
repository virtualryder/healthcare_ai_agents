import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "05-utilization-management-agent")]

from tools import gateway_tools as gw

NURSE = {"sub": "um-nurse-1", "custom:hpp_role": "UM_NURSE"}
DIRECTOR = {"sub": "md-1", "custom:hpp_role": "UM_MEDICAL_DIRECTOR"}


def test_criteria_evaluate_honors_meets():
    assert gw.evaluate_criteria(NURSE, "inpatient admission", meets=True)["meets_criteria"] is True
    assert gw.evaluate_criteria(NURSE, "inpatient admission", meets=False)["meets_criteria"] is False


def test_draft_recommendation_requires_approval():
    res = gw.draft_um_recommendation(NURSE, {"case_ref": "UM-1", "recommendation": "MEETS_CRITERIA"})
    assert res.decision == "PENDING_APPROVAL"


def test_draft_recommendation_with_approval_allows():
    res = gw.draft_um_recommendation(NURSE, {"case_ref": "UM-1", "recommendation": "MEETS_CRITERIA"},
                                     approval={"approved": True, "reviewer": {"sub": "md-1"}})
    assert res.decision == "ALLOW" and res.result["requires_medical_director"] is True


def test_agent_cannot_issue_determination_even_as_director():
    # The determination authority is WITHHELD from the agent entirely — not granted to
    # agent 05 — so even a medical-director session cannot issue it THROUGH the agent.
    res = gw._invoke(DIRECTOR, "payer.issue_determination", {"case_ref": "UM-1", "determination": "DENY"})
    assert res.decision == "DENY"
