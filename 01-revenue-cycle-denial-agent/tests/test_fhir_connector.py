"""
Tests for the HAPI FHIR (R4) real EHR connector — HPP's "one real connector" build.

Two layers:
  * Offline/deterministic (default): monkeypatch the connector's HTTP with recorded
    real-structure FHIR cassettes. No network. CI source of truth — covers mapping,
    the governed round-trip (allow reads / withhold writes), fail-closed writes, and
    fail-closed PHI masking.
  * Opt-in live smoke (RUN_LIVE_FHIR=1): actually calls https://hapi.fhir.org/baseR4
    and asserts the same governed read against real synthetic data. Skipped by default
    so CI needs no network.
"""
import json
import os
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))

from hpp_agent_platform.connectors import fhir  # noqa: E402
from hpp_agent_platform.connectors.factory import get_connector  # noqa: E402
from hpp_agent_platform.mcp_gateway.gateway import MCPGateway  # noqa: E402
from hpp_agent_platform.mcp_gateway import policy as _policy  # noqa: E402
from hpp_agent_platform.phi import mask  # noqa: E402

_FIX = AGENT / "tests" / "fixtures"
_PATIENT = json.loads((_FIX / "hapifhir_patient.json").read_text(encoding="utf-8"))
_PATIENT_BUNDLE = json.loads((_FIX / "hapifhir_patient_bundle.json").read_text(encoding="utf-8"))
_DOCS_BUNDLE = json.loads((_FIX / "hapifhir_docs_bundle.json").read_text(encoding="utf-8"))

HERO_AGENT = "01-revenue-cycle-denial"
_ROLE_CLAIM = os.getenv("AUTH_ROLE_CLAIM", "custom:hpp_role")


@pytest.fixture(autouse=True)
def _governed_mode(monkeypatch):
    monkeypatch.setenv("CONNECTOR_MODE", "live")
    monkeypatch.setenv("EHR_SOURCE", "hapifhir")


def _route(monkeypatch, mapping):
    """Monkeypatch the connector HTTP so a (path-prefix -> cassette) map is served offline."""
    def _fake_get(self, path, params=None):
        for prefix, payload in mapping.items():
            if path.startswith(prefix):
                return payload
        return {"resourceType": "Bundle", "entry": []}
    monkeypatch.setattr(fhir.HapiFhirEhrConnector, "_get", _fake_get)


def _entitled_role_for(tool):
    """Pick a role whose entitlement ∩ the hero agent's grant includes `tool` (self-adjusting)."""
    grants = _policy.AGENT_TOOL_GRANTS[HERO_AGENT]
    for role, ent in _policy.ROLE_ENTITLEMENTS.items():
        if tool in grants and tool in ent:
            return role
    raise AssertionError(f"no role entitled to {tool}")


# ── Mapping ──────────────────────────────────────────────────────────────────

def test_maps_real_patient_resource():
    rec = fhir.HapiFhirEhrConnector._map_patient(_PATIENT)
    assert rec["patient_ref"] == "example-1284321"
    assert rec["name"] == "Peter James Chalmers"
    assert rec["sex"] == "male" and rec["dob"] == "1974-12-25"
    assert "HAPI FHIR" in rec["source"]


def test_get_patient_summary_by_id(monkeypatch):
    _route(monkeypatch, {"Patient/example-1284321": _PATIENT})
    rec = fhir.HapiFhirEhrConnector().get_patient_summary(patient_ref="example-1284321")
    assert rec["patient_ref"] == "example-1284321" and rec["sex"] == "male"


def test_get_clinical_docs_returns_documents(monkeypatch):
    _route(monkeypatch, {"DocumentReference": _DOCS_BUNDLE})
    out = fhir.HapiFhirEhrConnector().get_clinical_docs(patient_ref="example-1284321")
    assert out["count"] == 2
    titles = [d["title"] for d in out["documents"]]
    assert "Discharge summary" in titles and "Consult note" in titles


