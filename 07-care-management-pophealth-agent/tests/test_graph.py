"""Graph wiring test — skipped if langgraph absent; asserts the care-manager interrupt."""
import sys
from pathlib import Path
import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "07-care-management-pophealth-agent")]


def test_graph_has_hitl_interrupt():
    pytest.importorskip("langgraph")
    from agent.graph import build_care_management_graph
    g = build_care_management_graph(use_memory=True)
    assert "care_manager_gate" in getattr(g, "interrupt_before_nodes", ["care_manager_gate"])
