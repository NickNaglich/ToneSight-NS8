from tonesight_ns8.live_identity import canonical_live_event, stable_event_hash


def test_stable_event_hash_ignores_timestamp_received():
    event_a = {
        "event_id": "evt_1",
        "source": "support_chat",
        "timestamp_received": "2026-02-21T00:00:00Z",
        "text": "hello",
        "meta": {"session_id": "s1"},
        "privacy_flags": {"contains_pii": False, "allow_store_raw": True},
    }
    event_b = {
        **event_a,
        "timestamp_received": "2026-02-21T00:00:10Z",
    }
    assert stable_event_hash(event_a) == stable_event_hash(event_b)


def test_canonical_live_event_excludes_volatile_fields():
    event = {
        "event_id": "evt_1",
        "source": "support_chat",
        "timestamp_received": "2026-02-21T00:00:00Z",
        "text": "hello",
        "meta": {"session_id": "s1"},
        "privacy_flags": {"contains_pii": False, "allow_store_raw": True},
    }
    canonical = canonical_live_event(event)
    assert "timestamp_received" not in canonical
    assert canonical["event_id"] == "evt_1"

