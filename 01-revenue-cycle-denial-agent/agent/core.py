# agent/core.py
# ============================================================
# Framework-free pipeline runner — the same nodes, run as a deterministic
# sequence so the workflow is fully testable (and demoable) without LangGraph.
# It honors the SAME HITL contract: the run STOPS at the human gate and returns
# the pending state; call resume() with an approval to execute finalize. This
# mirrors what interrupt_before does in graph.py.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, Optional

from agent import nodes


def run_until_gate(initial: Dict[str, Any]) -> Dict[str, Any]:
    s: Dict[str, Any] = dict(initial)
    s.update(nodes.intake(s))
    s.update(nodes.load_claim(s))
    s.update(nodes.analyze_denial(s))
    s.update(nodes.gather_evidence(s))

    # draft -> compliance -> (bounded revision) -> draft -> compliance
    for _ in range(2):
        s.update(nodes.draft_appeal(s))
        s.update(nodes.compliance_check(s))
        if nodes.routing_decision(s) == "human_review_gate":
            break
        s["revision_count"] = s.get("revision_count", 0) + 1

    s.update(nodes.set_recommended_action(s))   # the human_review_gate node
    s["_paused_at_gate"] = True
    return s


def resume(state: Dict[str, Any], approval: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    s = dict(state)
    s["_paused_at_gate"] = False
    if approval is not None:
        s["human_approval"] = approval
    s.update(nodes.finalize(s))
    return s
