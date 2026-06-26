# agent/graph.py
# ============================================================
# LangGraph DAG for the Prior-Authorization workflow.
#
#   intake -> check_requirement -> gather_evidence -> evaluate_criteria ->
#   assemble_packet -> compliance_check -> [routing] -> { assemble_packet (revise,
#   bounded) | human_review_gate } -> finalize -> END
#
# HITL is framework-enforced: interrupt_before=["human_review_gate"] — a PA nurse
# must approve before a request is submitted. The agent never issues a coverage
# determination (that authority is withheld from every agent).
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    assemble_packet,
    check_requirement,
    compliance_check,
    evaluate_criteria,
    finalize,
    gather_evidence,
    intake,
    routing_decision,
    set_recommended_action,
)
from agent.persistence import get_checkpointer
from agent.state import PriorAuthState

logger = logging.getLogger(__name__)


def build_prior_auth_graph(use_memory: bool = True):
    workflow = StateGraph(PriorAuthState)

    workflow.add_node("intake", intake)
    workflow.add_node("check_requirement", check_requirement)
    workflow.add_node("gather_evidence", gather_evidence)
    workflow.add_node("evaluate_criteria", evaluate_criteria)
    workflow.add_node("assemble_packet", assemble_packet)
    workflow.add_node("compliance_check", compliance_check)
    workflow.add_node("human_review_gate", set_recommended_action)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "check_requirement")
    workflow.add_edge("check_requirement", "gather_evidence")
    workflow.add_edge("gather_evidence", "evaluate_criteria")
    workflow.add_edge("evaluate_criteria", "assemble_packet")
    workflow.add_edge("assemble_packet", "compliance_check")
    workflow.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={
            "assemble_packet": "assemble_packet",        # bounded revision loop
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
    A[Requested service] --> B[intake]
    B --> C[check_requirement<br/>Da Vinci CRD]
    C --> D[gather_evidence<br/>Summary - Docs - Necessity]
    D --> E[evaluate_criteria<br/>MCG / InterQual]
    E --> F[assemble_packet<br/>LLM rationale - grounded]
    F --> G[compliance_check<br/>Grounding - PHI - Completeness]
    G --> H{routing_decision}
    H -->|ungrounded, revise| F
    H -->|ready / no-PA| I[human_review_gate<br/>PA Nurse]
    I --> J[finalize<br/>Submit 278 - Monitor status]
    J --> K[END]
    style I fill:#4CAF50,color:#fff
    style K fill:#2196F3,color:#fff
"""
