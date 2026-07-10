"""
HAPI FHIR connector — a REAL external EHR data source (read-only, de-identified).

This is the "one real connector per vertical" build for HPP: it replaces the fixture
`ehr` source with the **public HAPI FHIR R4 test server** — a genuine, public,
**synthetic / de-identified** FHIR system of record. It proves the governed pattern
(deny-by-default gateway → scoped token → PHI masking → human gate → append-only
audit) against a real FHIR API instead of a fixture, and needs **no BAA** because the
public test server holds only synthetic test data.

  Endpoint : https://hapi.fhir.org/baseR4         (public HAPI FHIR R4 test server)
  Docs     : https://hapi.fhir.org/  ·  FHIR R4: https://hl7.org/fhir/R4/

Design contract (matches the `ehr` fixture methods so it is drop-in interchangeable
with the FixtureBackedConnector / LiveHttpConnector for kind='ehr'):

  * get_patient_summary / get_encounter / get_clinical_docs  -> READ real FHIR
    resources (Patient / Encounter / DocumentReference), mapped to the agent shapes.
  * draft_note / any submit_* / update_*                     -> NOT SUPPORTED. The
    public test server is treated as READ-ONLY; drafting to the chart and any claim /
    appeal submission target the customer's own **validated** EHR / clearinghouse and
    stay **human-gated**. Calling them raises — the correct, fail-closed behavior: the
    agent can read the real world but cannot write to it.

  * stdlib-only HTTP (urllib), explicit timeout, fail-closed (any error raises).
  * PHI masking still runs downstream on returned text even though the server is
    synthetic — the control is exercised, not assumed.

The regulated/PHI variant (AWS HealthLake FHIR under a BAA, or a payer/Availity
sandbox) is the same interface behind a different EHR_BASE_URL / EHR_SOURCE; swap the
adapter, keep the agent.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib import request as _urllib_request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .base import Connector

_DEFAULT_BASE = "https://hapi.fhir.org/baseR4"
_TIMEOUT = 20

# ehr methods that mutate a system of record -> unsupported against the public server.
_WRITE_METHODS = {"draft_note", "submit_claim", "submit_appeal", "submit_pa",
                  "update_care_plan", "create_registration"}


def _api_key() -> str:
    """Optional bearer token for a secured FHIR endpoint (env or Secrets Manager).
    The public HAPI test server needs none; a customer sandbox / HealthLake does."""
    key = os.getenv("EHR_API_KEY", "")
    if key:
        return key
    try:
        from hpp_agent_platform.secrets import get_secret
        return get_secret("ehr_api_key", default="") or ""
    except Exception:
        return ""


def _human_name(names: List[Dict[str, Any]]) -> str:
    if not names:
        return "Unknown"
    n = names[0]
    if n.get("text"):
        return n["text"]
    given = " ".join(n.get("given", []) or [])
    return f"{given} {n.get('family', '')}".strip() or "Unknown"


class HapiFhirEhrConnector(Connector):
    """Real, read-only FHIR R4 EHR connector (kind='ehr'). Public synthetic data."""

    kind = "ehr"
    source = "HAPI FHIR R4 public test server (synthetic, de-identified)"

    def __init__(self, base_url: str = "", api_key: str = "") -> None:
        self._base_url = (base_url or os.getenv("EHR_BASE_URL", _DEFAULT_BASE)).rstrip("/")
        self._api_key = api_key  # empty -> resolved lazily

    # -- HTTP -----------------------------------------------------------------
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET {base}/{path}?{params} as FHIR JSON. Fail-closed: any error raises."""
        headers = {"Accept": "application/fhir+json"}
        key = self._api_key or _api_key()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        qs = f"?{urlencode(params)}" if params else ""
        url = f"{self._base_url}/{path.lstrip('/')}{qs}"
        req = _urllib_request.Request(url, headers=headers, method="GET")
        try:
            with _urllib_request.urlopen(req, timeout=_TIMEOUT) as resp:  # nosec B310 — operator-config URL
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                return {"resourceType": "Bundle", "entry": []}
            raise RuntimeError(f"FHIR API error [{exc.code}] for {url}: {exc}") from exc
        except (URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"FHIR API call failed for {url}: {exc}") from exc

    @staticmethod
    def _entries(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [e.get("resource", {}) for e in (bundle.get("entry") or []) if e.get("resource")]

    # -- Mapping FHIR resources -> agent shapes -------------------------------
    @staticmethod
    def _map_patient(p: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "patient_ref": p.get("id", ""),
            "name": _human_name(p.get("name", []) or []),
            "sex": p.get("gender", "unknown"),
            "dob": p.get("birthDate", ""),
            "active": bool(p.get("active", True)),
            "source": HapiFhirEhrConnector.source,
        }

    @staticmethod
    def _map_encounter(e: Dict[str, Any]) -> Dict[str, Any]:
        cls = (e.get("class") or {})
        period = e.get("period") or {}
        types = [c.get("text") or (c.get("coding", [{}])[0] or {}).get("display")
                 for c in (e.get("type") or [])]
        return {
            "encounter_ref": e.get("id", ""),
            "status": e.get("status", ""),
            "class": cls.get("code") or cls.get("display", ""),
            "type": [t for t in types if t],
            "start": period.get("start", ""),
            "end": period.get("end", ""),
        }

    @staticmethod
    def _map_document(d: Dict[str, Any]) -> Dict[str, Any]:
        typ = d.get("type") or {}
        title = typ.get("text") or (typ.get("coding", [{}])[0] or {}).get("display") or "Clinical document"
        return {
            "doc_id": d.get("id", ""),
            "title": title,
            "status": d.get("status", ""),
            "date": d.get("date", ""),
            "description": d.get("description", ""),
        }

    # -- ehr connector interface (READ) ---------------------------------------
    def get_patient_summary(self, patient_ref: Optional[str] = None,
                            patient_id: Optional[str] = None, **_: Any) -> Dict[str, Any]:
        """READ a real Patient. By id if given, else the most recent Patient."""
        pid = patient_ref or patient_id
        if pid:
            res = self._get(f"Patient/{pid}")
            if res.get("resourceType") == "Patient":
                return self._map_patient(res)
        bundle = self._get("Patient", {"_count": 1, "_sort": "-_lastUpdated"})
        pts = self._entries(bundle)
        if not pts:
            return {"patient_ref": pid or "", "status": "NOT_FOUND", "source": self.source}
        return self._map_patient(pts[0])

    def get_encounter(self, encounter_ref: Optional[str] = None,
                      patient_ref: Optional[str] = None, **_: Any) -> Dict[str, Any]:
        """READ a real Encounter by id, or the most recent for a patient."""
        if encounter_ref:
            res = self._get(f"Encounter/{encounter_ref}")
            if res.get("resourceType") == "Encounter":
                return self._map_encounter(res)
        params: Dict[str, Any] = {"_count": 1, "_sort": "-date"}
        if patient_ref:
            params["patient"] = patient_ref
        encs = self._entries(self._get("Encounter", params))
        if not encs:
            return {"encounter_ref": encounter_ref or "", "status": "NOT_FOUND", "source": self.source}
        return self._map_encounter(encs[0])

    def get_clinical_docs(self, patient_ref: Optional[str] = None,
                          limit: int = 5, **_: Any) -> Dict[str, Any]:
        """READ real DocumentReference resources grounding a denial appeal."""
        params: Dict[str, Any] = {"_count": max(1, min(limit, 20)), "_sort": "-date"}
        if patient_ref:
            params["patient"] = patient_ref
        docs = [self._map_document(d) for d in self._entries(self._get("DocumentReference", params))]
        return {"patient_ref": patient_ref or "", "documents": docs,
                "count": len(docs), "source": self.source}

    # -- Writes are intentionally unsupported (read-only public source) -------
    def __getattr__(self, method: str) -> Any:
        if method.startswith("_"):
            raise AttributeError(method)
        if method in _WRITE_METHODS:
            def _blocked(**_kw: Any) -> Any:
                raise NotImplementedError(
                    f"'{method}' is not supported against the public FHIR test server. "
                    "Writes (chart notes, claim/appeal submission) target the customer's "
                    "validated EHR / clearinghouse and remain human-gated. Use the sandbox "
                    "connector (EHR_BASE_URL) or fixtures for write paths."
                )
            return _blocked
        raise AttributeError(method)
