"""End-to-end demo (no API key). Runs the clinical-administration workflow over the
sample tasks, stopping at the clinician sign-off gate and resuming with an approval."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
import sys
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "03-clinical-administration-agent")]

from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "clinician-1", "name": "Attending"}}


def main() -> None:
    samples = json.loads((_REPO / "03-clinical-administration-agent/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        print(f"\n=== {req['task_id']} ({req['task_type']}, part2={req.get('part2_sensitive', False)})")
        print(f"  action={s.get('recommended_action')} grounded={s.get('grounding_report',{}).get('grounded')} "
              f"literacy_ok={s.get('literacy_report',{}).get('passes')} consent_block={s.get('consent_block')}")
        final = resume(s, approval=APPROVAL)
        print(f"  -> case_status={final.get('case_status')} note_ref={final.get('note_ref')}")


if __name__ == "__main__":
    main()
