"""
Compliance event bus — every journey step emits a PHI-masked, hash-chained evidence
event. Reuses the platform's append-only audit chain so the journey's evidence trail
is tamper-evident the same way the gateway's is. The bus is the auditable record a
reviewer or regulator reads to reconstruct exactly what happened, step by step.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

from hpp_agent_platform.mcp_gateway.audit import GatewayAuditLog  # noqa: E402


class ComplianceEventBus:
    def __init__(self) -> None:
        self._log = GatewayAuditLog()

    def emit(self, *, journey: str, step: str, agent_id: str, status: str,
             subject_ref: str = "", detail: str = "") -> str:
        return self._log.record({
            "kind": "journey_event", "journey": journey, "step": step,
            "agent_id": agent_id, "status": status, "subject_ref": subject_ref,
            "detail": detail,
        })

    @property
    def events(self) -> List[Dict[str, Any]]:
        return self._log.records

    def verify_chain(self) -> bool:
        return self._log.verify_chain()
