"""CI gate for the HPP Agent 01 (Revenue-Cycle Denials) 10-point negative demo."""
import importlib.util
import os

import pytest

from hpp_agent_platform import approvals, budget, jwt_verify
from hpp_agent_platform.mcp_gateway import audit as audit_mod
from hpp_agent_platform.mcp_gateway.gateway import MCPGateway
from hpp_agent_platform.mcp_gateway.audit import GatewayAuditLog

AGENT = "01-revenue-cycle-denial"
USER = {"sub": "u-den", "custom:hpp_role": "DENIALS_SPECIALIST"}
WRONG = {"sub": "u-msr", "custom:hpp_role": "MEMBER_SERVICES_REP"}
READ = "pas.get_claim"
WRITE = "payer.submit_appeal"
ARGS = {"claim_id": "CLM-1"}


def gw():
    return MCPGateway(audit=GatewayAuditLog(), connector_mode="fixture")


def test_1_no_jwt():
    assert gw().invoke(user_claims={}, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


def test_2_bad_jwt():
    with pytest.raises(jwt_verify.JWTError):
        jwt_verify.verify_jwt("not-a-jwt", jwks={"keys": []}, issuer="https://issuer", audience="app")


def test_3_wrong_role():
    assert gw().invoke(user_claims=WRONG, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


def test_4_unregistered_tool():
    assert gw().invoke(user_claims=USER, agent_id=AGENT, tool="pas.exfiltrate_all", args={}).decision == "DENY"


def test_5_self_approval():
    with pytest.raises(approvals.ApprovalError):
        approvals.mint_approval(reviewer_sub="u-x", requester_sub="u-x", agent_id=AGENT, tool=WRITE, args=ARGS)


def test_6_replay():
    store = approvals.InMemoryJtiStore()
    tok = approvals.mint_approval(reviewer_sub="u-mgr", requester_sub="u-den", agent_id=AGENT, tool=WRITE, args=ARGS)
    approvals.verify_approval(tok, agent_id=AGENT, tool=WRITE, requester_sub="u-den", args=ARGS, jti_store=store)
    with pytest.raises(approvals.ApprovalError):
        approvals.verify_approval(tok, agent_id=AGENT, tool=WRITE, requester_sub="u-den", args=ARGS, jti_store=store)


def test_7_tampered_args():
    tok = approvals.mint_approval(reviewer_sub="u-mgr", requester_sub="u-den", agent_id=AGENT, tool=WRITE, args=ARGS)
    with pytest.raises(approvals.ApprovalError):
        approvals.verify_approval(tok, agent_id=AGENT, tool=WRITE, requester_sub="u-den", args={"claim_id": "X"})


def test_8_masking_fail_closed():
    log = GatewayAuditLog()
    orig = audit_mod.mask
    audit_mod.mask = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("masker down"))
    try:
        with pytest.raises(Exception):
            log.record({"decision": "ALLOW", "tool": READ, "args": {"note": "SSN 123-45-6789"}})
        assert log.records == []
    finally:
        audit_mod.mask = orig


def test_9_audit_fail_closed():
    g = gw()
    g.audit.record = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("audit down"))
    with pytest.raises(Exception):
        g.invoke(user_claims=USER, agent_id=AGENT, tool=READ, args=ARGS)


def test_10_budget_exceeded():
    m = budget.BudgetMeter(agent_id=AGENT, dept="RevCycle", monthly_token_cap=1000, cap_behavior="hard")
    m.commit(900)
    assert m.preflight(500).allowed is False


def test_demo_exits_zero():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "01-revenue-cycle-denial-agent", "demo", "negative_demo.py")
    spec = importlib.util.spec_from_file_location("hppneg", os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
