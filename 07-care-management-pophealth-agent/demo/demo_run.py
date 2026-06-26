"""End-to-end demo (no API key). Runs the care-management workflow over the sample
patients, stopping at the care-manager gate and resuming with an approval."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
import sys
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "07-care-management-pophealth-agent")]

from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "care-mgr-lead-1", "name": "Care Manager"}}


def main() -> None:
    samples = json.loads((_REPO / "07-care-management-pophealth-agent/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        fr = s.get("fairness_report", {})
        print(f"\n=== {req['case_id']} (part2={req.get('part2_sensitive', False)}, no_gaps={req.get('no_gaps', False)})")
        print(f"  gaps={len(s.get('open_gaps', []))} action={s.get('recommended_action')} "
              f"grounded={s.get('grounding_report',{}).get('grounded')} literacy_ok={s.get('literacy_report',{}).get('passes')} "
              f"fairness={'flagged' if fr.get('applied') and not fr.get('passes_four_fifths', True) else ('ok' if fr.get('applied') else 'pop-level')}")
        final = resume(s, approval=APPROVAL)
        print(f"  -> case_status={final.get('case_status')} plan_ref={final.get('plan_ref')}")


if __name__ == "__main__":
    main()
