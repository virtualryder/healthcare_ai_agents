"""End-to-end demo (no API key). Runs the prior-auth workflow over the sample
requests, stopping at the human gate and resuming with a PA-nurse approval for
submission."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
import sys
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "02-prior-authorization-agent")]

from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "pa-nurse-1", "name": "PA Nurse"}}


def main() -> None:
    samples = json.loads((_REPO / "02-prior-authorization-agent/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        print(f"\n=== {req['case_id']} (service {req['service']}, urgent={req.get('urgent')})")
        print(f"  pa_required={s.get('pa_required')} action={s.get('recommended_action')} "
              f"grounded={s.get('grounding_report',{}).get('grounded')} missing={s.get('missing_info')}")
        final = resume(s, approval=APPROVAL)
        print(f"  -> case_status={final.get('case_status')} pa_ref={final.get('pa_ref')} "
              f"pa_status={final.get('pa_status')}")


if __name__ == "__main__":
    main()
