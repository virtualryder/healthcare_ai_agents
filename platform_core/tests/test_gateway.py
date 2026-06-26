"""Gateway authorization tests — deny-by-default, least-privilege intersection, HITL."""
from hpp_agent_platform.mcp_gateway import MCPGateway


def _gw():
    return MCPGateway(connector_mode="fixture")


def test_read_tool_allows_for_entitled_role():
    r = _gw().invoke(user_claims={"sub": "u", "custom:hpp_role": "DENIALS_SPECIALIST"},
                     agent_id="01-revenue-cycle-denial", tool="clearinghouse.validate_claim",
                     args={"claim_ref": "CLM-2026-55810"})
    assert r.decision == "ALLOW" and r.result["clean"] is False


def test_high_risk_write_blocks_without_approval():
    r = _gw().invoke(user_claims={"sub": "u", "custom:hpp_role": "DENIALS_SPECIALIST"},
                     agent_id="01-revenue-cycle-denial", tool="payer.submit_appeal",
                     args={"claim_ref": "CLM-2026-55810"})
    assert r.decision == "PENDING_APPROVAL"


def test_high_risk_write_proceeds_with_approval():
    r = _gw().invoke(user_claims={"sub": "u", "custom:hpp_role": "DENIALS_SPECIALIST"},
                     agent_id="01-revenue-cycle-denial", tool="payer.submit_appeal",
                     args={"claim_ref": "CLM-2026-55810"},
                     approval={"approved": True, "reviewer": {"sub": "mgr-1"}})
    assert r.decision == "ALLOW" and r.result["appeal_ref"]


def test_agent_overreach_denied():
    # The revenue-cycle agent is NOT granted claim submission (a biller submits).
    r = _gw().invoke(user_claims={"sub": "u", "custom:hpp_role": "DENIALS_MANAGER"},
                     agent_id="01-revenue-cycle-denial", tool="clearinghouse.submit_claim",
                     args={"claim_ref": "CLM-1"})
    assert r.decision == "DENY"


def test_user_underentitlement_denied():
    # UM nurse cannot issue a determination even if some agent were granted it.
    r = _gw().invoke(user_claims={"sub": "u", "custom:hpp_role": "UM_NURSE"},
                     agent_id="05-utilization-management", tool="payer.issue_determination",
                     args={"case_ref": "UM-1", "determination": "DENY"})
    assert r.decision == "DENY"


def test_no_agent_holds_issue_determination():
    from hpp_agent_platform.mcp_gateway import policy
    for agent, grants in policy.AGENT_TOOL_GRANTS.items():
        assert "payer.issue_determination" not in grants, agent


def test_unauthenticated_subject_fails_closed():
    r = _gw().invoke(user_claims={}, agent_id="01-revenue-cycle-denial",
                     tool="kb.search_policy", args={"query": "x"})
    assert r.decision == "DENY"
