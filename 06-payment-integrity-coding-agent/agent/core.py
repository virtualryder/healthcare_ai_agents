# agent/core.py
# ============================================================
# Framework-free pipeline runner — same nodes, deterministic sequence, fully
# testable without LangGraph. Honors the SAME HITL contract: STOPS at the review
# gate, returns pending state; resume() with an approval runs finalize.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, Optional

from agent import nodes


def run_until_gate(initial: Dict[str, Any]) -> Dict[str, Any]:
    s: Dict[str, Any] = dict(initial)
    s.update(nodes.intake(s))
    s.update(nodes.load_claim(s))
    s.update(nodes.analyze_coding(s))
    s.update(nodes.detect_issues(s))

    for _ in range(2):
        s.update(nodes.draft_finding(s))
        s.update(nodes.compliance_check(s))
        if nodes.routing_decision(s) == "review_gate":
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
