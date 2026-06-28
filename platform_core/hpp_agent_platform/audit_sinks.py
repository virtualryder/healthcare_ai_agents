"""
Append-only audit sinks — tamper-evident by construction.

The audit trail is the spine of a HIPAA Security Rule defense (45 CFR 164.312(b)).
These sinks make "append-only" a property of the API, not a hope:

  * No update/delete is exposed. Records are immutable once written.
  * Each record carries `prev_hash` and a `hash` computed over its content + the
    previous hash — a hash chain. Removing or altering any record breaks the chain,
    so tampering is detectable (`verify_chain`).
  * Production sink (DynamoDB) writes with a conditional `attribute_not_exists`
    on the key and runs under an IAM policy that **denies** UpdateItem/DeleteItem;
    finalized snapshots land in S3 Object Lock (WORM). Those are the managed
    equivalents of the in-memory model here.
"""
from __future__ import annotations

import abc
import hashlib
import json
import os
from typing import Any, Dict, List, Optional


def _record_hash(record: Dict[str, Any], prev_hash: str) -> str:
    body = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256((prev_hash + body).encode()).hexdigest()


class AuditSink(abc.ABC):
    """Append-only audit sink. Implementations expose append() and nothing mutating."""
    @abc.abstractmethod
    def append(self, record: Dict[str, Any]) -> Dict[str, Any]: ...


class InMemoryAppendOnlySink(AuditSink):
    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []
        self._last_hash = "0" * 64

    def append(self, record: Dict[str, Any]) -> Dict[str, Any]:
        h = _record_hash(record, self._last_hash)
        sealed = {**record, "prev_hash": self._last_hash, "hash": h}
        self._records.append(sealed)
        self._last_hash = h
        return sealed

    @property
    def records(self) -> List[Dict[str, Any]]:
        # a copy — callers cannot mutate the sealed trail through this view
        return [dict(r) for r in self._records]

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for r in self._records:
            body = {k: v for k, v in r.items() if k not in ("prev_hash", "hash")}
            if r.get("prev_hash") != prev or r.get("hash") != _record_hash(body, prev):
                return False
            prev = r["hash"]
        return True


class JsonlAppendOnlySink(AuditSink):
    """Appends sealed records to a JSONL file (open 'a' only)."""
    def __init__(self, path: str) -> None:
        self._path = path
        self._last_hash = "0" * 64

    def append(self, record: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - file IO
        h = _record_hash(record, self._last_hash)
        sealed = {**record, "prev_hash": self._last_hash, "hash": h}
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(sealed, default=str) + "\n")
        self._last_hash = h
        return sealed


class DynamoDBAppendOnlySink(AuditSink):  # pragma: no cover - requires AWS
    """
    Production sink: conditional PutItem (attribute_not_exists) under an IAM policy
    that denies UpdateItem/DeleteItem. Lazy boto3 import. The hash chain is carried
    in the item so the WORM snapshot is independently verifiable.
    """
    def __init__(self, table_name: str, region: Optional[str] = None) -> None:
        import boto3  # type: ignore
        self._table = boto3.resource("dynamodb", region_name=region or os.getenv("AWS_REGION", "us-east-1")).Table(table_name)
        self._last_hash = "0" * 64

    def append(self, record: Dict[str, Any]) -> Dict[str, Any]:
        h = _record_hash(record, self._last_hash)
        sealed = {**record, "prev_hash": self._last_hash, "hash": h}
        self._table.put_item(Item=sealed, ConditionExpression="attribute_not_exists(audit_id)")
        self._last_hash = h
        return sealed
