# app.py — Streamlit reference dashboard for Agent 02 (demo mode, no API key).
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]

import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Prior-Authorization Agent", page_icon="🏥", layout="wide")
st.title("🏥 Prior-Authorization Agent")
st.caption("Governed AI on AWS — Da Vinci requirement check, criteria-grounded packet, human-approved submission. The coverage decision stays with the payer.")

CLAIMS = {"sub": "pa-coord-1", "custom:hpp_role": "PA_COORDINATOR"}
service = st.text_input("Requested service (CPT/HCPCS)", "72148")
urgent = st.checkbox("Urgent / expedited", value=False)
if st.button("Assess & assemble PA"):
    s = run_until_gate({"service": service, "urgent": urgent, "patient_ref": "PT-40012",
                        "encounter_ref": "ENC-88231", "diagnosis": ["M54.16"],
                        "acting_user_claims": CLAIMS})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("PA rationale"); st.write(s.get("pa_rationale") or "(no PA required)")
        st.subheader("Citations")
        for c in s.get("citations", []):
            st.markdown(f"- [{c['title']}]({c['url']})")
    with c2:
        st.metric("PA required", str(s.get("pa_required")))
        st.metric("Recommended action", str(s.get("recommended_action")))
        st.metric("Grounded", str(s.get("grounding_report", {}).get("grounded")))
        st.subheader("Missing info"); st.write(s.get("missing_info") or "none")
    st.info("⏸️ Paused at human review gate. A PA nurse approves before submission.")
    if st.button("Approve & submit (nurse)"):
        final = resume(s, {"approved": True, "reviewer": {"sub": "pa-nurse-1"}})
        st.success(f"Case status: {final.get('case_status')} · PA {final.get('pa_ref')} ({final.get('pa_status')})")
