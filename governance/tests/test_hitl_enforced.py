"""HITL is framework-enforced at the gateway: high-risk tools cannot execute without approval."""
from hpp_agent_platform.mcp_gateway import MCPGateway

def test_high_risk_blocks_without_approval():
    gw = MCPGateway(connector_mode="fixture")
    r = gw.invoke(user_claims={"sub": "u", "custom:hpp_role": "PA_COORDINATOR"},
                  agent_id="02-prior-authorization", tool="payer.submit_pa",
                  args={"service": "imaging"})
    assert r.decision == "PENDING_APPROVAL"

def test_high_risk_proceeds_with_approval():
    gw = MCPGateway(connector_mode="fixture")
    r = gw.invoke(user_claims={"sub": "u", "custom:hpp_role": "PA_COORDINATOR"},
                  agent_id="02-prior-authorization", tool="payer.submit_pa",
                  args={"service": "imaging"},
                  approval={"approved": True, "reviewer": {"sub": "nurse-1"}})
    assert r.decision == "ALLOW"