# ── Writes are fail-closed (read-only public source) ─────────────────────────

def test_draft_note_raises():
    with pytest.raises(NotImplementedError):
        fhir.HapiFhirEhrConnector().draft_note(patient_ref="x", text="y")


def test_submit_appeal_raises():
    with pytest.raises(NotImplementedError):
        fhir.HapiFhirEhrConnector().submit_appeal(claim_ref="CLM-1")


# ── Factory routing (guarded switch) ─────────────────────────────────────────

def test_factory_routes_to_fhir_when_switch_set():
    assert type(get_connector("ehr", "live")).__name__ == "HapiFhirEhrConnector"


def test_factory_ignores_fhir_without_switch(monkeypatch):
    monkeypatch.delenv("EHR_SOURCE", raising=False)
    # default fixture mode must be unchanged when the switch is absent
    monkeypatch.setenv("CONNECTOR_MODE", "fixture")
    assert type(get_connector("ehr")).__name__ != "HapiFhirEhrConnector"


# ── Governed round-trip through the real gateway ─────────────────────────────

def test_governed_read_allowed_write_gated(monkeypatch):
    _route(monkeypatch, {"DocumentReference": _DOCS_BUNDLE, "Patient": _PATIENT_BUNDLE})
    gw = MCPGateway()
    role = _entitled_role_for("ehr.get_clinical_docs")
    claims = {"sub": "u-analyst", _ROLE_CLAIM: role}
    read = gw.invoke(user_claims=claims, agent_id=HERO_AGENT,
                     tool="ehr.get_clinical_docs", args={"patient_ref": "example-1284321"})
    assert read.allowed and read.decision == "ALLOW"
    assert read.result["count"] == 2 and read.audit_id

    # draft_note is consequential -> withheld from the agent (human-gated), not auto-run
    write = gw.invoke(user_claims=claims, agent_id=HERO_AGENT,
                      tool="ehr.draft_note", args={"patient_ref": "example-1284321"})
    assert not write.allowed


def test_least_privilege_denies_unentitled_role(monkeypatch):
    _route(monkeypatch, {"DocumentReference": _DOCS_BUNDLE})
    gw = MCPGateway()
    r = gw.invoke(user_claims={"sub": "x", _ROLE_CLAIM: "NO_SUCH_ROLE"},
                  agent_id=HERO_AGENT, tool="ehr.get_clinical_docs",
                  args={"patient_ref": "example-1284321"})
    assert not r.allowed and r.decision == "DENY"


# ── Fail-closed PHI masking on ingested text ─────────────────────────────────

def test_phi_masking_failclosed_on_ingested_text(monkeypatch):
    _route(monkeypatch, {"DocumentReference": _DOCS_BUNDLE})
    out = fhir.HapiFhirEhrConnector().get_clinical_docs(patient_ref="example-1284321")
    # the server is synthetic; stress the control with injected identifiers.
    stressed = json.dumps(out) + " member jane.doe@example.com SSN 123-45-6789"
    masked = mask(stressed)
    assert "123-45-6789" not in masked
    assert "jane.doe@example.com" not in masked


# ── Opt-in live smoke against the real HAPI FHIR server ──────────────────────

@pytest.mark.skipif(os.getenv("RUN_LIVE_FHIR", "") not in ("1", "true", "yes"),
                    reason="set RUN_LIVE_FHIR=1 to hit the real hapi.fhir.org")
def test_live_fhir_governed_read():
    gw = MCPGateway()
    role = _entitled_role_for("ehr.get_clinical_docs")
    r = gw.invoke(user_claims={"sub": "u-analyst", _ROLE_CLAIM: role},
                  agent_id=HERO_AGENT, tool="ehr.get_clinical_docs", args={})
    assert r.allowed and isinstance(r.result.get("documents"), list)
    assert r.audit_id
