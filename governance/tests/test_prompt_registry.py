import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "01-revenue-cycle-denial-agent")]

from governance.prompt_registry import verify

def test_pinned_prompts_match_manifest():
    from agent.prompts import DENIAL_CLASSIFY_PROMPT, APPEAL_DRAFT_PROMPT
    assert verify("01-revenue-cycle-denial.classify", DENIAL_CLASSIFY_PROMPT)
    assert verify("01-revenue-cycle-denial.appeal", APPEAL_DRAFT_PROMPT)
