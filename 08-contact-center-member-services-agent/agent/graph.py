# agent/graph.py
# ============================================================
# LangGraph DAG for the Contact Center / Member Services workflow.
#
#   intake -> verify_member -> retrieve -> draft_response -> compliance_check ->
#   [routing] -> { draft_response (revise, bounded) | review_gate } ->
#   finalize -> END
#
# HITL is framework-enforced: interrupt_before=["review_gate"]. A member-services
# rep approves before an interaction is logged or a grievance is filed (gated
# writes). No account detail is disclosed without a verified member identity.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    compliance_check,
    draft_response,
    finalize,
    intake,
    retrieve,
    routing_decision,
    set_recommended_action,
    verify_member,
)
from agent.persistence import get_checkpointer
from agent.state import MemberServicesState

logger = logging.getLogger(__name__)


def build_member_services_graph(use_memory: bool = True):
    workflow = StateGraph(MemberServicesState)

    workflow.add_node("intake", intake)
    workflow.add_node("verify_member", verify_member)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("draft_response", draft_response)
    workflow.add_node("compliance_check", compliance_check)
    workflow.add_node("review_gate", set_recommended_action)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "verify_member")
    workflow.add_edge("verify_member", "retrieve")
    workflow.add_edge("retrieve", "draft_response")
    workflow.add_edge("draft_response", "compliance_check")
    workflow.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={
            "draft_response": "draft_response",
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
    A[Member inquiry: claim / benefits / grievance] --> B[intake]
    B --> C[verify_member]
    C --> D[retrieve<br/>Claim status 276/277 - Eligibility 270/271]
    D --> E[draft_response<br/>plain-language, grounded]
    E --> F[compliance_check<br/>Grounding - PHI - Health literacy]
    F --> G{routing_decision}
    G -->|ungrounded/dense, revise| E
    G -->|ready / verify / inactive| H[review_gate<br/>Member-Services Rep]
    H --> I[finalize<br/>Answer+log / file grievance / escalate]
    I --> J[END]
    style H fill:#4CAF50,color:#fff
    style J fill:#2196F3,color:#fff
"""
