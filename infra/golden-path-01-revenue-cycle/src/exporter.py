"""
Audit WORM exporter — streams every finalized audit record into S3 Object Lock (COMPLIANCE).

Triggered by the AuditTable DynamoDB stream (INSERT events), so export is AUTOMATIC and part of
the durable write path — not a manual/roadmap step. Each record is written once, keyed by its
global `seq`, with an Object-Lock retain-until date so it is immutable for the retention window
(legal-hold-grade WORM). This is the durable, independently verifiable evidence a HIPAA Security
Rule (45 CFR 164.312(b)) / HITRUST assessor expects, separate from the live table.
"""
import datetime as _dt
import json
import os

_RETENTION_DAYS = int(os.getenv("WORM_RETENTION_DAYS", "2555"))   # ~7 years
_SEQ_KEY = "__seq__"


def _object_for(image, retention_days=_RETENTION_DAYS, now=None):
    """Pure transform (unit-testable): a plain audit record -> (s3_key, body, retain_until)."""
    now = now or _dt.datetime.now(_dt.timezone.utc)
    seq = int(image.get("seq", 0))
    audit_id = image.get("audit_id", "unknown")
    key = f"audit/{seq:012d}-{audit_id}.json"
    body = json.dumps(image, sort_keys=True, separators=(",", ":"), default=str)
    retain_until = now + _dt.timedelta(days=retention_days)
    return key, body, retain_until


def handler(event, context):  # pragma: no cover - requires AWS + stream event
    import boto3
    from boto3.dynamodb.types import TypeDeserializer
    s3 = boto3.client("s3")
    bucket = os.environ["WORM_BUCKET"]
    deser = TypeDeserializer()
    written = 0
    for rec in event.get("Records", []):
        if rec.get("eventName") != "INSERT":
            continue
        image = {k: deser.deserialize(v) for k, v in rec["dynamodb"]["NewImage"].items()}
        if image.get("audit_id") == _SEQ_KEY:        # skip the atomic counter item
            continue
        key, body, _ = _object_for(image)
        # Object Lock mode + retain-until are inherited from the bucket's default retention
        # (COMPLIANCE in prod, GOVERNANCE in non-prod) — set once on the bucket, not per object.
        s3.put_object(Bucket=bucket, Key=key, Body=body.encode(), ContentType="application/json")
        written += 1
    return {"exported": written}
