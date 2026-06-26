"""Connector framework tests — fixtures resolve; unknown kinds/methods fail loudly."""
import pytest

from hpp_agent_platform.connectors import get_connector


def test_all_kinds_build():
    for kind in ("ehr", "pas", "clearinghouse", "payer", "coding", "clinicalcriteria",
                 "careplan", "scheduling", "registration", "kb", "identity", "consent",
                 "idp", "contactcenter"):
        get_connector(kind, mode="fixture")


def test_fixture_method_shapes():
    ch = get_connector("clearinghouse", mode="fixture")
    assert ch.validate_claim(claim_ref="CLM-1")["edits"]
    payer = get_connector("payer", mode="fixture")
    assert payer.check_claim_status(claim_ref="CLM-1")["status"] == "Denied"


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        get_connector("nope")


def test_unknown_method_raises():
    kb = get_connector("kb", mode="fixture")
    with pytest.raises(AttributeError):
        kb.no_such_method()
