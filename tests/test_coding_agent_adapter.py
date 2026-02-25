from tonesight_ns8.coding_agent_adapter import adapt_coding_agent_event


def test_adapt_coding_agent_event_is_deterministic():
    event = {
        "event_id": "evt_adapter_1",
        "source": "coding_agent",
        "timestamp_received": "2026-02-25T12:00:00Z",
        "text": "import os\n\ndef solve(x):\n    return x\n",
        "meta": {"expected_language": "python", "tool_calls": 1},
        "privacy_flags": {"contains_pii": False, "allow_store_raw": True},
    }
    first = adapt_coding_agent_event(event)
    second = adapt_coding_agent_event(event)
    assert first == second
    assert first["adapter_id"] == "coding_agent"
    assert first["adapter_version"] == "1.0"
    assert all(1 <= value <= 8 for value in first["bins"].values())
    assert all(1 <= first["vad"][key] <= 8 for key in ("V", "A", "D"))

