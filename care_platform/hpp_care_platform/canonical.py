"""
Canonical record + adapters — one normalized view across systems of record.

A journey spans the EHR, the clearinghouse, the payer, patient accounting, and the
contact center, each with its own shape. The canonical record normalizes the fields
a journey reasons over (subject, plan, claim, encounter, status) so steps don't
re-derive them. Adapters map a connector payload into the canonical fields; they are
deliberately small and lossless-where-it-matters (they carry a `_raw` reference).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CanonicalSubject:
    subject_ref: str = ""           # patient_ref or member_ref
    member_ref: str = ""
    plan: str = ""
    coverage_active: Optional[bool] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalClaim:
    claim_ref: str = ""
    status: str = ""
    denial_codes: list = field(default_factory=list)
    cpt: list = field(default_factory=list)
    icd10: list = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


def subject_from_member(payload: Dict[str, Any]) -> CanonicalSubject:
    return CanonicalSubject(
        subject_ref=payload.get("member_ref", ""),
        member_ref=payload.get("member_ref", ""),
        plan=payload.get("plan", ""),
        coverage_active=payload.get("active"),
        raw=payload,
    )


def subject_from_patient(payload: Dict[str, Any]) -> CanonicalSubject:
    return CanonicalSubject(subject_ref=payload.get("patient_ref", ""), raw=payload)


def claim_from_payload(payload: Dict[str, Any]) -> CanonicalClaim:
    return CanonicalClaim(
        claim_ref=payload.get("claim_ref", ""),
        status=payload.get("status", ""),
        denial_codes=list(payload.get("denial_codes", []) or []),
        cpt=list(payload.get("cpt", []) or []),
        icd10=list(payload.get("icd10", []) or []),
        raw=payload,
    )
