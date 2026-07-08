"""PHI masker tests — HIPAA Safe Harbor identifiers redacted; code sets preserved."""
import sys
import types

from hpp_agent_platform.phi import (
    MASK_FAILURE_PLACEHOLDER,
    ML_MASK_FALLBACK_FLAG,
    luhn_valid,
    mask,
)


def test_ssn_and_contact_masked():
    out = mask("Patient SSN 123-45-6789, phone (415) 555-0142, email a@b.com")
    assert "123-45-6789" not in out and "555-0142" not in out and "a@b.com" not in out


def test_mrn_and_claim_masked():
    out = mask("MRN-887766 claim CLM-2026-55810 account ACCT-77120")
    assert "887766" not in out and "55810" not in out


def test_card_luhn_masked():
    assert luhn_valid("4111111111111111")
    assert "4111111111111111" not in mask("card 4111 1111 1111 1111")


def test_code_sets_preserved():
    # ICD-10 / CPT / NPI must survive — they are non-PHI reference data.
    text = "CPT 99214 ICD-10 E11.9 rendered by NPI 1234567893"
    out = mask(text)
    assert "99214" in out and "E11.9" in out


def test_mask_idempotent_and_none_safe():
    once = mask("SSN 123-45-6789")
    assert mask(once) == once
    assert mask(None) == ""


def test_ml_hook_failure_fails_closed(monkeypatch):
    """Round-2 hardening: a raising ML NER hook must NEVER leak unmasked input.

    The deterministic Safe-Harbor output must stand, plus an audit-visible
    warning flag marking the degraded (fallback) masking path.
    """
    broken = types.ModuleType("hpp_agent_platform._ml_ner")

    def _boom(text):
        raise RuntimeError("ml engine down")

    broken.redact = _boom
    monkeypatch.setitem(sys.modules, "hpp_agent_platform._ml_ner", broken)
    monkeypatch.setenv("MASK_ENGINE", "ml")

    out = mask("Patient SSN 123-45-6789, email jane.doe@example.com")
    assert "123-45-6789" not in out
    assert "jane.doe@example.com" not in out
    assert "[SSN-REDACTED]" in out and "[EMAIL-REDACTED]" in out
    assert ML_MASK_FALLBACK_FLAG in out  # degradation is audit-visible


def test_ml_hook_total_failure_returns_placeholder(monkeypatch):
    """Last resort: if the deterministic fallback ALSO fails, redact everything."""
    from hpp_agent_platform import phi

    broken = types.ModuleType("hpp_agent_platform._ml_ner")

    def _boom(text):
        raise RuntimeError("ml engine down")

    broken.redact = _boom
    monkeypatch.setitem(sys.modules, "hpp_agent_platform._ml_ner", broken)

    def _also_boom(text):
        raise ValueError("regex engine hosed")

    monkeypatch.setattr(phi, "_apply_deterministic", _also_boom)
    out = phi._ml_mask("SSN 123-45-6789")
    assert out == MASK_FAILURE_PLACEHOLDER
    assert "123-45-6789" not in out
