"""End-to-end demo (no API key). Runs the patient-access workflow over the sample
requests, stopping at the human gate and resuming with an access-rep approval."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
import sys
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "04-patient-access-agent")]

from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "access-lead-1", "name": "Access Rep"}}


def main() -> None:
    samples = json.loads((_REPO / "04-patient-access-agent/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        print(f"\n=== {req['request_id']} ({req['task_type']}, member {req.get('member_ref','-')})")
        print(f"  action={s.get('recommended_action')} grounded={s.get('grounding_report',{}).get('grounded')} "
              f"literacy_ok={s.get('literacy_report',{}).get('passes')} verified={s.get('identity_verified')}")
        final = resume(s, approval=APPROVAL)
        print(f"  -> case_status={final.get('case_status')} appt={final.get('appointment_ref')} "
              f"reg={final.get('registration_ref')}")


if __name__ == "__main__":
    main()
