"""
Enforcement acceptance tests — the "failing-on-purpose" gate.

These prove that, in a DEPLOYED posture (AUTH_REQUIRE_BOUND_APPROVAL=1), the gateway
ENFORCES the controls the README claims, rather than only modeling them. Each test maps
to a step of the clean-account acceptance test in REMEDIATION-PLAN.md §4 and to a finding
it closes:

  * self-approval blocked .................... F2 (separation of duties at mint)
  * fabricated/unauthenticated reviewer blocked  F2 (demo path closed when flag set)
  * bare approved:true blocked ............... F2
  * bound token authorizes exactly once ..... F2 (bound) + F4 (durable single-use)
  * replay of a used token blocked .......... F2 / durable replay protection
  * modified arguments blocked .............. F2 (binding hash)
  * unauthorized role blocked ............... deny-by-default authorization
  * durable audit chain verifies + tamper-evident  F4
"""
import pytest

from hpp_agent_platform import approvals
from hpp_agent_platform.audit_sinks import InMemoryAppendOnlySink
from hpp_agent_platform.mcp_gateway import MCPGateway
from hpp_agent_platform.mcp_gateway.audit import GatewayAuditLog

AGENT = "01-revenue-cycle-denial"
TOOL = "payer.submit_appeal"          # high-risk write -> requires approval
ARGS = {"claim_ref": "CLM-2026-55810", "level": 1, "reviewer": "u-requester"}
REQUESTER = {"sub": "u-requester", "custom:hpp_role": "DENIALS_SPECIALIST"}


def _gw():
    return MCPGateway(connector_mode="fixture")


@pytest.fixture(autouse=True)
def _enforce(monkeypatch):
    # Deployed posture: only bound, single-use, SoD tokens authorize a write.
    monkeypatch.setenv("AUTH_REQUIRE_BOUND_APPROVAL", "1")


def _bound_token(args=ARGS, reviewer="u-reviewer", requester="u-requester"):
    return approvals.mint_approval(reviewer_sub=reviewer, requester_sub=requester,
                                   agent_id=AGENT, tool=TOOL, args=args)


def test_no_approval_pends():
    r = _gw().invoke(user_claims=REQUESTER, agent_id=AGENT, tool=TOOL, args=ARGS)
    assert r.decision == "PENDING_APPROVAL"


def test_fabricated_unauthenticated_reviewer_blocked():
    # The exact bypass: requester invents a reviewer in the request body. With the flag
    # set, the demo path is closed — this must NOT execute.
    approval = {"approved": True, "reviewer": {"sub": "totally-made-up"}}
    r = _gw().invoke(user_claims=REQUESTER, agent_id=AGENT, tool=TOOL, args=ARGS, approval=approval)
    assert r.decision == "PENDING_APPROVAL"
    assert not r.allowed


def test_bare_approved_true_blocked():
    r = _gw().invoke(user_claims=REQUESTER, agent_id=AGENT, tool=TOOL, args=ARGS,
                     approval={"approved": True})
    assert r.decision == "PENDING_APPROVAL"


def test_self_approval_refused_at_mint():
    with pytest.raises(approvals.ApprovalError):
        approvals.mint_approval(reviewer_sub="u-requester", requester_sub="u-requester",
                                agent_id=AGENT, tool=TOOL, args=ARGS)


def test_bound_token_authorizes_once():
    gw = _gw()
    r = gw.invoke(user_claims=REQUESTER, agent_id=AGENT, tool=TOOL, args=ARGS,
                  approval={"token": _bound_token()})
    assert r.decision == "ALLOW" and r.allowed
    assert r.result and r.result.get("status") == "Submitted"


def test_replay_of_used_token_blocked():
    gw = _gw()
    tok = _bound_token()
    first = gw.invoke(user_claims=REQUESTER, agent_id=AGENT, tool=TOOL, args=ARGS, approval={"token": tok})
    assert first.decision == "ALLOW"
    # same token, same call -> single-use guard rejects it
    second = gw.invoke(user_claims=REQUESTER, agent_id=AGENT, tool=TOOL, args=ARGS, approval={"token": tok})
    assert second.decision == "PENDING_APPROVAL"
    assert not second.allowed


def test_modified_arguments_blocked():
    gw = _gw()
    tok = _bound_token(args=ARGS)
    tampered = {**ARGS, "claim_ref": "CLM-OTHER-99999"}  # retarget to a different claim
    r = gw.invoke(user_claims=REQUESTER, agent_id=AGENT, tool=TOOL, args=tampered, approval={"token": tok})
    assert r.decision == "PENDING_APPROVAL"
    assert not r.allowed


def test_unauthorized_role_denied():
    stranger = {"sub": "u-x", "custom:hpp_role": "FRONT_DESK"}
    r = _gw().invoke(user_claims=stranger, agent_id=AGENT, tool=TOOL, args=ARGS,
                     approval={"token": _bound_token(requester="u-x")})
    assert r.decision == "DENY"


def test_durable_audit_chain_is_tamper_evident():
    sink = InMemoryAppendOnlySink()
    gw = MCPGateway(audit=GatewayAuditLog(sink=sink), connector_mode="fixture")
    gw.invoke(user_claims=REQUESTER, agent_id=AGENT, tool="pas.get_claim", args={"claim_ref": "CLM-1"})
    gw.invoke(user_claims=REQUESTER, agent_id=AGENT, tool=TOOL, args=ARGS,
              approval={"token": _bound_token()})
    assert gw.audit.verify_chain() is True
    # tamper with a sealed record -> chain must break
    gw.audit.records[0]["decision"] = "TAMPERED"
    assert gw.audit.verify_chain() is False
