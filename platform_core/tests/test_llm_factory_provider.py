"""Provider-default + external-egress-gate tests for the HPP LLM factory."""
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO)]

import pytest
from hpp_agent_platform import llm_factory


def test_default_provider_is_bedrock(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert llm_factory.provider() == "bedrock"


def test_external_anthropic_requires_optin(monkeypatch):
    """LLM_PROVIDER=anthropic without ALLOW_EXTERNAL_LLM must refuse (no silent PHI egress)."""
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ALLOW_EXTERNAL_LLM", raising=False)
    with pytest.raises(RuntimeError, match="external"):
        llm_factory.get_llm("fast")
