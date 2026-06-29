"""End-to-end LIVE-CONNECTOR demo (no API key, no real EHR).

Runs Agent 01's full workflow with CONNECTOR_MODE=live against the bundled reference façade —
every system call is a real HTTP round-trip through the governed gateway, not a fixture. The
LLM drafting stays deterministic (EXTRACT_MODE=demo) so this proves the *connector* path without
needing Bedrock/Anthropic. To go live for real: point the *_BASE_URL at the customer's
FHIR/X12 gateway and set EXTRACT_MODE=live LLM_PROVIDER=bedrock — the agent code does not change."""
from __future__ import annotations
import os, sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "01-revenue-cycle-denial-agent")]
from demo.reference_facade import serve  # noqa: E402


def main() -> None:
    server = serve(port=0)
    base = f"http://{server.server_address[0]}:{server.server_address[1]}"
    # point every system-of-record connector Agent 01 uses at the façade
    for kind in ("PAS", "CLEARINGHOUSE", "PAYER", "CODING", "EHR", "KB"):
        os.environ[f"{kind}_BASE_URL"] = base
    os.environ["CONNECTOR_MODE"] = "live"     # real HTTP connectors
    os.environ["EXTRACT_MODE"] = "demo"       # deterministic drafting (no API key)

    from agent.core import run_until_gate, resume
    print(f"Live connectors → {base}  (CONNECTOR_MODE=live)\n")
    s = run_until_gate({"claim_ref": "CLM-2026-55810", "mode": "POST_DENIAL",
                        "acting_user_claims": {"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"}})
    print(f"  loaded claim (live HTTP): status={s['claim'].get('status')} denials={s.get('denial_codes')}")
    print(f"  root_cause={s.get('root_cause')} action={s.get('recommended_action')} "
          f"grounded={s.get('grounding_report',{}).get('grounded')}")
    final = resume(s, {"approved": True, "reviewer": {"sub": "denials-mgr-1"}})
    print(f"  -> case_status={final.get('case_status')} appeal_ref={final.get('appeal_ref')} (submitted via live façade)")
    server.shutdown()


if __name__ == "__main__":
    main()
