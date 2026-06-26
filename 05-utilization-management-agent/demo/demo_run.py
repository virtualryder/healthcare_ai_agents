"""End-to-end demo (no API key). Runs the UM workflow over the sample reviews,
stopping at the medical-director gate and resuming with an approval. The agent
forwards a recommendation; it never issues a determination."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
import sys
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "05-utilization-management-agent")]

from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "med-director-1", "name": "Medical Director"}}


def main() -> None:
    samples = json.loads((_REPO / "05-utilization-management-agent/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        fr = s.get("fairness_report", {})
        print(f"\n=== {req['case_id']} ({req['service']})")
        print(f"  recommendation={s.get('recommendation')} action={s.get('recommended_action')} "
              f"grounded={s.get('grounding_report',{}).get('grounded')} "
              f"fairness={'flagged' if fr.get('applied') and not fr.get('passes_four_fifths', True) else ('ok' if fr.get('applied') else 'batch-level')}")
        final = resume(s, approval=APPROVAL)
        print(f"  -> case_status={final.get('case_status')} um_case_ref={final.get('um_case_ref')}")


if __name__ == "__main__":
    main()
