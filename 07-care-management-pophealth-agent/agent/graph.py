# agent/graph.py
# ============================================================
# LangGraph DAG for the Care Management & Population Health workflow.
#
#   intake -> load_patient -> check_consent -> identify_gaps -> fairness_screen
#   -> draft_artifacts -> compliance_check -> [routing] ->
#   { draft_artifacts (revise, bounded) | care_manager_gate } -> finalize -> END
#
# HITL is framework-enforced: interrupt_before=["care_manager_gate"]. Care-plan
# updates are gated (care-manager sign-off); a 42 CFR Part 2 record without
# consent escalates and nothing is drafted. A four-fifths fairness screen runs on
# the risk-stratification step. The care manager owns the plan.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    check_consent,
    compliance_check,
    draft_artifacts,
    fairness_screen,
    finalize,
    identify_gaps,
    intake,
    load_patient,
    routing_decision,
    set_recommended_action,
)
from agent.persistence import get_checkpointer
from agent.state import CareManagementState

logger = logging.getLogger(__name__)


def build_care_management_graph(use_memory: bool = True):
    workflow = StateGraph(CareManagementState)

    workflow.add_node("intake", intake)
    workflow.add_node("load_patient", load_patient)
    workflow.add_node("check_consent", check_consent)
    workflow.add_node("identify_gaps", identify_gaps)
    workflow.add_node("fairness_screen", fairness_screen)
    workflow.add_node("draft_artifacts", draft_artifacts)
    workflow.add_node("compliance_check", compliance_check)
    workflow.add_node("care_manager_gate", set_recommended_action)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "load_patient")
    workflow.add_edge("load_patient", "check_consent")
    workflow.add_edge("check_consent", "identify_gaps")
    workflow.add_edge("identify_gaps", "fairness_screen")
    workflow.add_edge("fairness_screen", "draft_artifacts")
    workflow.add_edge("draft_artifacts", "compliance_check")
    workflow.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={
            "draft_artifacts": "draft_artifacts",
            "care_manager_gate": "care_manager_gate",
        },
    )
    workflow.add_edge("care_manager_gate", "finalize")
    workflow.add_edge("finalize", END)

    if use_memory:
        return workflow.compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["care_manager_gate"],  # framework-enforced HITL
        )
    return workflow.compile()


def get_graph_visualization() -> str:
    return """
graph TD
    A[Care-management review] --> B[intake]
    B --> C[load_patient<br/>EHR + care plan]
    C --> D[check_consent<br/>42 CFR Part 2]
    D --> E[identify_gaps<br/>Care gaps - HCC/RAF - SDOH]
    E --> F[fairness_screen<br/>EEOC four-fifths]
    F --> G[draft_artifacts<br/>Outreach + care-plan update]
    G --> H[compliance_check<br/>Grounding - PHI - Literacy - Fairness]
    H --> I{routing_decision}
    I -->|ungrounded/dense, revise| G
    I -->|ready / no gaps / consent block| J[care_manager_gate<br/>Care-Manager sign-off]
    J --> K[finalize<br/>Update plan / no action / escalate]
    K --> L[END]
    style J fill:#4CAF50,color:#fff
    style L fill:#2196F3,color:#fff
"""
