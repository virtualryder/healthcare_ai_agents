# app.py — Streamlit reference dashboard for Agent 01 (demo mode, no API key).
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]

import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Revenue-Cycle & Denial Agent", page_icon="🏥", layout="wide")
st.title("🏥 Revenue-Cycle & Denial Management Agent")
st.caption("Governed AI on AWS — grounded appeals, PHI-masked audit, human-approved submission. The agent never submits a claim.")

# The shipped image is secure by default (AUTH_REQUIRE_JWT=1): the gateway will not accept
# the demo's fixture claims without a verified JWT. This local dashboard has no authorizer,
# so it requires an EXPLICIT auth-off override — we do not silently disable it here.
if os.getenv("AUTH_REQUIRE_JWT", "").strip().lower() in ("1", "true", "yes"):
    st.error(
        "AUTH_REQUIRE_JWT is enabled (the secure-by-default image setting). The demo runs "
        "with fixture claims and no authorizer, so it needs an explicit override:\n\n"
        "`AUTH_REQUIRE_JWT=0 EXTRACT_MODE=demo streamlit run app.py`\n\n"
        "The runtime /invocations path stays secure — see README “Container auth contract”."
    )
    st.stop()

CLAIMS = {"sub": "rcm-rep-1", "custom:hpp_role": "DENIALS_SPECIALIST"}
claim_ref = st.text_input("Denied claim reference", "CLM-2026-55810")
if st.button("Review denial & draft appeal"):
    s = run_until_gate({"claim_ref": claim_ref, "mode": "POST_DENIAL", "acting_user_claims": CLAIMS})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Drafted appeal"); st.write(s.get("appeal_letter"))
        st.subheader("Citations")
        for c in s.get("citations", []):
            st.markdown(f"- [{c['title']}]({c['url']})")
    with c2:
        st.metric("Root cause", s.get("root_cause"))
        st.metric("Recommended action", str(s.get("recommended_action")))
        st.metric("Grounded", str(s.get("grounding_report", {}).get("grounded")))
        st.metric("Appealable", str(s.get("appealable")))
        st.subheader("Compliance findings"); st.write(s.get("quality_findings") or "none")
    st.info("⏸️ Paused at human review gate. A denials specialist approves before the appeal is submitted.")
    if st.button("Approve & submit appeal (specialist)"):
        final = resume(s, {"approved": True, "reviewer": {"sub": "denials-mgr-1"}})
        st.success(f"Case status: {final.get('case_status')} · appeal {final.get('appeal_ref')}")
