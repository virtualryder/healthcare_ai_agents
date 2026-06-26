import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "04-patient-access-agent")]

from tools import gateway_tools as gw

CLAIMS = {"sub": "access-1", "custom:hpp_role": "PATIENT_ACCESS_REP"}


def test_eligibility_and_estimate_read():
    assert gw.check_eligibility(CLAIMS, "MBR-30551")["active"] is True
    assert gw.check_eligibility(CLAIMS, "MBR-INACTIVE")["active"] is False
    assert gw.estimate_cost(CLAIMS, "99214")["basis"].startswith("Good Faith Estimate")


def test_book_appointment_requires_approval():
    res = gw.book_appointment(CLAIMS, {"service": "99214", "slot": "2026-06-29T09:00"})
    assert res.decision == "PENDING_APPROVAL"


def test_book_appointment_with_approval_allows():
    res = gw.book_appointment(CLAIMS, {"service": "99214", "slot": "2026-06-29T09:00"},
                              approval={"approved": True, "reviewer": {"sub": "lead-1"}})
    assert res.decision == "ALLOW" and res.result["appointment_ref"]


def test_create_registration_requires_approval():
    res = gw.create_registration(CLAIMS, {"patient_ref": "PT-40012"})
    assert res.decision == "PENDING_APPROVAL"


def test_agent_cannot_submit_pa():
    res = gw._invoke(CLAIMS, "payer.submit_pa", {"service": "72148"})
    assert res.decision == "DENY"
