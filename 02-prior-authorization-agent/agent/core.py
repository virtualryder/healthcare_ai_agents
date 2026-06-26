# agent/core.py
# ============================================================
# Framework-free pipeline runner — the same nodes, run as a deterministic
# sequence so the workflow is fully testable (and demoable) without LangGraph.
# Honors the SAME HITL contract: STOPS at the human gate, returns pending state;
# resume() with an approval executes finalize. Mirrors interrupt_before.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, Optional

from agent import nodes


def run_until_gate(initial: Dict[str, Any]) -> Dict[str, Any]:
    s: Dict[str, Any] = dict(initial)
    s.update(nodes.intake(s))
    s.update(nodes.check_requirement(s))
    s.update(nodes.gather_evidence(s))
    s.update(nodes.evaluate_criteria(s))

    for _ in range(2):
        s.update(nodes.assemble_packet(s))
        s.update(nodes.compliance_check(s))
        if nodes.routing_decision(s) == "human_review_gate":
            break
        s["revision_count"] = s.get("revision_count", 0) + 1

    s.update(nodes.set_recommended_action(s))
    s["_paused_at_gate"] = True
    return s


def resume(state: Dict[str, Any], approval: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    s = dict(state)
    s["_paused_at_gate"] = False
    if approval is not None:
        s["human_approval"] = approval
    s.update(nodes.finalize(s))
    return s
