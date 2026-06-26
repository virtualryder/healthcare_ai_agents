import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "02-prior-authorization-agent")]

from tools import gateway_tools as gw

CLAIMS = {"sub": "pa-1", "custom:hpp_role": "PA_COORDINATOR"}


def test_check_requirement_reads():
    assert gw.check_pa_requirement(CLAIMS, "72148")["pa_required"] is True
    assert gw.check_pa_requirement(CLAIMS, "99214")["pa_required"] is False


def test_evaluate_criteria_reads():
    assert gw.evaluate_criteria(CLAIMS, "72148")["meets_criteria"] is True


def test_submit_pa_requires_approval():
    res = gw.submit_pa(CLAIMS, {"service": "72148"})
    assert res.decision == "PENDING_APPROVAL"


def test_submit_pa_with_approval_allows():
    res = gw.submit_pa(CLAIMS, {"service": "72148"},
                       approval={"approved": True, "reviewer": {"sub": "nurse-1"}})
    assert res.decision == "ALLOW" and res.result["pa_ref"]


def test_agent_cannot_issue_determination():
    res = gw._invoke(CLAIMS, "payer.issue_determination", {"determination": "APPROVE"})
    assert res.decision == "DENY"
