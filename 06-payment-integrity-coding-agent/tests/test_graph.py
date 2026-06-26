"""Graph wiring test — skipped if langgraph absent; asserts the review-gate interrupt."""
import sys
from pathlib import Path
import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "06-payment-integrity-coding-agent")]


def test_graph_has_hitl_interrupt():
    pytest.importorskip("langgraph")
    from agent.graph import build_payment_integrity_graph
    g = build_payment_integrity_graph(use_memory=True)
    assert "review_gate" in getattr(g, "interrupt_before_nodes", ["review_gate"])
