"""
Live connectors — production adapters behind the SAME method signatures as the
fixtures. A real deployment implements the organization's actual systems here
(Epic / Oracle Health via FHIR + Amazon HealthLake, the patient-accounting
system, Change Healthcare / Availity for the clearinghouse, the payer's Da Vinci
/ X12 endpoints, the MCG / InterQual criteria service, the encoder, Amazon
Connect for the contact center, etc.). Until an adapter is implemented, the stub
raises NotImplementedError so the gap is explicit rather than silent.

A reference HTTP adapter (LiveHttpConnector) is provided to show the pattern:
point <KIND>_BASE_URL at a real service and method calls become REST/FHIR round-
trips through the gateway's scoped token.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict

from .base import Connector


class LiveConnector(Connector):
    def __init__(self, kind: str) -> None:
        self.kind = kind

    def __getattr__(self, method: str) -> Any:
        def _call(**kwargs: Any) -> Any:
            raise NotImplementedError(
                f"Live connector for kind={self.kind!r} method={method!r} is not implemented. "
                f"Provide the organization adapter in connectors/live.py or set CONNECTOR_MODE=fixture."
            )
        return _call


class LiveHttpConnector(Connector):
    """Reference REST adapter: <method> -> POST {base_url}/{method} with JSON args."""

    def __init__(self, kind: str, base_url: str, timeout: int = 15) -> None:
        self.kind = kind
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def __getattr__(self, method: str) -> Any:
        def _call(**kwargs: Any) -> Any:  # pragma: no cover - network path
            url = f"{self.base_url}/{method}"
            data = json.dumps(kwargs).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        return _call
