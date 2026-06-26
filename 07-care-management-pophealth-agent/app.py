# app.py — Streamlit reference dashboard for Agent 07 (demo mode, no API key).
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]

import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Care Management Agent", page_icon="🏥", layout="wide")
st.title("🏥 Care Management & Population Health Agent")
st.caption("Governed AI on AWS — care-gap + risk + SDOH, fairness screen, care-manager sign-off. The care manager owns the plan.")

CLAIMS = {"sub": "care-mgr-1", "custom:hpp_role": "CARE_MANAGER"}
no_gaps = st.checkbox("No open gaps (review scenario)", value=False)
part2 = st.checkbox("Source is 42 CFR Part 2 (SUD) data", value=False)
if st.button("Run care-management review"):
    s = run_until_gate({"patient_ref": "PT-40012", "no_gaps": no_gaps, "part2_sensitive": part2,
                        "acting_user_claims": CLAIMS})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Outreach (draft)"); st.write(s.get("outreach") or "(no outreach — see action)")
        st.subheader("Care-plan update"); st.write(s.get("care_plan_update") or "")
    with c2:
        st.metric("Open gaps", len(s.get("open_gaps", [])))
        st.metric("HCC risk score", s.get("risk_score_hcc"))
        st.metric("Recommended action", str(s.get("recommended_action")))
        st.metric("Consent block", str(s.get("consent_block")))
        st.subheader("Fairness"); st.write(s.get("fairness_report"))
    st.info("⏸️ Paused at care-manager gate. A care manager signs off before the plan is updated.")
    if st.button("Approve & update plan (care manager)"):
        final = resume(s, {"approved": True, "reviewer": {"sub": "care-mgr-lead-1"}})
        st.success(f"Case status: {final.get('case_status')} · {final.get('plan_ref')}")
