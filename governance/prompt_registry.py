"""
Prompt version registry — model-risk change control (NIST AI RMF: MEASURE/MANAGE).

Every system/agent prompt is registered and hash-pinned in prompt_manifest.json.
CI re-hashes the live prompts and fails if any prompt changed without a version
bump. This is the change-control mechanism that lets a payer/provider model-
governance or clinical-AI review board trust that a deployed agent's behavior
cannot drift silently — the kind of control a HITRUST assessor or a hospital AI
oversight committee expects before an agent touches a claim, a chart, or a
coverage decision.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Dict

_MANIFEST = os.path.join(os.path.dirname(__file__), "prompt_manifest.json")


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


@dataclass
class PromptRecord:
    name: str
    version: str
    sha256: str


def load_manifest() -> Dict[str, dict]:
    with open(_MANIFEST, "r", encoding="utf-8") as fh:
        return json.load(fh)["prompts"]


def register(name: str, version: str, text: str) -> PromptRecord:
    return PromptRecord(name=name, version=version, sha256=prompt_hash(text))


def verify(name: str, text: str) -> bool:
    """Return True if the live prompt matches the pinned hash for its registered version."""
    manifest = load_manifest()
    rec = manifest.get(name)
    if not rec:
        raise KeyError(f"prompt {name!r} is not registered in prompt_manifest.json")
    return rec["sha256"] == prompt_hash(text)
