"""
Scored eval runner for Agent 01 (Revenue-Cycle & Denial).

Loads the labeled golden denial set, runs the REAL Agent 01 classifier to produce
predictions, scores the regulatory-weighted metrics, gates against thresholds, and
writes an evidence report (eval-report-denial.md + eval-report-denial.json). Exit
code is non-zero if any threshold is missed — so CI holds the quality line.

    python -m governance.evals.score_denial
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))
sys.path.insert(0, str(_HERE.parent.parent / "platform_core"))

from governance.evals.scorers_denial import (  # noqa: E402
    score_dataset, gate, THRESHOLDS, LOWER_IS_BETTER,
)

GOLDEN = _HERE / "golden" / "agent01_denial_scored.json"
REPORT_MD = _HERE / "eval-report-denial.md"
REPORT_JSON = _HERE / "eval-report-denial.json"


def _load():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]


def build_report(result, passed, failures) -> str:
    m = result["metrics"]
    rows = []
    for name, thr in THRESHOLDS.items():
        val = m.get(name, 0.0)
        op = "<=" if name in LOWER_IS_BETTER else ">="
        ok = (val <= thr) if name in LOWER_IS_BETTER else (val >= thr)
        rows.append(f"| {name} | {val} | {op} {thr} | {'PASS' if ok else 'FAIL'} |")
    conf = result["confusion"]["recoverable"]
    md = [
        "# Agent 01 (Revenue-Cycle & Denial) — scored eval report",
        "",
        f"**Result:** {'PASS' if passed else 'FAIL'} · **Cases:** {result['n_cases']} · "
        f"Predictions from the REAL Agent 01 classifier (`{result['classifier']}`); "
        "appeal-draft grounding via `governance/grounding.py`; PHI-leak via the platform masker.",
        "",
        "Benchmark runs on **labeled synthetic denials** — there is no clean public, PHI-free "
        "denial API. The real source is the customer's **X12 835/277** remittance (clearinghouse) "
        "or **AWS HealthLake Claim/ClaimResponse (FHIR)** under a BAA; see the connector scaffold "
        "`platform_core/hpp_agent_platform/connectors/denials.py`.",
        "",
        "| Metric | Value | Threshold | Status |",
        "|---|---|---|---|",
        *rows,
        "",
        f"**Recoverable confusion:** TP={conf['tp']} FP={conf['fp']} FN={conf['fn']} TN={conf['tn']} "
        "(recall is weighted highest — missing a recoverable denial is a wrongful write-off, the money harm).",
        "",
        "This report is the quality-evidence artifact for the assurance packet: it shows the agent's "
        "denial classification measured against a labeled benchmark with a **PHI-leak hard gate (= 0)**. "
        "Human retains claim submission. Regenerate with `python -m governance.evals.score_denial`.",
    ]
    if failures:
        md += ["", "## Threshold failures", *[f"- {f}" for f in failures]]
    return "\n".join(md) + "\n"


def main() -> int:
    cases = _load()
    result = score_dataset(cases)
    passed, failures = gate(result["metrics"])
    REPORT_JSON.write_text(json.dumps({"passed": passed, **result, "failures": failures}, indent=2), encoding="utf-8")
    REPORT_MD.write_text(build_report(result, passed, failures), encoding="utf-8")
    print(f"Agent 01 scored eval — {'PASS' if passed else 'FAIL'} ({result['n_cases']} cases)")
    for k, v in result["metrics"].items():
        print(f"  {k:24s} {v}")
    for f in failures:
        print("  FAIL:", f)
    print(f"report -> {REPORT_MD}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
