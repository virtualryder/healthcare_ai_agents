"""
Concurrency-safe audit ledger tests — prove the production sink is tamper-evident WITHOUT any
in-process chain state: atomic global sequence (order + deletion detection) + per-record HMAC
(mutation/forgery detection). Verified deterministically with the in-memory table client.
"""
import pytest

from hpp_agent_platform.audit_sinks import InMemoryTableClient, LedgerSink


def _sink():
    return LedgerSink(InMemoryTableClient(), secret=b"unit-test-secret")


def test_appends_get_monotonic_global_seq_and_verify():
    tc = InMemoryTableClient()
    sink = LedgerSink(tc, secret=b"k")
    for i in range(5):
        sink.append({"audit_id": f"a{i}", "decision": "ALLOW", "tool": "pas.get_claim"})
    seqs = sorted(int(r["seq"]) for r in tc.scan_records())
    assert seqs == [1, 2, 3, 4, 5]
    assert sink.verify() is True


def test_mutation_is_detected():
    tc = InMemoryTableClient()
    sink = LedgerSink(tc, secret=b"k")
    sink.append({"audit_id": "a1", "decision": "ALLOW"})
    sink.append({"audit_id": "a2", "decision": "ALLOW"})
    tc._items["a2"]["decision"] = "DENY"        # tamper with a stored record
    assert sink.verify() is False


def test_deletion_shows_up_as_a_gap():
    tc = InMemoryTableClient()
    sink = LedgerSink(tc, secret=b"k")
    for i in range(3):
        sink.append({"audit_id": f"a{i}", "decision": "ALLOW"})
    tc._delete("a1")                             # remove the middle record -> seq gap
    assert sink.verify() is False


def test_signature_forgery_without_key_fails():
    tc = InMemoryTableClient()
    sink = LedgerSink(tc, secret=b"real-key")
    sink.append({"audit_id": "a1", "decision": "ALLOW"})
    # an attacker rewrites the record and re-hashes, but cannot produce a valid HMAC sig
    item = tc._items["a1"]
    item["decision"] = "DENY"
    from hpp_agent_platform.audit_sinks import _record_hash
    body = {k: v for k, v in item.items() if k not in ("record_hash", "sig", "hash")}
    item["record_hash"] = _record_hash(body)     # fix the hash...
    # ...but sig is still over the OLD hash and they lack the key to forge a new one
    assert sink.verify() is False


def test_conditional_put_blocks_overwrite():
    tc = InMemoryTableClient()
    sink = LedgerSink(tc, secret=b"k")
    sink.append({"audit_id": "dup", "decision": "ALLOW"})
    with pytest.raises(KeyError):
        tc.put({"audit_id": "dup", "seq": 99})   # attribute_not_exists(audit_id) equivalent


def test_concurrent_writers_get_distinct_seqs():
    tc = InMemoryTableClient()
    # two LedgerSinks sharing ONE table (like two Lambda environments) -> no shared memory state
    s1, s2 = LedgerSink(tc, secret=b"k"), LedgerSink(tc, secret=b"k")
    s1.append({"audit_id": "x1", "decision": "ALLOW"})
    s2.append({"audit_id": "x2", "decision": "ALLOW"})
    s1.append({"audit_id": "x3", "decision": "ALLOW"})
    seqs = sorted(int(r["seq"]) for r in tc.scan_records())
    assert seqs == [1, 2, 3]                      # atomic counter -> no duplicate/branched heads
    assert LedgerSink(tc, secret=b"k").verify() is True
