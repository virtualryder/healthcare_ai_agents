import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "08-contact-center-member-services-agent")]

from tools import gateway_tools as gw

CLAIMS = {"sub": "msr-1", "custom:hpp_role": "MEMBER_SERVICES_REP"}


def test_reads_member_and_status():
    assert gw.get_member(CLAIMS, "MBR-30551")["plan"]
    assert gw.check_claim_status(CLAIMS, "CLM-2026-55810")["status"] == "Denied"
    assert gw.check_eligibility(CLAIMS, "MBR-INACTIVE")["active"] is False


def test_log_interaction_requires_approval():
    res = gw.log_interaction(CLAIMS, {"channel": "voice", "member_ref": "MBR-30551"})
    assert res.decision == "PENDING_APPROVAL"


def test_create_grievance_requires_approval():
    res = gw.create_grievance(CLAIMS, {"category": "Member grievance", "member_ref": "MBR-30551"})
    assert res.decision == "PENDING_APPROVAL"


def test_create_grievance_with_approval_allows():
    res = gw.create_grievance(CLAIMS, {"category": "Member grievance", "member_ref": "MBR-30551"},
                              approval={"approved": True, "reviewer": {"sub": "lead-1"}})
    assert res.decision == "ALLOW" and res.result["grievance_id"]


def test_agent_cannot_submit_appeal():
    res = gw._invoke(CLAIMS, "payer.submit_appeal", {"claim_ref": "CLM-1"})
    assert res.decision == "DENY"
