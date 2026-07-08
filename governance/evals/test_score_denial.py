"""
CI gate for the Agent 01 scored eval (Revenue-Cycle & Denial) + negative controls.

The positive tests hold the quality line on the golden set. The negative controls
prove the gate has TEETH — that the scorers actually catch a denial-reason
misclassification, an ungrounded value in an appeal, and a PHI identifier — so a
green run means something. A completeness test proves the presence-not-truthiness
fix (a valid False/0.0 field must count as present).
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))
sys.path.insert(0, str(_HERE.parent.parent / "platform_core"))

from governance.evals.scorers_denial import (  # noqa: E402
    score_dataset, gate, predict, _completeness, THRESHOLDS, _PHI,
)
from governance.grounding import verify_grounding  # noqa: E402

GOLDEN = _HERE / "golden" / "agent01_denial_scored.json"


def _cases():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]


# ── positive: the benchmark passes every threshold ───────────────────────────

def test_scored_eval_meets_all_thresholds():
    result = score_dataset(_cases())
    passed, failures = gate(result["metrics"])
    assert passed, f"threshold failures: {failures}"


def test_phi_leak_hard_gate_is_zero():
    # Includes the two PHI-seeded cases — the masker must strip every identifier.
    result = score_dataset(_cases())
    assert result["metrics"]["phi_leak_rate"] == 0.0


def test_recoverable_recall_meets_money_bar():
    m = score_dataset(_cases())["metrics"]
    assert m["recoverable_recall"] >= THRESHOLDS["recoverable_recall"]


# ── negative controls: the gate must FAIL / flag on bad data ─────────────────

def test_gate_catches_a_reason_misclassification_and_missed_recoverable():
    # Poison a recoverable authorization denial so the record carries a code the
    # classifier maps to a write-off (CO-29 timely filing) while gold still says
    # recoverable authorization -> a wrong root cause AND a missed recoverable.
    cases = _cases()
    poisoned = json.loads(json.dumps(cases[0]))     # DN-0001, gold: authorization / recoverable
    poisoned["id"] = "DN-POISON"
    poisoned["denial"]["denial_codes"] = ["CO-29"]  # predict() -> timely_filing / write-off
    result = score_dataset([poisoned])
    passed, _ = gate(result["metrics"])
    assert result["metrics"]["denial_reason_accuracy"] < 1.0   # misclassified root cause
    assert result["metrics"]["recoverable_recall"] < 1.0       # missed a recoverable denial
    assert not passed                                          # the gate rejects it


def test_grounding_scorer_flags_an_ungrounded_value():
    # An appeal asserting a dollar amount absent from the case must be flagged.
    g = verify_grounding("We request payment of the billed 9999 for claim CLM-2026-0001.",
                         {"claim_id": "CLM-2026-0001", "billed": 312.00})
    assert g.ungrounded_numbers, "grounding scorer failed to flag an ungrounded number"


def test_phi_detector_catches_identifiers():
    assert _PHI.search("reporter jane.doe@example.com SSN 123-45-6789")
    assert not _PHI.search("Claim CLM-2026-0001 denied under CO-197 for service 99214.")


# ── completeness: presence, not truthiness (the fix) ─────────────────────────

def test_completeness_counts_false_and_zero_as_present():
    # A write-off artifact legitimately has recoverable=False and allowed_amount=0.0.
    # PRESENCE-based completeness must score it 1.0; a truthiness check would wrongly
    # drop those two fields (6/8 = 0.75) and fail the >=0.95 bar.
    art = {"claim_id": "CLM-1", "payer": "Aetna", "denial_code": "CO-27", "service": "99214",
           "appeal_letter": "…", "recommended_action": "WRITE_OFF",
           "recoverable": False, "allowed_amount": 0.0}
    assert _completeness(art) == 1.0
    truthy = sum(1 for k in ("claim_id", "payer", "denial_code", "service", "appeal_letter",
                             "recommended_action", "recoverable", "allowed_amount") if art.get(k))
    assert truthy < 8, "the truthiness trap should drop False/0.0 — presence must not"


def test_phi_seeded_cases_emit_no_identifiers():
    # Directly assert the two seeded cases produce masked, identifier-free output.
    seeded = [c for c in _cases() if c["gold"].get("phi_seeded")]
    assert len(seeded) >= 2
    for c in seeded:
        pred = predict(c)
        assert not _PHI.search(pred.emitted), f"PHI leaked from {c['id']}"
