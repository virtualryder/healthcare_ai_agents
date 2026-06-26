# agent/graph.py
# ============================================================
# LangGraph DAG for the Patient Access workflow.
#
#   intake -> verify_identity -> check_eligibility -> estimate_cost ->
#   get_availability -> prepare_summary -> compliance_check -> [routing] ->
#   { prepare_summary (revise, bounded) | human_review_gate } -> finalize -> END
#
# HITL is framework-enforced: interrupt_before=["human_review_gate"] — a patient-
# access rep approves before an appointment is booked or a registration is
# created. Account/benefit data is never disclosed without a verified identity.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    check_eligibility,
    compliance_check,
    estimate_cost,
    finalize,
    get_availability,
    intake,
    prepare_summary,
    routing_decision,
    set_recommended_action,
    verify_identity,
)
from agent.persistence import get_checkpointer
from agent.state import PatientAccessState

logger = logging.getLogger(__name__)


def build_patient_access_graph(use_memory: bool = True):
    workflow = StateGraph(PatientAccessState)

    workflow.add_node("intake", intake)
    workflow.add_node("verify_identity", verify_identity)
    workflow.add_node("check_eligibility", check_eligibility)
    workflow.add_node("estimate_cost", estimate_cost)
    workflow.add_node("get_availability", get_availability)
    workflow.add_node("prepare_summary", prepare_summary)
    workflow.add_node("compliance_check", compliance_check)
    workflow.add_node("human_review_gate", set_recommended_action)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "verify_identity")
    workflow.add_edge("verify_identity", "check_eligibility")
    workflow.add_edge("check_eligibility", "estimate_cost")
    workflow.add_edge("estimate_cost", "get_availability")
    workflow.add_edge("get_availability", "prepare_summary")
    workflow.add_edge("prepare_summary", "compliance_check")
    workflow.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={
            "prepare_summary": "prepare_summary",
            "human_review_gate": "human_review_gate",
        },
    )
    workflow.add_edge("human_review_gate", "finalize")
    workflow.add_edge("finalize", END)

    if use_memory:
        return workflow.compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["human_review_gate"],  # framework-enforced HITL
        )
    return workflow.compile()


def get_graph_visualization() -> str:
    return """
graph TD
    A[Access request: schedule / benefits / estimate] --> B[intake]
    B --> C[verify_identity]
    C --> D[check_eligibility<br/>X12 270/271]
    D --> E[estimate_cost<br/>Good Faith Estimate - deterministic]
    E --> F[get_availability]
    F --> G[prepare_summary<br/>plain-language, grounded]
    G --> H[compliance_check<br/>Grounding - PHI - Health literacy]
    H --> I{routing_decision}
    I -->|ungrounded/dense, revise| G
    I -->|ready / verify / inactive| J[human_review_gate<br/>Access Rep]
    J --> K[finalize<br/>Book + register / estimate / escalate]
    K --> L[END]
    style J fill:#4CAF50,color:#fff
    style L fill:#2196F3,color:#fff
"""
