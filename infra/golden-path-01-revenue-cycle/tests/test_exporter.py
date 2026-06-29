"""WORM exporter transform — keyed by global seq, immutable retain-until window."""
import datetime as dt
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import exporter  # noqa: E402


def test_object_key_is_seq_ordered_and_retained():
    now = dt.datetime(2026, 6, 29, tzinfo=dt.timezone.utc)
    key, body, retain = exporter._object_for(
        {"seq": 42, "audit_id": "abc", "decision": "ALLOW"}, retention_days=2555, now=now)
    assert key == "audit/000000000042-abc.json"          # zero-padded seq -> lexicographic order
    assert '"decision":"ALLOW"' in body
    assert retain == now + dt.timedelta(days=2555)        # WORM retain-until window


def test_keys_sort_in_seq_order():
    now = dt.datetime(2026, 6, 29, tzinfo=dt.timezone.utc)
    k1 = exporter._object_for({"seq": 9, "audit_id": "x"}, now=now)[0]
    k2 = exporter._object_for({"seq": 10, "audit_id": "x"}, now=now)[0]
    assert k1 < k2                                        # 000..009 < 000..010
