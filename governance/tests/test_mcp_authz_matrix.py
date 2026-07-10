"""MCP authorization negative-test matrix — the 12 cases a security reviewer expects, proven
against the SHIPPING HPP gateway. Framing maps to the deployed edge (401/403/deny).

  1 no token -> 401            5 wrong role -> deny        9  tampered approval args -> deny
  2 bad token -> 401           6 wrong data class -> deny  10 stale/expired approval -> deny
  3 missing scope -> 403       7 self-approval -> deny      11 no outbound credential -> deny
  4 unregistered tool -> deny  8 replayed approval -> deny  12 audit write failure -> deny
"""
import pytest

from hpp_agent_platform import approvals, jwt_verify
from hpp_agent_platform.mcp_gateway import tokens
from hpp_agent_platform.mcp_gateway.gateway import MCPGateway
from hpp_agent_platform.mcp_gateway.audit import GatewayAuditLog

AGENT = "01-revenue-cycle-denial"
USER = {"sub": "u-den", "custom:hpp_role": "DENIALS_SPECIALIST"}
WRONG = {"sub": "u-msr", "custom:hpp_role": "MEMBER_SERVICES_REP"}
READ = "pas.get_claim"
WRITE = "payer.submit_appeal"
OTHER_DATACLASS_TOOL = "careplan.get_care_plan"    # care-management data class — agent 01 not granted it
ARGS = {"claim_id": "CLM-1"}


def gw():
    return MCPGateway(audit=GatewayAuditLog(), connector_mode="fixture")


def test_01_no_token():
    assert gw().invoke(user_claims={}, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


def test_02_bad_token():
    with pytest.raises(jwt_verify.JWTError):
        jwt_verify.verify_jwt("not-a-jwt", jwks={"keys": []}, issuer="https://issuer", audience="app")


def test_03_missing_scope():
    tok = tokens.mint_scoped_token(subject="u-den", agent_id=AGENT, tool=READ, scope=[READ])
    with pytest.raises(ValueError):
        tokens.verify_scoped_token(tok, expected_tool=WRITE)


def test_04_unregistered_tool():
    assert gw().invoke(user_claims=USER, agent_id=AGENT, tool="pas.exfiltrate_all", args={}).decision == "DENY"


def test_05_wrong_role():
    assert gw().invoke(user_claims=WRONG, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


def test_06_wrong_data_class():
    assert gw().invoke(user_claims=USER, agent_id=AGENT, tool=OTHER_DATACLASS_TOOL, args={}).decision == "DENY"


def test_07_self_approval():
    with pytest.raises(approvals.ApprovalError):
        approvals.mint_approval(reviewer_sub="u-x", requester_sub="u-x", agent_id=AGENT, tool=WRITE, args=ARGS)


def test_08_replayed_approval():
    store = approvals.InMemoryJtiStore()
    tok = approvals.mint_approval(reviewer_sub="u-mgr", requester_sub="u-den", agent_id=AGENT, tool=WRITE, args=ARGS)
    approvals.verify_approval(tok, agent_id=AGENT, tool=WRITE, requester_sub="u-den", args=ARGS, jti_store=store)
    with pytest.raises(approvals.ApprovalError):
        approvals.verify_approval(tok, agent_id=AGENT, tool=WRITE, requester_sub="u-den", args=ARGS, jti_store=store)


def test_09_tampered_approval_args():
    tok = approvals.mint_approval(reviewer_sub="u-mgr", requester_sub="u-den", agent_id=AGENT, tool=WRITE, args=ARGS)
    with pytest.raises(approvals.ApprovalError):
        approvals.verify_approval(tok, agent_id=AGENT, tool=WRITE, requester_sub="u-den", args={"claim_id": "X"})


def test_10_expired_approval():
    tok = approvals.mint_approval(reviewer_sub="u-mgr", requester_sub="u-den", agent_id=AGENT,
                                  tool=WRITE, args=ARGS, ttl=-1000)
    with pytest.raises(approvals.ApprovalError):
        approvals.verify_approval(tok, agent_id=AGENT, tool=WRITE, requester_sub="u-den", args=ARGS)


def test_11_no_outbound_credential():
    with pytest.raises(ValueError):
        tokens.verify_scoped_token("no.valid.outbound.token", expected_tool=READ)


def test_12_audit_write_failure():
    g = gw()
    g.audit.record = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("audit sink down"))
    with pytest.raises(Exception):
        g.invoke(user_claims=USER, agent_id=AGENT, tool=READ, args=ARGS)
