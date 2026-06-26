"""
Connector framework — one interface, two implementations (fixture / live).

A *connector* is the typed adapter to a system of record (EHR/FHIR, patient
accounting, clearinghouse, payer portal, coding/encoder, clinical criteria, care
management, scheduling, registration, knowledge base, identity/consent, document
processing, contact center). Agents never call a vendor SDK directly: they call
the MCP gateway, which (after authorizing) calls a connector method. That keeps
three properties true:

  * One validated integration surface per system (the HIPAA/HITRUST scope is bounded).
  * Fixture mode runs the entire suite offline for demos, CI, and evals.
  * Live mode swaps in the real client behind the SAME method signatures, so no
    agent code changes between demo and production.

Add a system of record by registering a typed adapter in connectors/factory.py.
Method names here must match policy.TOOL_REGISTRY.
"""
from __future__ import annotations

import abc
from typing import Any, Dict


class Connector(abc.ABC):
    """Base class for all system-of-record connectors."""
    kind: str = "base"


class FixtureBackedConnector(Connector):
    """
    Deterministic, offline connector. Resolves <method> against a per-kind fixture
    table so the whole suite runs with no network, no credentials, no AWS account
    — the basis for demos, CI, and the governance eval harness.
    """

    def __init__(self, kind: str, table: Dict[str, Any]) -> None:
        self.kind = kind
        self._table = table

    def __getattr__(self, method: str) -> Any:
        table = self.__dict__.get("_table", {})
        if method not in table:
            raise AttributeError(f"connector {self.__dict__.get('kind')!r} has no method {method!r}")
        spec = table[method]

        def _call(**kwargs: Any) -> Any:
            return spec(kwargs) if callable(spec) else spec
        return _call
