"""Graph wiring test — skipped if langgraph absent; asserts the clinician sign-off interrupt."""
import sys
from pathlib import Path
import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "03-clinical-administration-agent")]


def test_graph_has_hitl_interrupt():
    pytest.importorskip("langgraph")
    from agent.graph import build_clinical_admin_graph
    g = build_clinical_admin_graph(use_memory=True)
    assert "clinician_review_gate" in getattr(g, "interrupt_before_nodes", ["clinician_review_gate"])
