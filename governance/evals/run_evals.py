"""
Structural eval harness. Validates that key artifacts keep their required shape —
the anatomy a reviewer and an auditor depend on. No API key, no network.

Two families live under governance/evals/:
  * STRUCTURAL (here)  — the golden_artifacts anatomy checks below, plus any
    golden/*.json file whose stem is registered in EVALUATORS.
  * SCORED (separate runners) — labeled benchmarks with regulatory thresholds,
    e.g. golden/agent01_denial_scored.json -> score_denial.py. These are handled
    by their own runners, so this harness SKIPS any golden file whose stem is not
    in EVALUATORS (rather than choking on an unexpected schema).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from .golden_artifacts import DENIAL_APPEAL, PRIOR_AUTH_PACKET

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

# Structural evaluators keyed by golden-file stem. Scored golden sets
# (e.g. "agent01_denial_scored") are intentionally absent — they have dedicated
# threshold-gating runners (score_denial.py) and MUST be skipped here.
EVALUATORS: Dict[str, Callable[[Dict], Tuple[bool, str]]] = {}


def _denial_appeal_ok(a: Dict) -> Tuple[bool, str]:
    if not a.get("appeal_letter"):
        return False, "missing appeal letter"
    if not a.get("citations"):
        return False, "appeal must cite payer/coverage policy"
    for c in a["citations"]:
        if not c.get("url"):
            return False, "every citation needs a URL"
    if a.get("submitted") is not False:
        return False, "agent artifact must not be auto-submitted (human gate)"
    return True, "ok"


def _prior_auth_ok(p: Dict) -> Tuple[bool, str]:
    if not p.get("evidence"):
        return False, "PA packet needs criteria evidence"
    if not p.get("requires_human_review"):
        return False, "PA packet must require human review"
    if p.get("submitted") is not False:
        return False, "PA packet must not be auto-submitted (human gate)"
    return True, "ok"


CASES: List[Tuple[str, Callable, Dict]] = [
    ("denial_appeal_anatomy", _denial_appeal_ok, DENIAL_APPEAL),
    ("prior_auth_packet_anatomy", _prior_auth_ok, PRIOR_AUTH_PACKET),
]


def _golden_cases() -> List[Tuple[str, Callable, Dict]]:
    """
    Discover golden/*.json structural suites, dispatching by file stem. Files
    whose stem is not registered in EVALUATORS (e.g. scored benchmarks handled by
    score_denial.py) are SKIPPED, so this harness is robust to new golden files.
    """
    discovered: List[Tuple[str, Callable, Dict]] = []
    if not GOLDEN_DIR.exists():
        return discovered
    for gf in sorted(GOLDEN_DIR.glob("*.json")):
        evaluator = EVALUATORS.get(gf.stem)
        if evaluator is None:
            print(f"[SKIP] {gf.name}: no structural evaluator registered "
                  f"(scored sets use their own runner)")
            continue
        suite = json.loads(gf.read_text(encoding="utf-8"))
        for case in suite.get("cases", []):
            discovered.append((f"{gf.stem}:{case.get('id', '?')}", evaluator, case))
    return discovered


def run() -> int:
    failures = 0
    for name, fn, art in CASES + _golden_cases():
        ok, msg = fn(art)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")
        failures += 0 if ok else 1
    total = len(CASES) + len(_golden_cases())
    print(f"\n{total - failures}/{total} eval cases passed")
    return failures


if __name__ == "__main__":
    sys.exit(0 if run() == 0 else 1)
