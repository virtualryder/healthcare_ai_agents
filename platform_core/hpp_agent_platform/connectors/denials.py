"""
Denials connector SCAFFOLD (kind='denials') — read-only, fail-closed.

HONEST FRAMING. Unlike an open, PHI-free public dataset, there is **no clean
public denial API**: real claim-denial data is the customer's remittance advice,
delivered as **X12 835** (electronic remittance) and **X12 277** (claim status)
through their clearinghouse (e.g. Availity, Change Healthcare/Optum) under a BAA,
or as **AWS HealthLake Claim / ClaimResponse (FHIR)** resources in the customer's
HIPAA-eligible data store. That source is **engagement-owned** and PHI-bearing.

This scaffold therefore follows the same governed contract as the other
connectors (connectors/base.py Connector; drop-in with the factory):

  * FIXTURE mode  -> returns LABELED SYNTHETIC denial records (the exact golden
    cases the scored eval harness uses — governance/evals/gen_golden_denial.py),
    so the whole workflow, demos, CI, and evals run offline with **no PHI, no
    credentials, no BAA**.
  * LIVE / SANDBOX mode -> every READ raises NotImplementedError pointing to the
    real engagement source (X12 835/277 clearinghouse feed, or HealthLake
    ClaimResponse FHIR under a BAA). The integration is deliberately NOT stubbed
    with a fake endpoint — implementing it is scoped customer work.
  * WRITES / consequential actions (claim resubmission, appeal submission) ALWAYS
    raise NotImplementedError, in every mode: submission is **human-gated** and is
    performed by a biller / denials specialist against the customer's validated
    system — never by the agent, never against a fixture.

Mirrors the read-only / fail-closed / explicit-mapping style of the reference
external connector so it is drop-in interchangeable behind the MCP gateway.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Connector

# Repo-relative golden set the fixture reuses (single source of truth: the eval
# generator). Resolved lazily and cached; falls back to build_cases() import,
# then to a minimal embedded stub, so the connector never hard-fails offline.
_GOLDEN = Path(__file__).resolve().parents[3] / "governance" / "evals" / "golden" / "agent01_denial_scored.json"

_LIVE_SOURCE = (
    "the customer's X12 835 (electronic remittance) / X12 277 (claim status) feed via their "
    "clearinghouse, or AWS HealthLake Claim/ClaimResponse (FHIR) under a BAA"
)


def _load_synthetic() -> List[Dict[str, Any]]:
    """Load the labeled synthetic denial records (fixture data)."""
    if _GOLDEN.exists():
        try:
            cases = json.loads(_GOLDEN.read_text(encoding="utf-8"))["cases"]
            return [dict(c["denial"], _id=c["id"], _gold=c["gold"]) for c in cases]
        except Exception:  # pragma: no cover - corrupt file; fall through
            pass
    try:  # generator import (repo root on path)
        from governance.evals.gen_golden_denial import build_cases  # type: ignore
        return [dict(c["denial"], _id=c["id"], _gold=c["gold"]) for c in build_cases()]
    except Exception:  # pragma: no cover - last-resort embedded stub
        return [{
            "_id": "DN-0001", "claim_id": "CLM-2026-0001", "payer": "BlueChoice PPO",
            "denial_codes": ["CO-197"], "remark_codes": ["N20"], "service": "99214",
            "cpt": ["99214"], "icd10": ["E11.9"], "billed": 312.00, "allowed": 0.0,
            "service_date": "2026-06-12",
            "_gold": {"root_cause": "authorization", "recoverable": True},
        }]


class DenialsConnector(Connector):
    """
    Claims-denial system-of-record adapter (kind='denials').

    Fixture mode reads labeled synthetic denials; live/sandbox reads raise
    NotImplementedError pointing to the real X12 835/277 or HealthLake source;
    writes are human-gated and raise in every mode.
    """

    kind = "denials"
    source_fixture = "labeled synthetic denial records (offline, non-PHI)"
    source_live = f"NOT IMPLEMENTED — {_LIVE_SOURCE}"

    def __init__(self, mode: str = "fixture") -> None:
        self.mode = (mode or "fixture").strip().lower()
        self._records: Optional[List[Dict[str, Any]]] = None

    # -- helpers --------------------------------------------------------------
    def _fixture_records(self) -> List[Dict[str, Any]]:
        if self._records is None:
            self._records = _load_synthetic()
        return self._records

    def _require_read(self, method: str) -> None:
        """Reads are supported ONLY in fixture mode; live/sandbox is engagement work."""
        if self.mode == "fixture":
            return
        raise NotImplementedError(
            f"DenialsConnector.{method} is not implemented for mode={self.mode!r}. "
            f"Real denial data is {_LIVE_SOURCE}. There is no clean public, PHI-free "
            f"denial API, so this read is intentionally not stubbed against a fake endpoint — "
            f"implement the clearinghouse/HealthLake adapter as scoped engagement work, or set "
            f"CONNECTOR_MODE=fixture for the offline synthetic set."
        )

    @staticmethod
    def _public(rec: Dict[str, Any]) -> Dict[str, Any]:
        """Return the denial record without the eval-only gold annotations."""
        return {k: v for k, v in rec.items() if k not in ("_gold",)}

    # -- reads (fixture-backed) -----------------------------------------------
    def get_denial(self, claim_id: Optional[str] = None, denial_code: Optional[str] = None,
                   payer: Optional[str] = None, **_: Any) -> Dict[str, Any]:
        """READ one denial (by claim_id, else first matching filter, else newest)."""
        self._require_read("get_denial")
        recs = self._fixture_records()
        for r in recs:
            if claim_id and r.get("claim_id") == claim_id:
                return self._public(r)
        for r in recs:
            if (not denial_code or denial_code in r.get("denial_codes", [])) and \
               (not payer or r.get("payer") == payer):
                return self._public(r)
        return {"claim_id": claim_id or "", "status": "NOT_FOUND", "valid": False,
                "source": self.source_fixture}

    def list_denials(self, payer: Optional[str] = None, denial_code: Optional[str] = None,
                     limit: int = 50, **_: Any) -> List[Dict[str, Any]]:
        """READ a filtered list of denials (synthetic worklist)."""
        self._require_read("list_denials")
        out: List[Dict[str, Any]] = []
        for r in self._fixture_records():
            if payer and r.get("payer") != payer:
                continue
            if denial_code and denial_code not in r.get("denial_codes", []):
                continue
            out.append(self._public(r))
            if len(out) >= max(1, limit):
                break
        return out

    def search_duplicates(self, claim_id: Optional[str] = None, payer: Optional[str] = None,
                          denial_code: Optional[str] = None, service: Optional[str] = None,
                          exclude_claim_id: Optional[str] = None, limit: int = 5,
                          **_: Any) -> List[Dict[str, Any]]:
        """
        Find candidate duplicate denials by shared payer + denial code + service.
        match_score is a transparent heuristic (payer 0.34 / code 0.33 / service
        0.33); real duplicate detection is a customer-validated algorithm.
        """
        self._require_read("search_duplicates")
        exclude_claim_id = exclude_claim_id or claim_id
        out: List[Dict[str, Any]] = []
        for r in self._fixture_records():
            cid = r.get("claim_id", "")
            if exclude_claim_id and cid == exclude_claim_id:
                continue
            score = (0.34 if payer and r.get("payer") == payer else 0.0) \
                + (0.33 if denial_code and denial_code in r.get("denial_codes", []) else 0.0) \
                + (0.33 if service and r.get("service") == service else 0.0)
            if score <= 0:
                continue
            out.append({"claim_id": cid, "payer": r.get("payer"),
                        "denial_codes": r.get("denial_codes", []), "service": r.get("service"),
                        "match_score": round(score, 2)})
            if len(out) >= max(1, limit):
                break
        out.sort(key=lambda x: x["match_score"], reverse=True)
        return out

    # -- writes are intentionally unsupported (human-gated, every mode) -------
    def resubmit_claim(self, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError(
            "Claim resubmission is a consequential, HUMAN-GATED action. A biller resubmits "
            "against the customer's validated clearinghouse/practice-management system — never "
            "the agent, never against this connector. The agent may recommend CORRECT_AND_RESUBMIT; "
            "a human performs the submission."
        )

    def submit_appeal(self, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError(
            "Appeal submission is a consequential, HUMAN-GATED action performed by a denials "
            "specialist against the payer, after review. The agent drafts a grounded appeal; a "
            "human approves and submits it. This connector does not submit."
        )
