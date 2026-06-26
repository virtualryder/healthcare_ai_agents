# app.py — Streamlit reference dashboard for Agent 03 (demo mode, no API key).
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]

import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Clinical-Administration Agent", page_icon="🏥", layout="wide")
st.title("🏥 Clinical-Administration Agent")
st.caption("Governed AI on AWS — chart-grounded drafts, 42 CFR Part 2 consent check, clinician sign-off. The agent drafts; a clinician signs.")

CLAIMS = {"sub": "ma-1", "custom:hpp_role": "CLINICAL_STAFF"}
task = st.selectbox("Task", ["chart_summary", "visit_prep", "referral", "discharge_summary", "inbox_followup"])
part2 = st.checkbox("Source is 42 CFR Part 2 (SUD) data", value=False)
if st.button("Produce draft"):
    s = run_until_gate({"task_type": task, "patient_ref": "PT-40012", "encounter_ref": "ENC-88231",
                        "part2_sensitive": part2, "acting_user_claims": CLAIMS})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Draft artifact"); st.write(s.get("artifact") or "(consent block — escalated)")
    with c2:
        st.metric("Recommended action", str(s.get("recommended_action")))
        st.metric("Grounded", str(s.get("grounding_report", {}).get("grounded")))
        st.metric("Health literacy OK", str(s.get("literacy_report", {}).get("passes")))
        st.metric("Consent block", str(s.get("consent_block")))
    st.info("⏸️ Paused at clinician review gate. A clinician signs before anything is filed.")
    if st.button("Approve & file draft (clinician)"):
        final = resume(s, {"approved": True, "reviewer": {"sub": "clinician-1"}})
        st.success(f"Case status: {final.get('case_status')} · note {final.get('note_ref')}")
