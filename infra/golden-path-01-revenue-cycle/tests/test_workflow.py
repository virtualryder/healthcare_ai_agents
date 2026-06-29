"""
Step Functions workflow tests — exercise the REAL task logic end-to-end in fixture mode,
proving the orchestration runs through the governed gateway and that finalize enforces the
bound, single-use approval (no auto-submit on a bare decision).
"""
import os
import sys

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

import workflow  # noqa: E402
from hpp_agent_platform import approvals  # noqa: E402
from hpp_agent_platform.mcp_gateway import MCPGateway  # noqa: E402

REQUESTER = {"sub": "u-requester", "custom:hpp_role": "DENIALS_SPECIALIST"}


@pytest.fixture(autouse=True)
def _enforce(monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRE_BOUND_APPROVAL", "1")


def _run_to_compliance(gw):
    state = {"claim_ref": "CLM-2026-55810", "user_claims": REQUESTER}
    for step in ("load_claim", "analyze_denial", "gather_evidence", "draft_appeal", "compliance_check"):
        state = workflow.run_step(step, state, gateway=gw)
    return state


def test_pipeline_reads_and_grounds():
    gw = MCPGateway(connector_mode="fixture")
    state = _run_to_compliance(gw)
    assert state["load_decision"] == "ALLOW"
    assert state["analysis"]["appealable"] is True
    assert set(state["evidence"]) == {"clearinghouse.validate_claim", "ehr.get_clinical_docs", "kb.search_policy"}
    assert state["appeal"]["citations"]                      # draft cites gathered evidence
    assert state["compliance"]["ok"] is True
    assert state["pending_write"]["tool"] == "payer.submit_appeal"


def test_finalize_blocks_without_approval():
    gw = MCPGateway(connector_mode="fixture")
    state = _run_to_compliance(gw)
    state = workflow.run_step("finalize", state, gateway=gw)
    assert state["finalize"]["decision"] == "PENDING_APPROVAL"
    assert state["finalize"]["allowed"] is False


def test_finalize_executes_once_with_bound_token():
    gw = MCPGateway(connector_mode="fixture")
    state = _run_to_compliance(gw)
    pw = state["pending_write"]
    # The reviewer service mints a token bound to EXACTLY the pending write the human approved.
    token = approvals.mint_approval(reviewer_sub="u-reviewer", requester_sub="u-requester",
                                    agent_id=workflow.AGENT_ID, tool=pw["tool"], args=pw["args"])
    state["approval"] = {"token": token}
    state = workflow.run_step("finalize", state, gateway=gw)
    assert state["finalize"]["decision"] == "ALLOW"
    assert state["finalize"]["allowed"] is True
    # replay the same token on a fresh finalize -> single-use guard rejects it
    state2 = workflow.run_step("finalize", state, gateway=gw)
    assert state2["finalize"]["decision"] == "PENDING_APPROVAL"


def test_unknown_step_raises():
    with pytest.raises(ValueError):
        workflow.run_step("nope", {"user_claims": REQUESTER}, gateway=MCPGateway(connector_mode="fixture"))
