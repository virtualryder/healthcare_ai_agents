# agent/graph.py
# ============================================================
# LangGraph DAG for the Clinical-Administration workflow.
#
#   intake -> load_chart -> check_consent -> produce_artifact -> compliance_check
#   -> [routing] -> { produce_artifact (revise, bounded) | clinician_review_gate }
#   -> finalize -> END
#
# HITL is framework-enforced: interrupt_before=["clinician_review_gate"] — a
# licensed clinician must review and sign before a draft note is filed. The agent
# has no order-entry or signing authority, and a 42 CFR Part 2 consent block
# routes straight to escalation.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    check_consent,
    compliance_check,
    finalize,
    intake,
    load_chart,
    produce_artifact,
    routing_decision,
    set_recommended_action,
)
from agent.persistence import get_checkpointer
from agent.state import ClinicalAdminState

logger = logging.getLogger(__name__)


def build_clinical_admin_graph(use_memory: bool = True):
    workflow = StateGraph(ClinicalAdminState)

    workflow.add_node("intake", intake)
    workflow.add_node("load_chart", load_chart)
    workflow.add_node("check_consent", check_consent)
    workflow.add_node("produce_artifact", produce_artifact)
    workflow.add_node("compliance_check", compliance_check)
    workflow.add_node("clinician_review_gate", set_recommended_action)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "load_chart")
    workflow.add_edge("load_chart", "check_consent")
    workflow.add_edge("check_consent", "produce_artifact")
    workflow.add_edge("produce_artifact", "compliance_check")
    workflow.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={
            "produce_artifact": "produce_artifact",
            "clinician_review_gate": "clinician_review_gate",
        },
    )
    workflow.add_edge("clinician_review_gate", "finalize")
    workflow.add_edge("finalize", END)

    if use_memory:
        return workflow.compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["clinician_review_gate"],  # framework-enforced HITL
        )
    return workflow.compile()


def get_graph_visualization() -> str:
    return """
graph TD
    A[Task: summary / prep / referral / discharge / inbox] --> B[intake]
    B --> C[load_chart<br/>EHR FHIR + care plan]
    C --> D[check_consent<br/>42 CFR Part 2]
    D --> E[produce_artifact<br/>chart-grounded draft]
    E --> F[compliance_check<br/>Grounding - PHI - Health literacy]
    F --> G{routing_decision}
    G -->|ungrounded/dense, revise| E
    G -->|ready / consent block| H[clinician_review_gate<br/>Clinician sign-off]
    H --> I[finalize<br/>File draft note / prep ready / escalate]
    I --> J[END]
    style H fill:#4CAF50,color:#fff
    style J fill:#2196F3,color:#fff
"""
