"""
Reproducible generator for the Agent 01 scored golden set (Revenue-Cycle Denial).

Produces governance/evals/golden/agent01_denial_scored.json: labeled synthetic
denial cases (claim/remittance-shaped records + gold labels) covering:

  * varied CARC/RARC-family reasons (authorization, medical necessity, coding,
    eligibility, timely filing, and an unmapped "other"),
  * recoverable denials (appeal / correct-and-resubmit) AND write-offs
    (eligibility terminated, timely-filing lapsed),
  * a duplicate pair (same payer + denial code + service, different claim id) and
    a near-miss (same payer + service, DIFFERENT denial code -> NOT a duplicate),
  * two cases seeded with PHI in a free-text note, to prove the platform masker
    strips identifiers before anything is emitted/audited.

Gold labels are the ground truth the scorers assert against; the REAL Agent 01
deterministic denial classifier (agent/nodes.analyze_denial) is the prediction.
The synthetic cases here are the single source of truth: the denials connector
scaffold reuses them in fixture mode (see connectors/denials.py).

    python -m governance.evals.gen_golden_denial
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

OUT = Path(__file__).resolve().parent / "golden" / "agent01_denial_scored.json"

# CARC (Claim Adjustment Reason Code) -> (root-cause category, recoverable?).
# Ground truth a denials specialist would confirm from the remittance (X12 835).
# Mirrors — but is INDEPENDENT of — the agent's own classifier map; the eval
# scores the agent's prediction against THIS gold.
_CARC_GOLD = {
    "CO-197": ("authorization", True),     # precert/authorization absent -> appeal
    "CO-50":  ("medical_necessity", True), # not deemed medically necessary -> appeal
    "CO-16":  ("coding", True),            # claim/service lacks information -> correct+resubmit
    "CO-11":  ("coding", True),            # dx inconsistent with procedure -> correct+resubmit
    "CO-27":  ("eligibility", False),      # expired/terminated coverage -> write-off
    "CO-29":  ("timely_filing", False),    # filing limit expired -> write-off
    # CO-45 (charge exceeds fee schedule) is intentionally NOT in the agent map:
    # it falls through to ("other", True) = route to a specialist for review.
}

# RARC-family remark codes carried alongside the CARC for realism (not graded).
_REMARK = {
    "CO-197": "N20", "CO-50": "M25", "CO-16": "MA130", "CO-11": "M51",
    "CO-27": "N30", "CO-29": "N211", "CO-45": "M137",
}

# Two PHI-seeded free-text notes (Safe-Harbor identifiers the masker must strip:
# SSN, email, MRN, DOB, phone, street address, account/claim number).
_PHI_NOTE_1 = ("Member Jane Doe, SSN 123-45-6789, reached at jane.doe@example.com "
               "regarding MRN MRN-5561230; DOB 1957-03-14.")
_PHI_NOTE_2 = ("Contact John Smith at 415-555-0199, 742 Evergreen Terrace, Springfield; "
               "prior account CLM-2026-0777.")


def _case(cid: str, claim_id: str, payer: str, carc: str, service: str,
          cpt: List[str], icd10: List[str], billed: float, allowed: float,
          note: str = "", **extra_gold: Any) -> Dict[str, Any]:
    root_cause, recoverable = _CARC_GOLD.get(carc, ("other", True))
    denial: Dict[str, Any] = {
        "claim_id": claim_id,
        "payer": payer,
        "denial_codes": [carc],
        "remark_codes": [_REMARK[carc]] if carc in _REMARK else [],
        "service": service,
        "cpt": list(cpt),
        "icd10": list(icd10),
        "billed": billed,
        "allowed": allowed,          # 0.0 on a full denial — a VALID present value
        "service_date": "2026-06-12",
    }
    if note:
        denial["raw_note"] = note
    gold: Dict[str, Any] = {
        "claim_id": claim_id, "payer": payer, "denial_code": carc, "service": service,
        "root_cause": root_cause, "recoverable": recoverable,
    }
    gold.update(extra_gold)
    return {"id": cid, "denial": denial, "gold": gold}


def build_cases() -> List[Dict[str, Any]]:
    """Deterministic, reproducible construction of the labeled denial set."""
    cases: List[Dict[str, Any]] = [
        # ── recoverable: authorization (appeal) ──────────────────────────────
        _case("DN-0001", "CLM-2026-0001", "BlueChoice PPO", "CO-197", "99214", ["99214"], ["E11.9", "I10"], 312.00, 0.0),
        _case("DN-0002", "CLM-2026-0002", "Aetna",          "CO-197", "72148", ["72148"], ["M54.16"],        980.00, 0.0),
        # ── recoverable: medical necessity (appeal) ──────────────────────────
        _case("DN-0003", "CLM-2026-0003", "UnitedHealthcare", "CO-50", "70553", ["70553"], ["G43.909"], 1420.00, 0.0),
        _case("DN-0004", "CLM-2026-0004", "Cigna",            "CO-50", "93000", ["93000"], ["R00.2"],   210.00, 0.0),
        # ── recoverable: coding (correct + resubmit) ─────────────────────────
        _case("DN-0005", "CLM-2026-0005", "BlueChoice PPO", "CO-16", "99213", ["99213"], ["E11.9"],  188.00, 0.0),
        _case("DN-0006", "CLM-2026-0006", "Humana",         "CO-16", "80053", ["80053"], ["E78.5"],  64.00,  0.0),
        _case("DN-0007", "CLM-2026-0007", "Medicare",       "CO-11", "99215", ["99215"], ["I48.91"], 402.00, 0.0),
        _case("DN-0008", "CLM-2026-0008", "Aetna",          "CO-11", "20610", ["20610"], ["M17.11"], 275.00, 0.0),
        # ── duplicate pair (same payer + denial code + service) ──────────────
        _case("DN-0009", "CLM-2026-0009", "Medicaid", "CO-197", "99204", ["99204"], ["E11.9"], 350.00, 0.0),
        _case("DN-0010", "CLM-2026-0010", "Medicaid", "CO-197", "99204", ["99204"], ["E11.9"], 350.00, 0.0,
              is_duplicate=True, dup_of="DN-0009"),
        # ── write-offs: eligibility terminated ───────────────────────────────
        _case("DN-0011", "CLM-2026-0011", "BlueChoice PPO", "CO-27", "99214", ["99214"], ["I10"],    312.00, 0.0),
        _case("DN-0012", "CLM-2026-0012", "Aetna",          "CO-27", "99213", ["99213"], ["E11.9"],  188.00, 0.0),
        _case("DN-0013", "CLM-2026-0013", "Medicare",       "CO-27", "93000", ["93000"], ["R00.2"],  210.00, 0.0),
        # ── write-offs: timely filing lapsed ─────────────────────────────────
        _case("DN-0014", "CLM-2026-0014", "Humana", "CO-29", "99214", ["99214"], ["E11.9"], 312.00, 0.0),
        _case("DN-0015", "CLM-2026-0015", "Cigna",  "CO-29", "80053", ["80053"], ["E78.5"], 64.00,  0.0),
        # ── other / unmapped -> route to specialist (needs-review, recoverable) ─
        _case("DN-0016", "CLM-2026-0016", "UnitedHealthcare", "CO-45", "99214", ["99214"], ["E11.9"], 312.00, 142.00),
        # ── near-miss: same payer + service as DN-0009 but DIFFERENT code -> NOT a dup ─
        _case("DN-0017", "CLM-2026-0017", "Medicaid", "CO-50", "99204", ["99204"], ["E11.9"], 350.00, 0.0,
              is_duplicate=False, dup_of="DN-0009"),
        # ── one more recoverable coding case ─────────────────────────────────
        _case("DN-0018", "CLM-2026-0018", "Cigna", "CO-16", "71046", ["71046"], ["J18.9"], 156.00, 0.0),
        # ── PHI-seeded cases (recoverable) — prove the masker strips identifiers ─
        _case("DN-0019", "CLM-2026-0019", "BlueChoice PPO", "CO-197", "99214", ["99214"], ["E11.9"], 312.00, 0.0,
              note=_PHI_NOTE_1, phi_seeded=True),
        _case("DN-0020", "CLM-2026-0020", "Aetna", "CO-50", "70553", ["70553"], ["G43.909"], 1420.00, 0.0,
              note=_PHI_NOTE_2, phi_seeded=True),
    ]
    return cases


def main() -> None:
    cases = build_cases()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"cases": cases}, indent=2), encoding="utf-8")
    print(f"wrote {len(cases)} cases -> {OUT}")


if __name__ == "__main__":
    main()
