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
    (Amazon Comprehend Medical / Presidio) can be layered behind MASK_ENGINE=ml.
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


def mask(text: Optional[str]) -> str:
    """
    Mask PHI/PII identifiers in free text for safe logging and audit.

    Idempotent; returns "" for None. Set MASK_ENGINE=ml to additionally run an
    optional NER engine (Amazon Comprehend Medical / Presidio — not bundled).
    """
    if not text:
        return ""
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

    if os.getenv("MASK_ENGINE", "").strip().lower() == "ml":
        out = _ml_mask(out)
    return out


def _ml_mask(text: str) -> str:
    """Optional ML NER hook (Amazon Comprehend Medical / Presidio). No-op if absent."""
    try:  # pragma: no cover - optional dependency path
        from hpp_agent_platform._ml_ner import redact  # type: ignore

        return redact(text)
    except Exception:
        return text
