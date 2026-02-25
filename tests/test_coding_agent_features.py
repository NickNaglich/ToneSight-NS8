import pytest

from tonesight_ns8.coding_agent_features import detect_language, extract_coding_agent_features


def test_detect_language_python_signal():
    text = "import os\n\ndef handler(x):\n    try:\n        return x\n    except Exception:\n        raise\n"
    assert detect_language(text) == "python"


def test_extract_features_with_expected_language_mismatch():
    event = {
        "event_id": "evt1",
        "source": "coding_agent",
        "timestamp_received": "2026-02-25T12:00:00Z",
        "text": "const x: string = 'hi';\ntry { return x; } catch (e) { throw e; }",
        "meta": {"expected_language": "python", "tool_calls": [{"name": "lint"}]},
        "privacy_flags": {"contains_pii": False, "allow_store_raw": True},
    }
    features = extract_coding_agent_features(event)
    assert features["response_lines"] == 2
    assert features["lang_detected"] in {"typescript", "javascript"}
    assert features["lang_expected"] == "python"
    assert features["lang_mismatch"] == 1
    assert features["tool_call_count"] == 1


def test_extract_features_requires_text_or_segments():
    event = {
        "event_id": "evt2",
        "source": "coding_agent",
        "timestamp_received": "2026-02-25T12:00:00Z",
        "meta": {},
        "privacy_flags": {"contains_pii": False, "allow_store_raw": True},
    }
    with pytest.raises(ValueError, match="requires non-empty text"):
        extract_coding_agent_features(event)
