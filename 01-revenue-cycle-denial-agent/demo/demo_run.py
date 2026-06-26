"""End-to-end demo (no API key). Runs the revenue-cycle/denial workflow over the
sample claims, stopping at the human gate and resuming with a denials-specialist
approval for the appeal submission."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
import sys
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "01-revenue-cycle-denial-agent")]

from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "denials-mgr-1", "name": "Denials Specialist"}}


def main() -> None:
    samples = json.loads((_REPO / "01-revenue-cycle-denial-agent/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        print(f"\n=== {req['case_id']} (claim {req['claim_ref']})")
        print(f"  root_cause={s.get('root_cause')} appealable={s.get('appealable')} "
              f"action={s.get('recommended_action')} grounded={s.get('grounding_report',{}).get('grounded')}")
        final = resume(s, approval=APPROVAL)
        print(f"  -> case_status={final.get('case_status')} appeal_ref={final.get('appeal_ref')}")


if __name__ == "__main__":
    main()
