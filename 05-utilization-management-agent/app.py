# app.py — Streamlit reference dashboard for Agent 05 (demo mode, no API key).
from __future__ import annotations
import os, sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_REPO = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(Path(__file__).resolve().parent)]

import streamlit as st  # noqa: E402
from agent.core import run_until_gate, resume  # noqa: E402

st.set_page_config(page_title="Utilization Management Agent", page_icon="🏥", layout="wide")
st.title("🏥 Utilization Management Agent")
st.caption("Governed AI on AWS — criteria-based recommendation, fairness screen, medical-director decides. The agent never issues a determination.")

CLAIMS = {"sub": "um-nurse-1", "custom:hpp_role": "UM_NURSE"}
service = st.text_input("Requested service / level of care", "inpatient admission")
meets = st.checkbox("Evidence meets criteria (review scenario)", value=True)
if st.button("Apply criteria & draft recommendation"):
    s = run_until_gate({"service": service, "cpt": ["99223"], "diagnosis": ["I50.9"],
                        "encounter_ref": "ENC-88231", "meets": meets, "acting_user_claims": CLAIMS})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Recommendation rationale"); st.write(s.get("rationale"))
        st.subheader("Citations")
        for c in s.get("citations", []):
            st.markdown(f"- [{c['title']}]({c['url']})")
    with c2:
        st.metric("Recommendation", s.get("recommendation"))
        st.metric("Recommended action", str(s.get("recommended_action")))
        st.metric("Grounded", str(s.get("grounding_report", {}).get("grounded")))
        st.subheader("Fairness"); st.write(s.get("fairness_report"))
    st.warning("⏸️ Paused at medical-director gate. The agent forwards a recommendation; the medical director issues any determination.")
    if st.button("Approve & forward recommendation (director)"):
        final = resume(s, {"approved": True, "reviewer": {"sub": "med-director-1"}})
        st.success(f"Case status: {final.get('case_status')} · {final.get('um_case_ref')}")
