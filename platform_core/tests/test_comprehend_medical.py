"""
Amazon Comprehend Medical PHI engine tests — mocked client, NO real AWS calls.

Verifies the belt-and-suspenders contract wired into phi.mask():
  (a) Comprehend Medical entities are redacted AND the deterministic Safe-Harbor
      pass also masks its identifier families (both engines contribute);
  (b) a ClientError from Comprehend Medical fails CLOSED — the deterministic
      masking still applies, no PHI survives, and no exception leaks unmasked
      text (the audit-visible fallback flag is present instead).

A fake ``comprehendmedical`` client is injected via monkeypatching
``comprehend_medical._client`` so the tests never touch AWS.
"""
from hpp_agent_platform import comprehend_medical as cm
from hpp_agent_platform.phi import ML_MASK_FALLBACK_FLAG, mask


class _FakeClientError(Exception):
    """Stand-in for botocore.exceptions.ClientError (avoids a botocore import)."""


class _FakeCMClientEntities:
    """Fake comprehendmedical client whose detect_phi returns fixed entities."""

    def __init__(self, entities):
        self._entities = entities

    def detect_phi(self, Text):  # noqa: N803 (boto3 param name)
        return {"Entities": self._entities}


class _FakeCMClientRaises:
    """Fake comprehendmedical client whose detect_phi raises a ClientError."""

    def detect_phi(self, Text):  # noqa: N803
        raise _FakeClientError("AccessDeniedException: DetectPHI denied")


def _entities_for(text):
    """Build DetectPHI-shaped entities for the NAME and AGE spans in text."""
    name = "John Q. Public"
    age = "88-year-old"
    ents = []
    if name in text:
        b = text.index(name)
        ents.append(
            {"BeginOffset": b, "EndOffset": b + len(name), "Type": "NAME", "Score": 0.99}
        )
    if age in text:
        b = text.index(age)
        ents.append(
            {"BeginOffset": b, "EndOffset": b + len(age), "Type": "AGE", "Score": 0.97}
        )
    return ents


def test_comprehend_medical_entities_and_deterministic_both_applied(monkeypatch):
    """(a) CM entities redacted AND deterministic patterns also masked."""
    text = (
        "88-year-old John Q. Public, SSN 123-45-6789, "
        "email jane.doe@example.com, MRN-887766"
    )
    monkeypatch.setenv("PHI_ENGINE", "comprehend_medical")
    monkeypatch.setattr(cm, "_client", lambda region=None: _FakeCMClientEntities(_entities_for(text)))

    out = mask(text)

    # Comprehend Medical spans redacted with [<TYPE>-REDACTED]:
    assert "John Q. Public" not in out
    assert "[NAME-REDACTED]" in out
    assert "88-year-old" not in out
    assert "[AGE-REDACTED]" in out
    # Deterministic Safe-Harbor pass ALSO masked its families:
    assert "123-45-6789" not in out and "[SSN-REDACTED]" in out
    assert "jane.doe@example.com" not in out and "[EMAIL-REDACTED]" in out
    assert "887766" not in out and "[MRN-REDACTED]" in out
    # No degradation flag on the success path.
    assert ML_MASK_FALLBACK_FLAG not in out


def test_comprehend_medical_client_error_fails_closed(monkeypatch):
    """(b) A ClientError fails closed: deterministic masking still applied,
    no PHI survives, no exception leaks unmasked text."""
    text = "Patient SSN 123-45-6789, email jane.doe@example.com, phone (415) 555-0142"
    monkeypatch.setenv("PHI_ENGINE", "comprehend_medical")
    monkeypatch.setattr(cm, "_client", lambda region=None: _FakeCMClientRaises())

    # Must NOT raise — fail closed to the deterministic fallback.
    out = mask(text)

    assert "123-45-6789" not in out and "[SSN-REDACTED]" in out
    assert "jane.doe@example.com" not in out and "[EMAIL-REDACTED]" in out
    assert "555-0142" not in out and "[PHONE-REDACTED]" in out
    # Degradation is audit-visible.
    assert ML_MASK_FALLBACK_FLAG in out


def test_comprehend_medical_boto3_error_fails_closed(monkeypatch):
    """boto3 missing/failing at client build -> raises -> mask() fails closed.

    _client() raising (e.g. ImportError for boto3, or a construction error)
    propagates out of redact() as a non-ImportError to phi._ml_mask's runtime
    branch, so the deterministic fallback + audit-visible flag are applied and
    no unmasked text leaks.
    """
    text = "SSN 123-45-6789 for John Q. Public"
    monkeypatch.setenv("PHI_ENGINE", "comprehend_medical")

    def _boom(region=None):
        raise RuntimeError("boto3/comprehendmedical client unavailable")

    monkeypatch.setattr(cm, "_client", _boom)

    out = mask(text)  # must not raise
    assert "123-45-6789" not in out and "[SSN-REDACTED]" in out
    assert ML_MASK_FALLBACK_FLAG in out


def test_below_threshold_entities_not_redacted_by_cm(monkeypatch):
    """Low-confidence CM entities are skipped by CM, but deterministic pass
    still masks real identifiers (belt and suspenders)."""
    text = "Contact John Q. Public at SSN 123-45-6789"
    ents = _entities_for(text)
    for e in ents:
        e["Score"] = 0.10  # below default 0.5 threshold
    monkeypatch.setenv("PHI_ENGINE", "comprehend_medical")
    monkeypatch.setattr(cm, "_client", lambda region=None: _FakeCMClientEntities(ents))

    out = mask(text)
    # CM did not redact the low-confidence NAME span...
    assert "[NAME-REDACTED]" not in out
    # ...but the deterministic SSN pass still fired.
    assert "123-45-6789" not in out and "[SSN-REDACTED]" in out


def test_confidence_threshold_env_override(monkeypatch):
    """PHI_COMPREHEND_MIN_CONFIDENCE tunes which CM entities redact."""
    text = "Patient John Q. Public"
    ents = _entities_for(text)
    ents[0]["Score"] = 0.60
    monkeypatch.setenv("PHI_ENGINE", "comprehend_medical")
    monkeypatch.setenv("PHI_COMPREHEND_MIN_CONFIDENCE", "0.90")
    monkeypatch.setattr(cm, "_client", lambda region=None: _FakeCMClientEntities(ents))

    out = mask(text)
    # 0.60 < 0.90 threshold -> name not redacted by CM.
    assert "[NAME-REDACTED]" not in out


def test_redact_direct_with_injected_client():
    """redact() honors an injected client (unit-level, no env/boto3)."""
    text = "Seen: John Q. Public today"
    client = _FakeCMClientEntities(_entities_for(text))
    out = cm.redact(text, client=client)
    assert out == "Seen: [NAME-REDACTED] today"
