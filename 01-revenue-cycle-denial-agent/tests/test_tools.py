import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "01-revenue-cycle-denial-agent")]

from tools import gateway_tools as gw

CLAIMS = {"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"}


def test_get_claim_reads():
    assert gw.get_claim(CLAIMS, "CLM-2026-55810")["status"] == "Denied"


def test_validate_claim_reads_edits():
    assert gw.validate_claim(CLAIMS, "CLM-2026-55810")["edits"]


def test_submit_appeal_requires_approval():
    res = gw.submit_appeal(CLAIMS, {"claim_ref": "CLM-2026-55810", "level": 1})
    assert res.decision == "PENDING_APPROVAL"


def test_submit_appeal_with_approval_allows():
    res = gw.submit_appeal(CLAIMS, {"claim_ref": "CLM-2026-55810", "level": 1},
                           approval={"approved": True, "reviewer": {"sub": "mgr-1"}})
    assert res.decision == "ALLOW" and res.result["appeal_ref"]


def test_agent_cannot_submit_claim():
    # Even a manager's session: the agent is not granted claim submission.
    mgr = {"sub": "m", "custom:hpp_role": "DENIALS_MANAGER"}
    res = gw._invoke(mgr, "clearinghouse.submit_claim", {"claim_ref": "CLM-1"})
    assert res.decision == "DENY"
