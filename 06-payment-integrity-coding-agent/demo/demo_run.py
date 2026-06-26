"""End-to-end demo (no API key). Runs the payment-integrity/coding workflow over the
sample claims, stopping at the review gate and resuming with a reviewer approval to
record a flag. The agent flags; it never recoups, adjusts payment, or submits."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
import sys
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "06-payment-integrity-coding-agent")]

from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "pi-reviewer-1", "name": "Payment Integrity Reviewer"}}


def main() -> None:
    samples = json.loads((_REPO / "06-payment-integrity-coding-agent/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        print(f"\n=== {req['case_id']} (billed {req.get('billed_cpt')})")
        print(f"  finding={s.get('finding')} action={s.get('recommended_action')} "
              f"grounded={s.get('grounding_report',{}).get('grounded')} issues={len(s.get('issues',[]))}")
        final = resume(s, approval=APPROVAL)
        print(f"  -> case_status={final.get('case_status')} flag_ref={final.get('flag_ref')}")


if __name__ == "__main__":
    main()
