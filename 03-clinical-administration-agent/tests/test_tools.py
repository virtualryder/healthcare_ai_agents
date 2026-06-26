import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "03-clinical-administration-agent")]

from tools import gateway_tools as gw

CLAIMS = {"sub": "ma-1", "custom:hpp_role": "CLINICAL_STAFF"}


def test_reads_chart():
    assert gw.get_patient_summary(CLAIMS, "PT-40012")["active_problems"]
    assert gw.get_care_plan(CLAIMS, "PT-40012")["goals"]


def test_consent_honors_part2():
    assert gw.check_consent(CLAIMS, "PT-40012", "clinical_admin", part2_sensitive=False)["granted"] is True
    assert gw.check_consent(CLAIMS, "PT-40012", "clinical_admin", part2_sensitive=True)["granted"] is False


def test_draft_note_requires_approval():
    res = gw.draft_note(CLAIMS, {"encounter_ref": "ENC-88231"})
    assert res.decision == "PENDING_APPROVAL"


def test_draft_note_with_approval_allows():
    res = gw.draft_note(CLAIMS, {"encounter_ref": "ENC-88231"},
                        approval={"approved": True, "reviewer": {"sub": "clinician-1"}})
    assert res.decision == "ALLOW" and res.result["requires_clinician_signoff"] is True


def test_agent_cannot_order_or_submit_claim():
    res = gw._invoke(CLAIMS, "clearinghouse.submit_claim", {"claim_ref": "CLM-1"})
    assert res.decision == "DENY"
