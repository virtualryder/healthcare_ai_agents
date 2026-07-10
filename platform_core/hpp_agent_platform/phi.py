"""
PHI / PII masking — HIPAA data-protection support at the log/audit boundary.

Logs, traces, and audit records in a provider or health-plan workload must never
contain raw protected health information. This module gives every agent one
masking function applied at log/audit boundaries. It targets the identifier
families enumerated by the HIPAA Privacy Rule **Safe Harbor** de-identification
standard (45 CFR 164.514(b)(2)) that are most likely to appear in claims,
clinical notes, prior-auth packets, eligibility responses, and member calls:

    * US SSN                          123-45-6789      (PII)
    * Medical record number (MRN)     MRN-prefixed     (Safe Harbor #7)
    * Health-plan beneficiary / member ID              (Safe Harbor #8)
    * Account / claim numbers         ACCT-/CLM-/CLAIM- (Safe Harbor #9-10)
    * Dates more specific than year   (DOB, admit/discharge, service dates) (#3)
    * Email addresses, phone/fax numbers               (Safe Harbor #4-6)
    * Street addresses (number + street-type)          (Safe Harbor #1)
    * Payment card numbers (Luhn-validated; PCI for patient-pay flows)
    * Device identifiers / serial numbers (#13)

NOT masked: the National Provider Identifier (NPI) and standard code sets
(ICD-10, CPT, HCPCS, DRG) — these are non-PHI reference data the agents must
reason over and cite. Masking them would break grounding and coding validation.

Design notes:
  * Deterministic and dependency-free (regex + Luhn). An optional ML NER pass
    can be layered on: the AWS-native Amazon Comprehend Medical DetectPHI engine
    (PHI_ENGINE=comprehend_medical), or a generic pluggable NER hook
    (MASK_ENGINE=ml). Both are strictly additive to the deterministic pass.
  * Conservative: over-masking a log line is acceptable; leaking PHI is not.
  * mask() is idempotent and safe to call on already-masked text.

This is the de-identification *control point*; it does NOT by itself constitute a
Safe Harbor or Expert Determination de-identification of a dataset, which is
governed by the customer's privacy and security officers and their BAA.
"""
from __future__ import annotations

import os
import re
from typing import Optional

_TRUTHY = {"1", "true", "yes", "on"}


class RealDataMaskingError(RuntimeError):
    """
    Raised when real-data mode (ALLOW_REAL_DATA) is enabled but the mandatory NER
    engine is not selected/available. The masker FAILS CLOSED rather than silently
    degrading to the regex-only deterministic pass — which does NOT mask free-text
    patient NAMES (HIPAA Safe Harbor identifier #1) — so real PHI is never written
    to a log/prompt/audit with names left in the clear.
    """


def _real_data_mode() -> bool:
    """True when the caller has asserted this text may contain REAL PHI."""
    return os.getenv("ALLOW_REAL_DATA", "").strip().lower() in _TRUTHY


