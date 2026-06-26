import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "06-payment-integrity-coding-agent")]

from tools import gateway_tools as gw

CLAIMS = {"sub": "coder-1", "custom:hpp_role": "CODING_SPECIALIST"}


def test_validate_codes_honors_ncci():
    assert gw.validate_codes(CLAIMS, ["99214"], ["E11.9"])["valid"] is True
    assert gw.validate_codes(CLAIMS, ["99214"], ["E11.9"], ncci=True)["ncci_edits"]


def test_necessity_honors_supported():
    assert gw.check_medical_necessity(CLAIMS, ["99214"], ["E11.9"], supported=True)["supported"] is True
    assert gw.check_medical_necessity(CLAIMS, ["99214"], ["Z00.00"], supported=False)["supported"] is False


def test_update_case_requires_approval():
    res = gw.update_case(CLAIMS, {"case_ref": "CASE-1", "status": "FLAG"})
    assert res.decision == "PENDING_APPROVAL"


def test_update_case_with_approval_allows():
    res = gw.update_case(CLAIMS, {"case_ref": "CASE-1", "status": "FLAG"},
                         approval={"approved": True, "reviewer": {"sub": "pi-1"}})
    assert res.decision == "ALLOW" and res.result["note_added"] is True


def test_agent_cannot_submit_claim():
    res = gw._invoke(CLAIMS, "clearinghouse.submit_claim", {"claim_ref": "CLM-1"})
    assert res.decision == "DENY"
