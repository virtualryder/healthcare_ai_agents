"""The LIVE HTTP connector path round-trips against the reference façade (no API key).
Proves CONNECTOR_MODE=live is a real HTTP call through the gateway, not a fixture."""
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "01-revenue-cycle-denial-agent")]

from demo.reference_facade import serve
from hpp_agent_platform.connectors import get_connector
from hpp_agent_platform.mcp_gateway import MCPGateway


def _facade():
    s = serve(port=0)
    base = f"http://{s.server_address[0]}:{s.server_address[1]}"
    return s, base


def test_live_http_connector_round_trips():
    s, base = _facade()
    try:
        os.environ["PAS_BASE_URL"] = base
        conn = get_connector("pas", mode="live")            # LiveHttpConnector
        out = conn.get_claim(claim_ref="CLM-2026-55810")    # real HTTP POST
        assert out["status"] == "Denied" and out["denial_codes"] == ["CO-197"]
    finally:
        s.shutdown()


def test_gateway_drives_live_connector():
    s, base = _facade()
    try:
        os.environ["PAS_BASE_URL"] = base
        gw = MCPGateway(connector_mode="live")
        r = gw.invoke(user_claims={"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"},
                      agent_id="01-revenue-cycle-denial", tool="pas.get_claim",
                      args={"claim_ref": "CLM-2026-55810"})
        assert r.decision == "ALLOW" and r.result["status"] == "Denied"
    finally:
        s.shutdown()
        os.environ.pop("PAS_BASE_URL", None)


def test_sandbox_connector_round_trips_with_lineage():
    """CONNECTOR_MODE=sandbox uses the resilient adapter over a REAL socket against the façade,
    capturing lineage (system/endpoint/status/attempts/latency/request_id)."""
    from hpp_agent_platform.connectors.sandbox import SandboxHttpConnector
    s, base = _facade()
    try:
        os.environ["PAS_BASE_URL"] = base
        conn = get_connector("pas", mode="sandbox")
        assert isinstance(conn, SandboxHttpConnector)
        out = conn.get_claim(claim_ref="CLM-2026-55810")    # real HTTP via resilient path
        assert out["status"] == "Denied" and out["denial_codes"] == ["CO-197"]
        assert conn.last_lineage["http_status"] == 200
        assert conn.last_lineage["attempts"] == 1
        assert conn.last_lineage["request_id"]
        assert conn.last_lineage["endpoint"].endswith("/get_claim")
    finally:
        s.shutdown()
        os.environ.pop("PAS_BASE_URL", None)


def test_gateway_drives_sandbox_connector():
    s, base = _facade()
    try:
        os.environ["PAS_BASE_URL"] = base
        gw = MCPGateway(connector_mode="sandbox")
        r = gw.invoke(user_claims={"sub": "rcm-1", "custom:hpp_role": "DENIALS_SPECIALIST"},
                      agent_id="01-revenue-cycle-denial", tool="pas.get_claim",
                      args={"claim_ref": "CLM-2026-55810"})
        assert r.decision == "ALLOW" and r.result["status"] == "Denied"
    finally:
        s.shutdown()
        os.environ.pop("PAS_BASE_URL", None)
