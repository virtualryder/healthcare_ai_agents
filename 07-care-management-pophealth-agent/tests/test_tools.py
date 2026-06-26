import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "07-care-management-pophealth-agent")]

from tools import gateway_tools as gw

CLAIMS = {"sub": "care-mgr-1", "custom:hpp_role": "CARE_MANAGER"}


def test_identify_gaps_honors_no_gaps():
    assert gw.identify_gaps(CLAIMS, "PT-40012")["open_gaps"]
    assert gw.identify_gaps(CLAIMS, "PT-40012", no_gaps=True)["open_gaps"] == []


def test_consent_honors_part2():
    assert gw.check_consent(CLAIMS, "PT-40012", "care_management", part2_sensitive=False)["granted"] is True
    assert gw.check_consent(CLAIMS, "PT-40012", "care_management", part2_sensitive=True)["granted"] is False


def test_update_care_plan_requires_approval():
    res = gw.update_care_plan(CLAIMS, {"patient_ref": "PT-40012"})
    assert res.decision == "PENDING_APPROVAL"


def test_update_care_plan_with_approval_allows():
    res = gw.update_care_plan(CLAIMS, {"patient_ref": "PT-40012"},
                              approval={"approved": True, "reviewer": {"sub": "lead-1"}})
    assert res.decision == "ALLOW" and res.result["requires_care_manager_signoff"] is True


def test_agent_cannot_issue_determination():
    res = gw._invoke(CLAIMS, "payer.issue_determination", {"determination": "DENY"})
    assert res.decision == "DENY"
