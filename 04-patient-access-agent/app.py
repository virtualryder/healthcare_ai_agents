# app.py — Streamlit reference dashboard for Agent 04 (demo mode, no API key).
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]

import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Patient Access Agent", page_icon="🏥", layout="wide")
st.title("🏥 Patient Access Agent")
st.caption("Governed AI on AWS — identity-verified benefits, deterministic Good Faith Estimate, human-approved booking.")

CLAIMS = {"sub": "access-1", "custom:hpp_role": "PATIENT_ACCESS_REP"}
task = st.selectbox("Task", ["schedule", "benefits", "estimate"])
verified = st.checkbox("Identity verified", value=True)
member = st.text_input("Member ID", "MBR-30551")
if st.button("Run access workflow"):
    s = run_until_gate({"task_type": task, "patient_ref": "PT-40012", "member_ref": member,
                        "service": "99214",
                        "identity_assertion": "verified-idp-token" if verified else "",
                        "acting_user_claims": CLAIMS})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Member message"); st.write(s.get("summary") or "(no disclosure — see action)")
        st.subheader("Estimate"); st.write(s.get("estimate") or {})
    with c2:
        st.metric("Recommended action", str(s.get("recommended_action")))
        st.metric("Identity verified", str(s.get("identity_verified")))
        st.metric("Coverage active", str(s.get("coverage_active")))
        st.metric("Health literacy OK", str(s.get("literacy_report", {}).get("passes")))
    st.info("⏸️ Paused at human review gate. An access rep approves before booking/registration.")
    if st.button("Approve & finalize (rep)"):
        final = resume(s, {"approved": True, "reviewer": {"sub": "access-lead-1"}})
        st.success(f"Case status: {final.get('case_status')} · appt {final.get('appointment_ref')} · reg {final.get('registration_ref')}")
