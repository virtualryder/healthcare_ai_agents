# app.py — Streamlit reference dashboard for Agent 06 (demo mode, no API key).
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]

import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Payment Integrity & Coding Agent", page_icon="🏥", layout="wide")
st.title("🏥 Payment Integrity & Coding Agent")
st.caption("Governed AI on AWS — NCCI/MUE edits, upcoding & duplicate detection, human review. The agent flags; it never recoups or submits.")

CLAIMS = {"sub": "coder-1", "custom:hpp_role": "CODING_SPECIALIST"}
billed = st.text_input("Billed CPT", "99215")
ncci = st.checkbox("Simulate NCCI edit", value=False)
dup = st.checkbox("Known duplicate", value=False)
nec = st.checkbox("Medical necessity supported", value=True)
if st.button("Review claim"):
    s = run_until_gate({"claim_ref": "CLM-2026-55810", "encounter_ref": "ENC-88231",
                        "billed_cpt": [billed], "billed_icd10": ["E11.9"],
                        "simulate_ncci": ncci, "duplicate": dup, "necessity_supported": nec,
                        "acting_user_claims": CLAIMS})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Finding rationale"); st.write(s.get("rationale"))
        st.subheader("Issues"); st.write(s.get("issues") or "none")
    with c2:
        st.metric("Finding", s.get("finding"))
        st.metric("Recommended action", str(s.get("recommended_action")))
        st.metric("Grounded", str(s.get("grounding_report", {}).get("grounded")))
    st.info("⏸️ Paused at review gate. A payment-integrity reviewer confirms before any flag is recorded.")
    if st.button("Approve & record flag (reviewer)"):
        final = resume(s, {"approved": True, "reviewer": {"sub": "pi-reviewer-1"}})
        st.success(f"Case status: {final.get('case_status')} · {final.get('flag_ref')}")
