# agent/graph.py
# ============================================================
# LangGraph DAG for the Utilization-Management workflow.
#
#   intake -> gather_clinical -> evaluate_criteria -> fairness_screen ->
#   draft_recommendation -> compliance_check -> [routing] ->
#   { draft_recommendation (revise, bounded) | medical_director_gate } ->
#   finalize -> END
#
# HITL is framework-enforced: interrupt_before=["medical_director_gate"]. The
# agent prepares a RECOMMENDATION; the coverage DETERMINATION is the medical
# director's. payer.issue_determination is withheld from every agent — even an
# adverse recommendation is forwarded for a human decision, never auto-denied.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    compliance_check,
    draft_recommendation,
    evaluate_criteria,
    fairness_screen,
    finalize,
    gather_clinical,
    intake,
    routing_decision,
    set_recommended_action,
)
from agent.persistence import get_checkpointer
from agent.state import UtilizationMgmtState

logger = logging.getLogger(__name__)


def build_utilization_mgmt_graph(use_memory: bool = True):
    workflow = StateGraph(UtilizationMgmtState)

    workflow.add_node("intake", intake)
    workflow.add_node("gather_clinical", gather_clinical)
    workflow.add_node("evaluate_criteria", evaluate_criteria)
    workflow.add_node("fairness_screen", fairness_screen)
    workflow.add_node("draft_recommendation", draft_recommendation)
    workflow.add_node("compliance_check", compliance_check)
    workflow.add_node("medical_director_gate", set_recommended_action)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "gather_clinical")
    workflow.add_edge("gather_clinical", "evaluate_criteria")
    workflow.add_edge("evaluate_criteria", "fairness_screen")
    workflow.add_edge("fairness_screen", "draft_recommendation")
    workflow.add_edge("draft_recommendation", "compliance_check")
    workflow.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={
            "draft_recommendation": "draft_recommendation",
            "medical_director_gate": "medical_director_gate",
        },
    )
    workflow.add_edge("medical_director_gate", "finalize")
    workflow.add_edge("finalize", END)

    if use_memory:
        return workflow.compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["medical_director_gate"],  # framework-enforced HITL
        )
    return workflow.compile()


def get_graph_visualization() -> str:
    return """
graph TD
    A[UM review request] --> B[intake]
    B --> C[gather_clinical<br/>EHR docs - PA status]
    C --> D[evaluate_criteria<br/>MCG / InterQual]
    D --> E[fairness_screen<br/>EEOC four-fifths]
    E --> F[draft_recommendation<br/>MEETS / NOT MEET / NEEDS INFO]
    F --> G[compliance_check<br/>Grounding - PHI - Fairness]
    G --> H{routing_decision}
    H -->|ungrounded, revise| F
    H -->|ready| I[medical_director_gate<br/>Medical Director decides]
    I --> J[finalize<br/>Forward recommendation - never auto-deny]
    J --> K[END]
    style I fill:#4CAF50,color:#fff
    style K fill:#2196F3,color:#fff
"""
