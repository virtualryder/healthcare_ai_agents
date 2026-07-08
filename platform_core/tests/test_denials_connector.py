"""
Denials connector scaffold tests — fixture reads work; live reads and all writes
fail closed with an engagement-pointing message; factory wiring is additive.
"""
import pytest

from hpp_agent_platform.connectors import get_connector
from hpp_agent_platform.connectors.denials import DenialsConnector


def test_factory_builds_denials_fixture():
    c = get_connector("denials", mode="fixture")
    assert isinstance(c, DenialsConnector)
    assert c.mode == "fixture"


def test_fixture_reads_return_synthetic_denials():
    c = get_connector("denials", mode="fixture")
    rec = c.get_denial(claim_id="CLM-2026-0001")
    assert rec["payer"] == "BlueChoice PPO"
    assert rec["denial_codes"] == ["CO-197"]
    assert "_gold" not in rec  # eval-only annotations are not leaked to callers
    worklist = c.list_denials(limit=100)
    assert len(worklist) >= 20


def test_fixture_duplicate_search_ranks_shared_payer_code_service():
    c = get_connector("denials", mode="fixture")
    dups = c.search_duplicates(payer="Medicaid", denial_code="CO-197", service="99204",
                               exclude_claim_id="CLM-2026-0009")
    assert dups and dups[0]["claim_id"] == "CLM-2026-0010"
    assert dups[0]["match_score"] == 1.0


def test_live_mode_read_raises_pointing_to_real_source():
    c = get_connector("denials", mode="live")
    with pytest.raises(NotImplementedError) as ei:
        c.get_denial(claim_id="CLM-X")
    msg = str(ei.value)
    assert "835" in msg and "HealthLake" in msg


def test_writes_are_human_gated_in_every_mode():
    for mode in ("fixture", "live", "sandbox"):
        c = get_connector("denials", mode=mode)
        with pytest.raises(NotImplementedError):
            c.resubmit_claim(claim_ref="CLM-1")
        with pytest.raises(NotImplementedError):
            c.submit_appeal(claim_ref="CLM-1")


def test_denials_wiring_does_not_regress_other_kinds():
    # Existing fixture default is unchanged for a representative kind.
    ch = get_connector("clearinghouse", mode="fixture")
    assert ch.validate_claim(claim_ref="CLM-1")["edits"]
