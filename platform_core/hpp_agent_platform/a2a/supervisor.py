"""
Agent-to-agent (A2A) supervisor — a governed reference hop.

Multi-agent orchestration in HPP is opt-in. The default stance (recorded as
ADR-001 in ENTERPRISE-PLATFORM.md) is in-process LangGraph today; an A2A hop
through Amazon Bedrock AgentCore is introduced only when a workflow genuinely
spans agents (e.g. the revenue-cycle agent hands a clinically complex denial to
the prior-authorization agent to assemble a retro-auth, or the patient-access
agent hands an eligibility-confirmed referral to clinical-administration).

Crucially, an A2A hop does NOT widen authority: the downstream agent still calls
the SAME MCP gateway with the SAME acting-user claims, so the deny-by-default
intersection and the human-approval gates apply identically. The supervisor here
is a thin, testable reference that proves the hop preserves least privilege.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class Handoff:
    from_agent: str
    to_agent: str
    reason: str
    payload: Dict[str, Any] = field(default_factory=dict)


class A2ASupervisor:
    """Routes a handoff to a registered downstream agent runner, preserving claims."""

    def __init__(self) -> None:
        self._runners: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self.trail: List[Handoff] = []

    def register(self, agent_id: str, runner: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self._runners[agent_id] = runner

    def handoff(self, handoff: Handoff, acting_user_claims: Dict[str, Any]) -> Dict[str, Any]:
        if handoff.to_agent not in self._runners:
            raise KeyError(f"no runner registered for {handoff.to_agent!r}")
        self.trail.append(handoff)
        # The downstream runner receives the SAME claims — authority never widens.
        state = dict(handoff.payload)
        state["acting_user_claims"] = acting_user_claims
        state["_a2a_from"] = handoff.from_agent
        return self._runners[handoff.to_agent](state)
