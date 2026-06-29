"""
Gateway audit log — tamper-evident, PHI-masked record of every tool attempt.

Every decision (ALLOW / DENY / PENDING_APPROVAL / ERROR) is recorded with the
acting workforce user, agent, tool, lineage to the system of record reached
(EHR / clearinghouse / payer / patient accounting), and the approver where a
human gate applied. Free-text args are PHI-masked before they are written, so an
audit record can never become a back door around the minimum-necessary standard.

In production the sink is an append-only store (DynamoDB with a deny on
UpdateItem/DeleteItem, plus PITR) and finalized snapshots land in S3 Object Lock
(COMPLIANCE mode, WORM) so the trail is tamper-evident by design — the access-
accounting and audit-control a HIPAA Security Rule (45 CFR 164.312(b)) / HITRUST
assessor expects. Without a sink it is an in-memory list plus optional JSONL file
so the model is testable without AWS; pass a DynamoDBAppendOnlySink to make the
DEPLOYED trail append-only and WORM-backed.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import uuid
from typing import Any, Dict, List, Optional

from hpp_agent_platform.phi import mask


def _mask_args(args: Any) -> Any:
    if isinstance(args, dict):
        return {k: _mask_args(v) for k, v in args.items()}
    if isinstance(args, list):
        return [_mask_args(v) for v in args]
    if isinstance(args, str):
        return mask(args)
    return args


def _chain_hash(record: Dict[str, Any], prev_hash: str) -> str:
    body = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256((prev_hash + body).encode()).hexdigest()


class GatewayAuditLog:
    """Append-only, PHI-masked, hash-chained audit. Each record seals over the
    previous record's hash, so removing or altering any entry breaks the chain
    (`verify_chain`). With a durable `sink` (DynamoDBAppendOnlySink) the sink owns
    the chain and is the system of record — see hpp_agent_platform.audit_sinks."""

    def __init__(self, jsonl_path: Optional[str] = None, sink: Optional[Any] = None) -> None:
        self.records: List[Dict[str, Any]] = []
        self._path = jsonl_path or os.getenv("GATEWAY_AUDIT_JSONL")
        self._last_hash = "0" * 64
        # Optional durable, append-only sink. When set, the sink seals/chains the
        # record and IS the system of record; we keep a local mirror only so
        # verify_chain()/tests can read it back. This is what makes the DEPLOYED
        # audit append-only + WORM-backed rather than in-memory.
        self._sink = sink

    def record(self, entry: Dict[str, Any]) -> str:
        audit_id = str(uuid.uuid4())
        full = {
            "audit_id": audit_id,
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            **entry,
        }
        if "args" in full:
            full["args"] = _mask_args(full["args"])
        if "detail" in full and isinstance(full["detail"], str):
            full["detail"] = mask(full["detail"])
        if self._sink is not None:
            # Durable sink owns the single hash chain; persist first so a failed
            # durable write fails the call closed rather than recording a phantom ALLOW.
            sealed = self._sink.append(full)
            self._last_hash = sealed.get("hash", self._last_hash)
            self.records.append(sealed)
            return audit_id
        # In-memory chain: hash over the record BODY (pre-prev_hash/hash), chained on prev.
        prev = self._last_hash
        h = _chain_hash(full, prev)
        full["prev_hash"] = prev
        full["hash"] = h
        self._last_hash = h
        self.records.append(full)
        if self._path:  # pragma: no cover - file IO
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(full) + "\n")
        return audit_id

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for r in self.records:
            body = {k: v for k, v in r.items() if k not in ("prev_hash", "hash")}
            if r.get("prev_hash") != prev or r.get("hash") != _chain_hash(body, prev):
                return False
            prev = r["hash"]
        return True
