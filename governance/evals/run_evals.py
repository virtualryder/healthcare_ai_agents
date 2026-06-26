"""
Structural eval harness. Validates that key artifacts keep their required shape —
the anatomy a reviewer and an auditor depend on. No API key, no network.
"""
from __future__ import annotations

import sys
from typing import Callable, Dict, List, Tuple

from .golden_artifacts import DENIAL_APPEAL, PRIOR_AUTH_PACKET


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


def run() -> int:
    failures = 0
    for name, fn, art in CASES:
        ok, msg = fn(art)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")
        failures += 0 if ok else 1
    print(f"\n{len(CASES) - failures}/{len(CASES)} eval cases passed")
    return failures


if __name__ == "__main__":
    sys.exit(0 if run() == 0 else 1)
