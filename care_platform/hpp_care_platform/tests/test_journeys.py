import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "care_platform")]

from hpp_care_platform.govern import GovernedActions
from hpp_care_platform.events import ComplianceEventBus
from hpp_care_platform import journeys
from hpp_care_platform.saga import Saga, Step, JourneySuspended
from hpp_care_platform.consent import ConsentLedger


def _gov():
    return GovernedActions(connector_mode="fixture")


def test_denial_journey_suspends_at_human_gate():
    bus = ComplianceEventBus()
    saga = journeys.denial_to_resolution(_gov(), bus)
    res = saga.run({"claim_ref": "CLM-2026-55810", "member_ref": "MBR-30551"})
    # the appeal step is a high-risk write -> suspends without an approval
    assert res.status == "SUSPENDED" and res.suspended_at == "appeal"
    assert "load" in res.completed and "validate" in res.completed
    assert bus.verify_chain()


def test_denial_journey_completes_with_approvals():
    bus = ComplianceEventBus()
    saga = journeys.denial_to_resolution(_gov(), bus)
    approvals = {"appeal": {"approved": True, "reviewer": {"sub": "mgr-1"}},
                 "notify": {"approved": True, "reviewer": {"sub": "lead-1"}}}
    res = saga.run({"claim_ref": "CLM-2026-55810", "member_ref": "MBR-30551", "approvals": approvals})
    assert res.status == "COMPLETED"
    assert res.completed == ["load", "validate", "appeal", "notify"]


def test_admission_journey_suspends_at_clinician_gate():
    res = journeys.admission_to_followup(_gov(), ComplianceEventBus()).run(
        {"subject_ref": "PT-40012", "encounter_ref": "ENC-88231"})
    assert res.status == "SUSPENDED" and res.suspended_at == "discharge"


def test_new_member_onboarding_completes_with_approval():
    approvals = {"register": {"approved": True, "reviewer": {"sub": "lead-1"}}}
    res = journeys.new_member_onboarding(_gov(), ComplianceEventBus()).run(
        {"member_ref": "MBR-30551", "subject_ref": "PT-40099", "approvals": approvals})
    assert res.status == "COMPLETED" and "care_gaps" in res.completed


def test_saga_compensates_on_failure():
    bus = ComplianceEventBus()
    state = {"undone": []}

    def ok(ctx): ctx.setdefault("did", []).append("a")
    def undo_a(ctx): state["undone"].append("a")
    def boom(ctx): raise RuntimeError("downstream system error")

    saga = Saga("t", [Step("a", "x", ok, compensate=undo_a), Step("b", "y", boom)], bus)
    res = saga.run({})
    assert res.status == "COMPENSATED" and res.failed_at == "b"
    assert state["undone"] == ["a"] and res.compensated == ["a"]
    assert bus.verify_chain()


def test_platform_never_widens_authority():
    # a journey step that calls a withheld tool is denied by the SAME gateway
    gov = _gov()
    r = gov.call(claims={"sub": "um-1", "custom:hpp_role": "UM_NURSE"},
                 agent_id="05-utilization-management", tool="payer.issue_determination",
                 args={"determination": "DENY"})
    assert r.decision == "DENY"


def test_consent_ledger_gates_sensitive_scope():
    led = ConsentLedger()
    # routine scope allowed without explicit grant; sensitive (Part 2) denied without grant
    assert led.permits(subject_ref="PT-1", scope="treatment_payment_operations")
    assert not led.permits(subject_ref="PT-1", scope="42cfr_part2")
    led.record(subject_ref="PT-1", scope="42cfr_part2", aal="AAL2", granted=True)
    assert led.permits(subject_ref="PT-1", scope="42cfr_part2", aal="AAL2")
    assert not led.permits(subject_ref="PT-1", scope="42cfr_part2", aal="AAL1")  # assurance gate