# ── Identifier patterns (order matters: most specific first) ──────────────────
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
# Medical record number, member/beneficiary ID, account / claim numbers.
# Allow internal hyphens so multi-segment IDs (CLM-2026-55810) mask in full.
_MRN_RE = re.compile(r"\b(?:MRN|MR|MEMBER|MBR|MBI|HICN|SUBSCRIBER|BENE)[-#:\s]?[A-Z0-9][A-Z0-9-]{3,}\b", re.I)
_ACCT_RE = re.compile(
    r"\b(?:ACCT|ACCOUNT|CLM|CLAIM|CASE|AUTH|APL|REF|ENC|ENCOUNTER|FIN|GUAR|GRV|INT)[-_ #]?[A-Z0-9][A-Z0-9-]{2,}\b",
    re.I,
)
# Dates more specific than a bare year (YYYY-MM-DD, MM/DD/YYYY, DD-Mon-YYYY)
_DATE_RE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"\d{1,2}[-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]\d{2,4})\b",
    re.I,
)
# Street address: number + name + street-type suffix
_ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+(?:[A-Za-z0-9.'-]+\s+){0,4}"
    r"(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Ln|Lane|Dr|Drive|Ct|Court|"
    r"Way|Pl|Place|Ter|Terrace|Cir|Circle|Hwy|Highway|Pkwy|Parkway)\b\.?",
    re.I,
)
# 13-19 digit runs that pass Luhn -> payment cards (patient-pay / PCI)
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
# Long bare digit runs (>=9) -> account / member / device-style identifiers
_LONGNUM_RE = re.compile(r"\b\d{9,}\b")


def luhn_valid(number: str) -> bool:
    """Return True if the digit string passes the Luhn checksum."""
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _mask_cards(text: str) -> str:
    def repl(m: "re.Match") -> str:
        raw = m.group(0)
        return "[CARD-REDACTED]" if luhn_valid(raw) else raw
    return _CARD_RE.sub(repl, text)


# ── Fail-closed markers (round-2 hardening) ──────────────────────────────────
ML_MASK_FALLBACK_FLAG = "[PHI-MASK-WARNING: ML-ENGINE-FAILED; DETERMINISTIC-FALLBACK-APPLIED]"
MASK_FAILURE_PLACEHOLDER = "[REDACTED: PHI-MASKING-FAILURE]"


def _apply_deterministic(text: str) -> str:
    """The deterministic regex/Safe-Harbor pass — the always-on masking baseline."""
    out = str(text)
    out = _SSN_RE.sub("[SSN-REDACTED]", out)
    out = _EMAIL_RE.sub("[EMAIL-REDACTED]", out)
    out = _MRN_RE.sub("[MRN-REDACTED]", out)
    out = _ACCT_RE.sub("[ACCT-REDACTED]", out)
    out = _mask_cards(out)
    out = _PHONE_RE.sub("[PHONE-REDACTED]", out)
    out = _ADDRESS_RE.sub("[ADDRESS-REDACTED]", out)
    out = _DATE_RE.sub("[DATE-REDACTED]", out)
    out = _LONGNUM_RE.sub("[ID-REDACTED]", out)
    return out


def _ml_engine_selected() -> bool:
    """True when an optional ML NER pass should run in addition to deterministic."""
    if os.getenv("MASK_ENGINE", "").strip().lower() == "ml":
        return True
    if os.getenv("PHI_ENGINE", "").strip().lower() == "comprehend_medical":
        return True
    return False


def mask(text: Optional[str]) -> str:
    """
    Mask PHI/PII identifiers in free text for safe logging and audit.

    Idempotent; returns "" for None. Two opt-in ML NER routes layer an additional
    pass on top of the always-on deterministic Safe-Harbor masker:
    PHI_ENGINE=comprehend_medical (Amazon Comprehend Medical DetectPHI, HIPAA-
    eligible, reached over the regional API / PrivateLink under the AWS BAA) or
    MASK_ENGINE=ml (a generic pluggable NER hook). The ML pass is strictly
    additive and fail-closed: the deterministic Safe-Harbor pass ALWAYS runs
    (before and after the ML pass — belt and suspenders), and if the ML pass
    fails the deterministic output stands (with an audit-visible
    ML_MASK_FALLBACK_FLAG). Unmasked input is never returned.
    """
    if not text:
        return ""
    strict = _real_data_mode()
    # Real-data mode: the deterministic regex pass does NOT mask free-text patient
    # names (Safe Harbor #1). Require an NER engine and fail closed if absent, rather
    # than silently emitting regex-only output that could leak a name.
    if strict and not _ml_engine_selected():
        raise RealDataMaskingError(
            "ALLOW_REAL_DATA is set but no NER engine is selected "
            "(set MASK_ENGINE=ml or PHI_ENGINE=comprehend_medical). Refusing to mask "
            "real PHI with the regex-only pass, which does not mask free-text names."
        )
    out = _apply_deterministic(str(text))
    if _ml_engine_selected():
        out = _ml_mask(out, strict=strict)
    return out


def _resolve_ml_redactor():
    """
    Resolve the redaction callable for the selected ML engine.
    PHI_ENGINE=comprehend_medical takes precedence and binds the AWS-native
    Comprehend Medical redact; otherwise the generic _ml_ner.redact hook is used.
    Raises ImportError if the selected engine's dependency is absent.
    """
    if os.getenv("PHI_ENGINE", "").strip().lower() == "comprehend_medical":
        from hpp_agent_platform.comprehend_medical import redact  # type: ignore
        return redact
    from hpp_agent_platform._ml_ner import redact  # type: ignore
    return redact


def _ml_mask(text: str, strict: bool = False) -> str:
    """
    Optional ML NER hook (Amazon Comprehend Medical / generic NER) — FAIL-CLOSED.
    On the success path the deterministic Safe-Harbor pass is re-applied AFTER
    the ML redaction (Comprehend Medical + regex together, never one alone).

    Demo/default (strict=False): engine absent -> deterministic output stands;
    engine raises -> deterministic fallback + ML_MASK_FALLBACK_FLAG; deterministic
    also raises -> MASK_FAILURE_PLACEHOLDER. The unmasked input is NEVER returned.

    Real-data (strict=True, ALLOW_REAL_DATA): a missing or failing NER engine is a
    hard error (RealDataMaskingError) — we must not fall back to regex-only, which
    would leave free-text names in the clear.
    """
    try:
        redact = _resolve_ml_redactor()
    except ImportError as exc:  # optional dependency absent — expected in most deploys
        if strict:
            raise RealDataMaskingError(
                "real-data mode requires the NER engine, but its dependency is not importable"
            ) from exc
        return _apply_deterministic(text)
    try:
        return _apply_deterministic(redact(text))
    except Exception as exc:
        if strict:
            raise RealDataMaskingError(f"real-data NER pass failed: {exc}") from exc
        try:
            return f"{_apply_deterministic(text)} {ML_MASK_FALLBACK_FLAG}"
        except Exception:
            return MASK_FAILURE_PLACEHOLDER
