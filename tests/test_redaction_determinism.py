from tonesight_ns8.redaction import redact_live_event, redact_text


def test_redact_text_is_deterministic_and_counts_tokens():
    text = "Contact me at test@example.com or 555-123-4567 and SSN 123-45-6789."
    redacted_a, counts_a = redact_text(text)
    redacted_b, counts_b = redact_text(text)
    assert redacted_a == redacted_b
    assert counts_a == counts_b
    assert redacted_a == "Contact me at [EMAIL] or [PHONE] and SSN [SSN]."
    assert counts_a == {"EMAIL": 1, "PHONE": 1, "SSN": 1}


def test_redact_live_event_redacts_text_and_segments():
    event = {
        "event_id": "evt_1",
        "text": "Reach me at person@org.com",
        "segments": [
            {"id": "s1", "text": "Call 212-555-1212 please."},
            {"id": "s2", "text": "SSN 000-11-2222"},
        ],
    }
    redacted, counts = redact_live_event(event)
    assert redacted["text"] == "Reach me at [EMAIL]"
    assert redacted["segments"][0]["text"] == "Call [PHONE] please."
    assert redacted["segments"][1]["text"] == "SSN [SSN]"
    assert counts == {"EMAIL": 1, "PHONE": 1, "SSN": 1}

