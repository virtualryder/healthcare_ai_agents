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
assessor expects. Here it is an in-memory list plus optional JSONL file so the
model is testable without AWS.
"""
from __future__ import annotations

import datetime as _dt
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


class GatewayAuditLog:
    def __init__(self, jsonl_path: Optional[str] = None) -> None:
        self.records: List[Dict[str, Any]] = []
        self._path = jsonl_path or os.getenv("GATEWAY_AUDIT_JSONL")

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
        self.records.append(full)
        if self._path:  # pragma: no cover - file IO
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(full) + "\n")
        return audit_id
