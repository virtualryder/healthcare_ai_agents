"""End-to-end demo (no API key). Runs the member-services workflow over the sample
inquiries, stopping at the rep review gate and resuming with an approval."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
import sys
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "08-contact-center-member-services-agent")]

from agent.core import run_until_gate, resume  # noqa: E402

APPROVAL = {"approved": True, "reviewer": {"sub": "msr-lead-1", "name": "Member Services Rep"}}


def main() -> None:
    samples = json.loads((_REPO / "08-contact-center-member-services-agent/data/fixtures/sample_requests.json").read_text())
    for req in samples:
        s = run_until_gate(req)
        print(f"\n=== {req['interaction_id']} ({req['inquiry_type']}, member {req.get('member_ref')})")
        print(f"  action={s.get('recommended_action')} grounded={s.get('grounding_report',{}).get('grounded')} "
              f"literacy_ok={s.get('literacy_report',{}).get('passes')} verified={s.get('identity_verified')}")
        final = resume(s, approval=APPROVAL)
        print(f"  -> case_status={final.get('case_status')} logged={final.get('interaction_logged')} "
              f"grievance={final.get('grievance_ref')}")


if __name__ == "__main__":
    main()
