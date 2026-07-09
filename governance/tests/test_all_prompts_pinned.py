"""Every agent prompt is hash-pinned in prompt_manifest.json — and the manifest has no
orphans. Runs in isolation (execs each agent's prompts.py) so it needs no package imports."""
import hashlib
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
_MANIFEST = json.loads((_REPO / "governance" / "prompt_manifest.json").read_text())["prompts"]


def _agent_prompt_texts():
    texts = []
    for prompts_py in sorted(_REPO.glob("0*-*-agent/agent/prompts.py")):
        ns = {}
        # encoding="utf-8" is required: prompts contain non-ASCII (em-dashes). Without it,
        # Path.read_text() uses the platform default (cp1252 on Windows) and mis-hashes the
        # prompt vs the utf-8-pinned manifest, so the test would pass on Linux CI but fail on
        # Windows. Pin the encoding so the hash is identical on every platform.
        exec(compile(prompts_py.read_text(encoding="utf-8"), str(prompts_py), "exec"), ns)
        for name, val in ns.items():
            if name.endswith("_PROMPT") and isinstance(val, str):
                texts.append((prompts_py.parent.parent.name, name, val))
    return texts


def _sha(t):
    return hashlib.sha256(t.strip().encode("utf-8")).hexdigest()


def test_every_agent_prompt_is_pinned():
    pinned = {rec["sha256"] for rec in _MANIFEST.values()}
    texts = _agent_prompt_texts()
    assert len(texts) >= 16, f"expected >=16 agent prompts, found {len(texts)}"
    for agent, name, val in texts:
        assert _sha(val) in pinned, f"{agent}.{name} is not hash-pinned in prompt_manifest.json"


def test_manifest_has_no_orphans():
    live = {_sha(v) for _, _, v in _agent_prompt_texts()}
    for key, rec in _MANIFEST.items():
        assert rec["sha256"] in live, f"manifest entry {key} matches no live prompt (orphan/drift)"
