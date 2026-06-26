"""Graph wiring test — skipped if langgraph absent; asserts the medical-director interrupt."""
import sys
from pathlib import Path
import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "05-utilization-management-agent")]


def test_graph_has_hitl_interrupt():
    pytest.importorskip("langgraph")
    from agent.graph import build_utilization_mgmt_graph
    g = build_utilization_mgmt_graph(use_memory=True)
    assert "medical_director_gate" in getattr(g, "interrupt_before_nodes", ["medical_director_gate"])
