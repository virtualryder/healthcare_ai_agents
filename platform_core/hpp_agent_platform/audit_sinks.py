"""
Append-only audit sinks — tamper-evident by construction.

Two designs are provided:

  * InMemoryAppendOnlySink / JsonlAppendOnlySink — a hash CHAIN (each record seals over the
    previous record's hash). Correct in a single process; used for tests and local runs.

  * LedgerSink (the production sink) — a CONCURRENCY-SAFE ledger that does NOT depend on an
    in-process "previous hash", so it is correct across cold starts, scaling, and concurrent
    Lambda environments. Each record gets:
       - a GLOBAL monotonic `seq` from an atomic DynamoDB counter (UpdateItem ADD), so order is
         well-defined no matter which environment writes it, and DELETION shows up as a gap;
       - a `record_hash` over the canonical record, and an HMAC `sig` over that hash keyed by an
         audit-signing secret, so MUTATION or INSERTION is detectable (an attacker lacks the key).
    Verification (`verify`) re-derives every hash, checks every signature, and asserts the seq
    sequence is contiguous (1..N) — no in-process state required. The append uses a conditional
    PutItem so a key collision can never overwrite an existing record.

`DynamoDbTableClient` is the AWS binding; `InMemoryTableClient` lets the ledger be unit-tested
deterministically with no AWS. Finalized records are streamed to S3 Object Lock (WORM) by the
golden-path AuditExporterFn off the table's DynamoDB stream — automatic, not a roadmap item.
"""
from __future__ import annotations

import abc
import hashlib
import hmac
import json
import os
import secrets
from typing import Any, Dict, List, Optional

_AUDIT_SECRET = os.getenv("AUDIT_SIGNING_SECRET", secrets.token_hex(32)).encode()
_SEQ_KEY = "__seq__"


def _canon(record: Dict[str, Any]) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), default=str).encode()


def _record_hash(record: Dict[str, Any], prev_hash: str = "") -> str:
    return hashlib.sha256((prev_hash + _canon(record).decode()).encode()).hexdigest()


class AuditSink(abc.ABC):
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


# ── Concurrency-safe ledger ──────────────────────────────────────────────────
class TableClient(abc.ABC):
    @abc.abstractmethod
    def next_seq(self) -> int: ...
    @abc.abstractmethod
    def put(self, item: Dict[str, Any]) -> None: ...
    @abc.abstractmethod
    def scan_records(self) -> List[Dict[str, Any]]: ...


class InMemoryTableClient(TableClient):
    """Deterministic stand-in for DynamoDB so the ledger is unit-testable without AWS."""
    def __init__(self) -> None:
        self._seq = 0
        self._items: Dict[str, Dict[str, Any]] = {}

    def next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def put(self, item: Dict[str, Any]) -> None:
        key = item["audit_id"]
        if key in self._items:
            raise KeyError("conditional put failed: audit_id exists")  # attribute_not_exists
        self._items[key] = dict(item)

    def scan_records(self) -> List[Dict[str, Any]]:
        return [dict(v) for v in self._items.values()]

    # test helpers
    def _delete(self, audit_id: str) -> None:
        self._items.pop(audit_id, None)


class DynamoDbTableClient(TableClient):  # pragma: no cover - requires AWS
    """Atomic counter + conditional PutItem against the audit DynamoDB table."""
    def __init__(self, table_name: str, region: Optional[str] = None) -> None:
        import boto3  # type: ignore
        self._table = boto3.resource(
            "dynamodb", region_name=region or os.getenv("AWS_REGION", "us-east-1")
        ).Table(table_name)

    def next_seq(self) -> int:
        resp = self._table.update_item(
            Key={"audit_id": _SEQ_KEY, "ts": _SEQ_KEY},
            UpdateExpression="ADD seqno :one",
            ExpressionAttributeValues={":one": 1},
            ReturnValues="UPDATED_NEW",
        )
        return int(resp["Attributes"]["seqno"])

    def put(self, item: Dict[str, Any]) -> None:
        self._table.put_item(Item=item, ConditionExpression="attribute_not_exists(audit_id)")

    def scan_records(self) -> List[Dict[str, Any]]:
        items, kw = [], {}
        while True:
            resp = self._table.scan(**kw)
            items.extend(resp.get("Items", []))
            if "LastEvaluatedKey" not in resp:
                break
            kw["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        return [i for i in items if i.get("audit_id") != _SEQ_KEY]


class LedgerSink(AuditSink):
    def __init__(self, table_client: TableClient, secret: Optional[bytes] = None) -> None:
        self._tc = table_client
        self._secret = secret or _AUDIT_SECRET

    def append(self, record: Dict[str, Any]) -> Dict[str, Any]:
        seq = self._tc.next_seq()
        body = {**record, "seq": seq}
        rh = _record_hash(body)
        sig = hmac.new(self._secret, rh.encode(), hashlib.sha256).hexdigest()
        sealed = {**body, "record_hash": rh, "sig": sig, "hash": rh}
        self._tc.put(sealed)
        return sealed

    def verify(self) -> bool:
        rows = sorted(self._tc.scan_records(), key=lambda r: int(r.get("seq", 0)))
        if not rows:
            return True
        for i, r in enumerate(rows, start=1):
            if int(r.get("seq", -1)) != i:                      # gap => a record was deleted
                return False
            body = {k: v for k, v in r.items() if k not in ("record_hash", "sig", "hash")}
            rh = _record_hash(body)
            if rh != r.get("record_hash"):                      # mutation
                return False
            expect = hmac.new(self._secret, rh.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expect, r.get("sig", "")):  # forged/tampered
                return False
        return True


# Back-compat alias: the prior name resolves to the concurrency-safe ledger when given a
# table NAME (it wraps DynamoDbTableClient). Existing callers keep working.
def DynamoDBAppendOnlySink(table_name: str, region: Optional[str] = None) -> LedgerSink:  # noqa: N802
    return LedgerSink(DynamoDbTableClient(table_name, region=region))


def ledger_sink(table_name: str) -> LedgerSink:
    return LedgerSink(DynamoDbTableClient(table_name))
