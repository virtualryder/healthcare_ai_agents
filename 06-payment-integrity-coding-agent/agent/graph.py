# agent/graph.py
# ============================================================
# LangGraph DAG for the Payment Integrity & Coding workflow.
#
#   intake -> load_claim -> analyze_coding -> detect_issues -> draft_finding ->
#   compliance_check -> [routing] -> { draft_finding (revise, bounded) |
#   review_gate } -> finalize -> END
#
# HITL is framework-enforced: interrupt_before=["review_gate"]. The agent FLAGS
# for a human payment-integrity reviewer; recording a flag (pas.update_case) is a
# gated write. The agent never recoups, adjusts payment, or submits a claim.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    analyze_coding,
    compliance_check,
    detect_issues,
    draft_finding,
    finalize,
    intake,
    load_claim,
    routing_decision,
    set_recommended_action,
)
from agent.persistence import get_checkpointer
from agent.state import PaymentIntegrityState

logger = logging.getLogger(__name__)


def build_payment_integrity_graph(use_memory: bool = True):
    workflow = StateGraph(PaymentIntegrityState)

    workflow.add_node("intake", intake)
    workflow.add_node("load_claim", load_claim)
    workflow.add_node("analyze_coding", analyze_coding)
    workflow.add_node("detect_issues", detect_issues)
    workflow.add_node("draft_finding", draft_finding)
    workflow.add_node("compliance_check", compliance_check)
    workflow.add_node("review_gate", set_recommended_action)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "load_claim")
    workflow.add_edge("load_claim", "analyze_coding")
    workflow.add_edge("analyze_coding", "detect_issues")
    workflow.add_edge("detect_issues", "draft_finding")
    workflow.add_edge("draft_finding", "compliance_check")
    workflow.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={
            "draft_finding": "draft_finding",
            "review_gate": "review_gate",
        },
    )
    workflow.add_edge("review_gate", "finalize")
    workflow.add_edge("finalize", END)

    if use_memory:
        return workflow.compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["review_gate"],  # framework-enforced HITL
        )
    return workflow.compile()


def get_graph_visualization() -> str:
    return """
graph TD
    A[Claim / encounter] --> B[intake]
    B --> C[load_claim<br/>Patient accounting + docs]
    C --> D[analyze_coding<br/>Suggest - NCCI/MUE - Necessity - Scrub]
    D --> E[detect_issues<br/>Bundling - Upcoding - Duplicate - Necessity]
    E --> F[draft_finding<br/>grounded flag rationale]
    F --> G[compliance_check<br/>Grounding - PHI]
    G --> H{routing_decision}
    H -->|ungrounded, revise| F
    H -->|ready| I[review_gate<br/>Payment-Integrity Reviewer]
    I --> J[finalize<br/>Record flag - never recoup/submit]
    J --> K[END]
    style I fill:#4CAF50,color:#fff
    style K fill:#2196F3,color:#fff
"""
