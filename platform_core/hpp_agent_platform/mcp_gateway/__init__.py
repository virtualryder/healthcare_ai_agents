"""HPP MCP authorization gateway — reference logic for Bedrock AgentCore Gateway + Identity."""
from .gateway import MCPGateway, GatewayResult
from .audit import GatewayAuditLog
from .errors import ApprovalRequired, GatewayError, PolicyDenied
from . import policy

__all__ = [
    "MCPGateway", "GatewayResult", "GatewayAuditLog",
    "ApprovalRequired", "GatewayError", "PolicyDenied", "policy",
]
