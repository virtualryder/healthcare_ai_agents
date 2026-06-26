"""Gateway error types — fail-closed authorization signals."""
from __future__ import annotations


class GatewayError(Exception):
    """Base class for all MCP gateway errors."""


class PolicyDenied(GatewayError):
    """Deny-by-default authorization refused the tool call."""


class ApprovalRequired(GatewayError):
    """A high-risk (write/irreversible) tool requires a human approval record."""
