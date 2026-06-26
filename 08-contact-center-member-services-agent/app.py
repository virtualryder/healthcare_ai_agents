# app.py — Streamlit reference dashboard for Agent 08 (demo mode, no API key).
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]

import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Member Services Agent", page_icon="🏥", layout="wide")
st.title("🏥 Contact Center / Member Services Agent")
st.caption("Governed AI on AWS (Amazon Connect) — identity-verified answers, plain-language responses, human-approved logging & grievance intake.")

CLAIMS = {"sub": "msr-1", "custom:hpp_role": "MEMBER_SERVICES_REP"}
itype = st.selectbox("Inquiry type", ["claim_status", "benefits", "grievance"])
verified = st.checkbox("Member identity verified", value=True)
member = st.text_input("Member ID", "MBR-30551")
if st.button("Handle inquiry"):
    s = run_until_gate({"inquiry_type": itype, "member_ref": member, "claim_ref": "CLM-2026-55810",
                        "identity_assertion": "verified-idp-token" if verified else "",
                        "acting_user_claims": CLAIMS})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Member response (draft)"); st.write(s.get("response") or "(no disclosure — see action)")
    with c2:
        st.metric("Recommended action", str(s.get("recommended_action")))
        st.metric("Identity verified", str(s.get("identity_verified")))
        st.metric("Coverage active", str(s.get("coverage_active")))
        st.metric("Health literacy OK", str(s.get("literacy_report", {}).get("passes")))
    st.info("⏸️ Paused at rep review gate. A member-services rep approves before logging / filing.")
    if st.button("Approve & finalize (rep)"):
        final = resume(s, {"approved": True, "reviewer": {"sub": "msr-lead-1"}})
        st.success(f"Case status: {final.get('case_status')} · log {final.get('interaction_logged')} · grievance {final.get('grievance_ref')}")
