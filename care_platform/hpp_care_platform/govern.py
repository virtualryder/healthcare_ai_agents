"""
Governed action contract — the platform never bypasses the gateway.

Every read or write a journey performs goes through the SAME MCP authorization
gateway with the acting user's claims, so the deny-by-default intersection, the
human-approval gate, scoped tokens, and the PHI-masked audit apply identically to
platform-initiated actions. An orchestration layer that quietly widened authority
would defeat the whole design; this contract makes that impossible by construction.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

from hpp_agent_platform.mcp_gateway import MCPGateway  # noqa: E402


class GovernedActions:
    """Thin facade over the gateway for journey steps. One gateway, one audit chain."""

    def __init__(self, gateway: Optional[MCPGateway] = None, connector_mode: str = "fixture") -> None:
        self.gateway = gateway or MCPGateway(connector_mode=connector_mode)

    def call(self, *, claims: Dict[str, Any], agent_id: str, tool: str,
             args: Optional[Dict[str, Any]] = None, approval: Optional[Dict[str, Any]] = None):
        """Authorize + execute one tool call as the agent that owns this journey step."""
        return self.gateway.invoke(user_claims=claims, agent_id=agent_id, tool=tool,
                                   args=args or {}, approval=approval)
