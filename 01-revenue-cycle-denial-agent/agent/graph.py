# agent/graph.py
# ============================================================
# LangGraph DAG for the Revenue-Cycle & Denial workflow.
#
#   intake -> load_claim -> analyze_denial -> gather_evidence -> draft_appeal ->
#   compliance_check -> [routing] -> { draft_appeal (revise, bounded) |
#                                      human_review_gate } -> finalize -> END
#
# HITL is framework-enforced: the graph compiles with
# interrupt_before=["human_review_gate"], so a Denials Specialist must update
# state and resume before finalize runs. No application code can bypass it, and
# the agent can never submit a claim (only a biller role holds that tool).
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    analyze_denial,
    compliance_check,
    draft_appeal,
    finalize,
    gather_evidence,
    intake,
    load_claim,
    routing_decision,
    set_recommended_action,
)
from agent.persistence import get_checkpointer
from agent.state import RevenueCycleState

logger = logging.getLogger(__name__)


def build_revenue_cycle_graph(use_memory: bool = True):
    workflow = StateGraph(RevenueCycleState)

    workflow.add_node("intake", intake)
    workflow.add_node("load_claim", load_claim)
    workflow.add_node("analyze_denial", analyze_denial)
    workflow.add_node("gather_evidence", gather_evidence)
    workflow.add_node("draft_appeal", draft_appeal)
    workflow.add_node("compliance_check", compliance_check)
    workflow.add_node("human_review_gate", set_recommended_action)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "load_claim")
    workflow.add_edge("load_claim", "analyze_denial")
    workflow.add_edge("analyze_denial", "gather_evidence")
    workflow.add_edge("gather_evidence", "draft_appeal")
    workflow.add_edge("draft_appeal", "compliance_check")
    workflow.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={
            "draft_appeal": "draft_appeal",          # bounded revision loop
            "human_review_gate": "human_review_gate",  # clean or escalated -> human
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
    A[Denied / Pre-submission Claim] --> B[intake]
    B --> C[load_claim<br/>Patient accounting]
    C --> D[analyze_denial<br/>CARC/RARC root cause]
    D --> E[gather_evidence<br/>Docs - Coding - Necessity - Policy]
    E --> F[draft_appeal<br/>LLM draft - grounded]
    F --> G[compliance_check<br/>Grounding - PHI - Literacy]
    G --> H{routing_decision}
    H -->|ungrounded, revise| F
    H -->|clean / escalate| I[human_review_gate<br/>Denials Specialist]
    I --> J[finalize<br/>Submit appeal - Update case]
    J --> K[END]
    style I fill:#4CAF50,color:#fff
    style K fill:#2196F3,color:#fff
"""
