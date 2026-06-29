"""
Connector factory — resolve a connector by kind and mode.

    get_connector("clearinghouse")          # mode from CONNECTOR_MODE (default fixture)
    get_connector("payer", "live")           # bare reference REST adapter
    get_connector("payer", "sandbox")        # production-grade resilient adapter

Modes:
    fixture   deterministic offline store (demos, CI, evals)                 [default]
    live      bare reference REST/FHIR round-trip (LiveHttpConnector)
    sandbox   resilient adapter (SandboxHttpConnector): auth, idempotency, retries,
              timeout, circuit breaker, write reconciliation, lineage — point at a
              customer sandbox (Availity / Change Healthcare / payer FHIR) or the façade

Live/sandbox resolution: if <KIND>_BASE_URL is set (e.g. PAYER_BASE_URL, EHR_BASE_URL) — or
SANDBOX_BASE_URL as a fallback — an HTTP adapter is returned. Otherwise a LiveConnector stub is
returned so an unimplemented integration fails loudly, not silently.
"""
from __future__ import annotations

import os
from typing import Optional

from .base import Connector
from .fixtures import build_fixture
from .live import LiveConnector, LiveHttpConnector

_KINDS = {"ehr", "pas", "clearinghouse", "payer", "coding", "clinicalcriteria",
          "careplan", "scheduling", "registration", "kb", "identity", "consent",
          "idp", "contactcenter"}


def _base_url(kind: str) -> str:
    return os.getenv(f"{kind.upper()}_BASE_URL", "") or os.getenv("SANDBOX_BASE_URL", "")


def get_connector(kind: str, mode: Optional[str] = None) -> Connector:
    if kind not in _KINDS:
        raise ValueError(f"unknown connector kind {kind!r}")
    mode = (mode or os.getenv("CONNECTOR_MODE", "fixture")).strip().lower()

    if mode == "sandbox":
        base_url = _base_url(kind)
        if not base_url:
            return LiveConnector(kind)  # fail loud: no endpoint configured
        from .sandbox import SandboxHttpConnector, build_auth
        return SandboxHttpConnector(kind, base_url=base_url, auth=build_auth(kind))

    if mode == "live":
        base_url = _base_url(kind)
        if base_url:
            return LiveHttpConnector(kind, base_url=base_url)
        return LiveConnector(kind)

    return build_fixture(kind)
