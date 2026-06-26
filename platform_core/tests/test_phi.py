"""PHI masker tests — HIPAA Safe Harbor identifiers redacted; code sets preserved."""
from hpp_agent_platform.phi import mask, luhn_valid


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
