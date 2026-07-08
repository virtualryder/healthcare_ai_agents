"""
Scored eval metrics for Agent 01 (Revenue-Cycle & Denial) — scored benchmark.

Where run_evals.py answers "does the artifact keep its required shape?" (binary,
structural regression), this module answers "how GOOD is the agent, on a labeled
denial benchmark, against thresholds a VP of Revenue Cycle / Compliance would set?"

Predictions come from the REAL Agent 01 deterministic classifier
(01-revenue-cycle-denial-agent/agent/nodes.analyze_denial) — the same CARC ->
root-cause / appealability logic the workflow runs — so this scores the actual
classification, not a stub. Entity extraction reads the claim/remittance record;
the grounded appeal draft is scored with governance/grounding.py; PHI-leak reuses
the platform masker (hpp_agent_platform.phi.mask).

HONESTY NOTE: there is no clean public, PHI-free denial API. Real denial data is
the customer's X12 835/277 remittance (via a clearinghouse) or AWS HealthLake
Claim/ClaimResponse (FHIR) under a BAA. The benchmark therefore runs on LABELED
SYNTHETIC denials (gen_golden_denial.py); the connector scaffold documents the
real engagement-owned source (connectors/denials.py).

Metrics (aggregated over the golden set), with regulatory-weighted thresholds:
  denial_reason_accuracy  >= 0.90   (CARC/RARC-family root-cause classification)
  recoverable_recall      >= 0.95   (missing a RECOVERABLE denial is the money harm
                                     — a wrongful write-off; recall weighted highest)
  entity_f1               >= 0.85   (claim_id / payer / denial_code / service)
  grounding_rate          >= 0.90   (appeal-draft claims traceable to the case)
  phi_leak_rate           == 0.00   (HARD GATE — any unmasked identifier fails)
  appeal_completeness     >= 0.95   (required appeal fields present)
  duplicate_accuracy      >= 0.90   (duplicate-vs-near-miss discrimination)
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "platform_core"))

from governance.grounding import verify_grounding   # noqa: E402
from hpp_agent_platform.phi import mask              # noqa: E402

# Score the REAL Agent 01 denial classifier (deterministic CARC -> root-cause /
# appealability), not just a stub. Path-guarded so the eval still runs if the
# agent package layout changes — falls back to the mirrored map below.
_AGENT = _REPO / "01-revenue-cycle-denial-agent"
sys.path.insert(0, str(_AGENT))
try:
    from agent.nodes import analyze_denial as _agent_analyze  # noqa: E402
except Exception:  # pragma: no cover
    _agent_analyze = None

# Fallback mirror of the agent's CARC map (used only if the real import fails).
_CARC_FALLBACK: Dict[str, Tuple[str, bool]] = {
    "CO-197": ("authorization", True), "CO-50": ("medical_necessity", True),
    "CO-16": ("coding", True), "CO-11": ("coding", True),
    "CO-27": ("eligibility", False), "CO-29": ("timely_filing", False),
}

THRESHOLDS: Dict[str, float] = {
    "denial_reason_accuracy": 0.90,
    "recoverable_recall": 0.95,     # weighted highest — a missed recoverable is a write-off
    "entity_f1": 0.85,
    "grounding_rate": 0.90,
    "phi_leak_rate": 0.0,           # <= (hard gate: must be exactly 0)
    "appeal_completeness": 0.95,
    "duplicate_accuracy": 0.90,
}
# Direction: most metrics are "higher is better" (>=); phi_leak_rate is "<=".
LOWER_IS_BETTER = {"phi_leak_rate"}

# Required fields for a complete appeal artifact. Note: allowed_amount=0.0 and
# recoverable=False are VALID present values, so completeness tests PRESENCE
# (not None/""/[]/{}), NOT truthiness — a False/0 must count as present.
_APPEAL_REQUIRED = ["claim_id", "payer", "denial_code", "service",
                    "appeal_letter", "recommended_action", "recoverable", "allowed_amount"]

# Conservative PHI-leak detector for the two highest-signal identifiers (SSN,
# email). If either survives masking, the emitted artifact leaked PHI.
_PHI = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|[\w.+-]+@[\w-]+\.[\w.]+")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def _classify(codes: List[str]) -> Tuple[str, bool]:
    """Run the real Agent 01 classifier; fall back to the mirrored map."""
    if _agent_analyze is not None:
        try:
            out = _agent_analyze({"denial_codes": list(codes)})
            return str(out["root_cause"]), bool(out["appealable"])
        except Exception:  # pragma: no cover
            pass
    root, appealable = "other", True
    for c in codes:
        if c in _CARC_FALLBACK:
            root, appealable = _CARC_FALLBACK[c]
            break
    return root, appealable


def _compose_appeal(claim_id: str, payer: str, denial_code: str, service: str) -> str:
    """
    Compose a factual, grounded appeal draft from ONLY the case's structured
    fields (this is also what the grounding eval scores against). Deliberately
    claims nothing the record does not contain.
    """
    return (f"Re: Claim {claim_id} denied by {payer} under {denial_code} for service {service}. "
            f"Per the payer's published coverage policy, we respectfully request reprocessing and "
            f"payment. This appeal is prepared for a denials specialist's review; no submission is "
            f"made without human approval.")


@dataclass
class CasePrediction:
    case_id: str
    root_cause: str
    recoverable: bool
    entities: Set[str]
    appeal_letter: str
    emitted: str
    artifact: Dict[str, Any]
    record: Dict[str, Any]


def predict(case: Dict[str, Any]) -> CasePrediction:
    """
    Produce the agent's prediction for a denial case:
      * root-cause + recoverability -> the REAL Agent 01 classifier (analyze_denial)
      * entity extraction           -> read the claim/remittance record fields
      * appeal draft                -> grounded compose from structured fields
      * emitted text                -> masked (letter + any free-text note)
    """
    rec = case["denial"]
    codes = rec.get("denial_codes", []) or []
    root_cause, recoverable = _classify(codes)

    claim_id = rec.get("claim_id", "")
    payer = rec.get("payer", "")
    denial_code = codes[0] if codes else ""
    service = rec.get("service", "")

    entities = {f"claim_id:{_norm(claim_id)}", f"payer:{_norm(payer)}",
                f"denial_code:{_norm(denial_code)}", f"service:{_norm(service)}"}

    letter = _compose_appeal(claim_id, payer, denial_code, service)

    # PHI control: mask the emitted artifact (letter + any free-text note). Even
    # though the composed letter is PHI-free, a real note may carry identifiers —
    # the masker runs at the emit/audit boundary and must strip them.
    note = rec.get("raw_note", "")
    emitted = mask((letter + " " + note).strip())

    if not recoverable:
        action = "WRITE_OFF"
    elif root_cause == "coding":
        action = "CORRECT_AND_RESUBMIT"
    else:
        action = "APPEAL"

    artifact = {
        "claim_id": claim_id, "payer": payer, "denial_code": denial_code, "service": service,
        "appeal_letter": letter,
        "recommended_action": action,
        "recoverable": recoverable,          # may be False (write-off) — present, not truthy
        "allowed_amount": rec.get("allowed", 0.0),  # may be 0.0 — present, not truthy
    }
    return CasePrediction(case_id=case["id"], root_cause=root_cause, recoverable=recoverable,
                          entities=entities, appeal_letter=letter, emitted=emitted,
                          artifact=artifact, record=rec)


# ── metric helpers ────────────────────────────────────────────────────────────

def _prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 1.0
    r = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1


def _completeness(artifact: Dict[str, Any]) -> float:
    """
    Fraction of required fields present. PRESENCE, not truthiness: a valid
    False / 0 / 0.0 value counts as present — only None/""/[]/{} are "missing".
    """
    present = sum(1 for f in _APPEAL_REQUIRED if artifact.get(f) not in (None, "", [], {}))
    return present / len(_APPEAL_REQUIRED)


def score_dataset(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    cases: list of {"id", "denial": {...}, "gold": {claim_id, payer, denial_code,
           service, root_cause, recoverable, is_duplicate?, dup_of?}}.
    Returns metrics + per-case detail + confusion.
    """
    reason_correct = 0
    r_tp = r_fp = r_fn = r_tn = 0          # recoverable confusion (positive = recoverable)
    e_tp = e_fp = e_fn = 0                 # entity micro-F1 accumulators
    grounded = 0
    phi_leaks = 0
    completeness_scores: List[float] = []
    detail: List[Dict[str, Any]] = []

    preds: Dict[str, CasePrediction] = {}
    for c in cases:
        pred = predict(c)
        preds[c["id"]] = pred
        gold = c["gold"]

        # denial-reason (root-cause) classification accuracy
        if pred.root_cause == gold["root_cause"]:
            reason_correct += 1

        # recoverable vs write-off (recall weighted highest downstream)
        gr, prc = bool(gold["recoverable"]), bool(pred.recoverable)
        if gr and prc: r_tp += 1
        elif gr and not prc: r_fn += 1
        elif not gr and prc: r_fp += 1
        else: r_tn += 1

        # entities (claim_id/payer/denial_code/service micro-set)
        gold_ents = {f"claim_id:{_norm(gold['claim_id'])}", f"payer:{_norm(gold['payer'])}",
                     f"denial_code:{_norm(gold['denial_code'])}", f"service:{_norm(gold['service'])}"}
        e_tp += len(gold_ents & pred.entities)
        e_fp += len(pred.entities - gold_ents)
        e_fn += len(gold_ents - pred.entities)

        # grounding on the appeal draft (against the claim/remittance record)
        g = verify_grounding(pred.appeal_letter, pred.record)
        is_grounded = not (g.ungrounded_numbers or g.ungrounded_entities)
        grounded += 1 if is_grounded else 0

        # PHI-leak: the emitted (masked) artifact must carry no identifier
        leaked = bool(_PHI.search(pred.emitted))
        phi_leaks += 1 if leaked else 0

        completeness_scores.append(_completeness(pred.artifact))

        detail.append({"id": c["id"], "reason_gold": gold["root_cause"], "reason_pred": pred.root_cause,
                       "recoverable_gold": gr, "recoverable_pred": prc,
                       "grounded": is_grounded, "phi_leak": leaked})

    # duplicate detection: gold cases carry is_duplicate + dup_of. Predict a
    # duplicate when the case and its referenced pair share payer + denial code +
    # service (a resubmitted/duplicated denial), which the near-miss (different
    # code) must NOT trigger.
    dup_correct = dup_total = 0
    for c in cases:
        if "is_duplicate" not in c["gold"]:
            continue
        dup_total += 1
        gold_dup = bool(c["gold"]["is_duplicate"])
        ref = c["gold"].get("dup_of")
        pred_dup = False
        if ref and ref in preds:
            a, b = preds[c["id"]].record, preds[ref].record
            pred_dup = bool(a.get("payer") == b.get("payer")
                            and set(a.get("denial_codes", [])) & set(b.get("denial_codes", []))
                            and a.get("service") == b.get("service"))
        if pred_dup == gold_dup:
            dup_correct += 1

    _, r_recall, _ = _prf(r_tp, r_fp, r_fn)
    _, _, e_f1 = _prf(e_tp, e_fp, e_fn)
    n = len(cases)
    metrics = {
        "denial_reason_accuracy": round(reason_correct / n, 4) if n else 1.0,
        "recoverable_recall": round(r_recall, 4),
        "entity_f1": round(e_f1, 4),
        "grounding_rate": round(grounded / n, 4) if n else 1.0,
        "phi_leak_rate": round(phi_leaks / n, 4) if n else 0.0,
        "appeal_completeness": round(sum(completeness_scores) / n, 4) if n else 1.0,
        "duplicate_accuracy": round(dup_correct / dup_total, 4) if dup_total else 1.0,
    }
    return {"metrics": metrics, "n_cases": n, "detail": detail,
            "confusion": {"recoverable": {"tp": r_tp, "fp": r_fp, "fn": r_fn, "tn": r_tn}},
            "classifier": "agent.nodes.analyze_denial" if _agent_analyze is not None else "fallback-map"}


def gate(metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
    """Return (passed, failures) against THRESHOLDS."""
    failures: List[str] = []
    for name, thr in THRESHOLDS.items():
        val = metrics.get(name, 0.0)
        if name in LOWER_IS_BETTER:
            if val > thr:
                failures.append(f"{name}={val} exceeds max {thr}")
        elif val < thr:
            failures.append(f"{name}={val} below min {thr}")
    return (not failures), failures
