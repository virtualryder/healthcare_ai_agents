import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "01-revenue-cycle-denial-agent")]

from agent.core import run_until_gate, resume
from agent.state import RecommendedAction

CLAIMS = {"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"}
APPROVAL = {"approved": True, "reviewer": {"sub": "mgr-1"}}


def test_auth_denial_is_appealable_and_grounded():
    s = run_until_gate({"claim_ref": "CLM-2026-55810", "acting_user_claims": CLAIMS})
    assert s["root_cause"] == "authorization" and s["appealable"]
    assert s["grounding_report"]["grounded"]
    assert s["citations"] and s["citations"][0]["url"]
    assert s["recommended_action"] == RecommendedAction.APPEAL
    assert s["_paused_at_gate"] is True


def test_appeal_submits_only_with_approval():
    s = run_until_gate({"claim_ref": "CLM-2026-55810", "acting_user_claims": CLAIMS})
    final = resume(s, APPROVAL)
    assert final["case_status"] == "APPEAL_SUBMITTED" and final["appeal_ref"]


def test_appeal_not_submitted_without_approval():
    s = run_until_gate({"claim_ref": "CLM-2026-55810", "acting_user_claims": CLAIMS})
    final = resume(s, approval=None)
    assert final.get("appeal_ref") is None
    assert final["case_status"] == "PENDING_REVIEW"


def test_coding_denial_routes_to_resubmit():
    s = run_until_gate({"claim_ref": "CLM-2026-55811", "denial_codes": ["CO-16"],
                        "acting_user_claims": CLAIMS})
    assert s["root_cause"] == "coding"
    assert s["recommended_action"] == RecommendedAction.CORRECT_AND_RESUBMIT
    final = resume(s, APPROVAL)
    assert final["case_status"] == "RESUBMIT_QUEUED"


def test_timely_filing_escalates():
    s = run_until_gate({"claim_ref": "CLM-2026-55812", "denial_codes": ["CO-29"],
                        "acting_user_claims": CLAIMS})
    assert s["root_cause"] == "timely_filing" and not s["appealable"]
    assert s["recommended_action"] == RecommendedAction.ESCALATE
