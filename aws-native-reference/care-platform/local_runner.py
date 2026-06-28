"""Run the Care & Claims Orchestration journeys end-to-end (no API key).

Demonstrates: a journey that SUSPENDS at the human gate; the same journey COMPLETING
with bound approvals; and a saga COMPENSATING on a downstream failure — every step
emitting a hash-chained compliance event. The AWS-native form is a Step Functions
state machine (compensation = Catch->compensate; human gate = waitForTaskToken)."""
from __future__ import annotations
import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "care_platform")]

from hpp_care_platform.govern import GovernedActions          # noqa: E402
from hpp_care_platform.events import ComplianceEventBus       # noqa: E402
from hpp_care_platform import journeys                        # noqa: E402
from hpp_care_platform.saga import Saga, Step                 # noqa: E402


def main() -> None:
    gov = GovernedActions(connector_mode="fixture")

    print("=== denial_to_resolution — no approvals (suspends at human gate) ===")
    bus = ComplianceEventBus()
    r = journeys.denial_to_resolution(gov, bus).run({"claim_ref": "CLM-2026-55810", "member_ref": "MBR-30551"})
    print(f"  status={r.status} suspended_at={r.suspended_at} completed={r.completed} chain_ok={bus.verify_chain()}")

    print("\n=== denial_to_resolution — with approvals (completes) ===")
    bus = ComplianceEventBus()
    appr = {"appeal": {"approved": True, "reviewer": {"sub": "mgr-1"}},
            "notify": {"approved": True, "reviewer": {"sub": "lead-1"}}}
    r = journeys.denial_to_resolution(gov, bus).run({"claim_ref": "CLM-2026-55810", "member_ref": "MBR-30551", "approvals": appr})
    print(f"  status={r.status} completed={r.completed} events={len(bus.events)} chain_ok={bus.verify_chain()}")

    print("\n=== admission_to_followup — full approvals (completes) ===")
    appr = {k: {"approved": True, "reviewer": {"sub": "rev-" + k}} for k in ("discharge", "care_plan", "followup")}
    r = journeys.admission_to_followup(gov, ComplianceEventBus()).run(
        {"subject_ref": "PT-40012", "encounter_ref": "ENC-88231", "approvals": appr})
    print(f"  status={r.status} completed={r.completed}")

    print("\n=== saga compensation demo (downstream failure rolls back) ===")
    bus = ComplianceEventBus()
    undone = []
    saga = Saga("compensation_demo", [
        Step("reserve_slot", "04-patient-access", lambda c: None, compensate=lambda c: undone.append("slot")),
        Step("downstream", "x", lambda c: (_ for _ in ()).throw(RuntimeError("payer timeout"))),
    ], bus)
    r = saga.run({})
    print(f"  status={r.status} failed_at={r.failed_at} compensated={r.compensated} undone={undone}")


if __name__ == "__main__":
    main()
