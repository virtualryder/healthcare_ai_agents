"""
Amazon Comprehend Medical PHI masker — the AWS-native ML NER engine for phi.py.

This module is the concrete implementation behind phi.py's optional ML masking
hook. It calls the Comprehend Medical ``DetectPHI`` API, which returns PHI
``Entities`` with ``BeginOffset`` / ``EndOffset`` / ``Type`` / ``Score``, and
redacts each detected span in place with a ``[<TYPE>-REDACTED]`` marker.

Design contract (must hold for HIPAA-safe logging/audit):

  * **Opt-in.** Only used when ``PHI_ENGINE=comprehend_medical``. If the flag is
    unset or set to anything else, phi.py never imports/calls this module.
  * **Optional dependency.** ``boto3`` is imported *lazily* inside the call so the
    dependency is not required in the default deterministic deployment.
  * **Fail closed.** ANY error — boto3 missing, client construction failure,
    throttling, ``ClientError``, malformed response, bad offsets — is raised.
    phi.py's ML hook catches it and falls back to the deterministic Safe-Harbor
    masker (never returning unmasked text). This module NEVER returns the input
    text on an error path, and NEVER returns partially-masked text on error.
  * **Belt and suspenders.** phi.py ALWAYS runs the deterministic Safe-Harbor
    pass in addition to this engine — Comprehend Medical + regex, never one
    alone.

HIPAA / residency: Amazon Comprehend Medical is a HIPAA-eligible service and is
reached over the regional Comprehend Medical API endpoint. In the golden-path
deployment that endpoint is reached privately over an interface VPC endpoint
(AWS PrivateLink); traffic to the regional service stays on AWS private
networking under the executed AWS BAA. PHI is processed by the AWS service, not
sent to any non-AWS third-party AI API.
"""
from __future__ import annotations

import os
from typing import List, Optional, Tuple

# Environment flag value that selects this engine (checked by phi.py).
PHI_ENGINE_COMPREHEND_MEDICAL = "comprehend_medical"

# Default minimum confidence for a detected entity to be redacted. Conservative:
# Comprehend Medical scores are 0..1; only spans at/above the threshold redact,
# but the deterministic Safe-Harbor pass in phi.py still runs regardless.
DEFAULT_CONFIDENCE_THRESHOLD = 0.5


def _confidence_threshold() -> float:
    """Resolve the confidence threshold from env, falling back to the default."""
    raw = os.getenv("PHI_COMPREHEND_MIN_CONFIDENCE", "").strip()
    if not raw:
        return DEFAULT_CONFIDENCE_THRESHOLD
    try:
        val = float(raw)
    except ValueError:
        return DEFAULT_CONFIDENCE_THRESHOLD
    # Clamp to a sane range; an out-of-range env value must not disable masking.
    if val < 0.0 or val > 1.0:
        return DEFAULT_CONFIDENCE_THRESHOLD
    return val


def _client(region: Optional[str] = None):
    """
    Construct a boto3 ``comprehendmedical`` client. boto3 is imported lazily so
    the dependency is optional. Any failure here propagates (fail closed).
    """
    import boto3  # lazy import — optional dependency

    region = region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    if region:
        return boto3.client("comprehendmedical", region_name=region)
    return boto3.client("comprehendmedical")


def detect_phi_spans(
    text: str,
    *,
    confidence_threshold: Optional[float] = None,
    client=None,
) -> List[Tuple[int, int, str, float]]:
    """
    Call Comprehend Medical ``DetectPHI`` and return PHI spans that meet the
    confidence threshold, as ``(begin_offset, end_offset, type, score)`` tuples.

    Raises on any boto3/client/response error — the caller (phi.py) fails closed
    on the exception. Never returns unmasked text; this returns spans only.
    """
    if confidence_threshold is None:
        confidence_threshold = _confidence_threshold()

    cm = client if client is not None else _client()
    # DetectPHI is the PHI-specific detection API. Any ClientError / throttling /
    # network error raises out of here by design.
    resp = cm.detect_phi(Text=text)
    entities = resp["Entities"]  # KeyError here also fails closed (malformed resp)

    spans: List[Tuple[int, int, str, float]] = []
    for ent in entities:
        score = float(ent.get("Score", 0.0))
        if score < confidence_threshold:
            continue
        begin = int(ent["BeginOffset"])
        end = int(ent["EndOffset"])
        etype = str(ent.get("Type", "PHI"))
        # Guard against nonsensical offsets rather than silently mis-redacting.
        if begin < 0 or end > len(text) or begin >= end:
            raise ValueError(
                f"Comprehend Medical returned out-of-range offsets: {begin}-{end} "
                f"for text length {len(text)}"
            )
        spans.append((begin, end, etype, score))
    return spans


def redact(
    text: str,
    *,
    confidence_threshold: Optional[float] = None,
    client=None,
) -> str:
    """
    Redact PHI spans detected by Comprehend Medical ``DetectPHI`` in ``text``.

    Each detected span at/above the confidence threshold is replaced with
    ``[<TYPE>-REDACTED]``. This is the function phi.py's ML hook invokes when
    ``PHI_ENGINE=comprehend_medical``.

    FAIL CLOSED: any boto3/client/response error propagates to the caller, which
    applies the deterministic Safe-Harbor fallback. This function never returns
    the unmasked input on an error path.
    """
    if not text:
        return ""

    spans = detect_phi_spans(
        text, confidence_threshold=confidence_threshold, client=client
    )
    if not spans:
        return text

    # Redact from the end so earlier offsets stay valid as we splice.
    spans.sort(key=lambda s: s[0], reverse=True)
    out = text
    for begin, end, etype, _score in spans:
        marker = f"[{etype.upper()}-REDACTED]"
        out = out[:begin] + marker + out[end:]
    return out


def enabled() -> bool:
    """True when PHI_ENGINE selects Comprehend Medical."""
    return (
        os.getenv("PHI_ENGINE", "").strip().lower()
        == PHI_ENGINE_COMPREHEND_MEDICAL
    )
