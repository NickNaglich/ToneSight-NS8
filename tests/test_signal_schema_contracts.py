import json
from pathlib import Path


def _load_schema(name: str) -> dict:
    path = Path("schemas") / name
    assert path.exists(), f"Missing schema: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_signal_observation_schema_contract():
    schema = _load_schema("signal_observation.schema.json")
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema"]["const"] == "ns8.signal.observation.v1"
    required = set(schema["required"])
    for field in ("t", "domain", "entity_type", "entity_id", "stream_id", "channels"):
        assert field in required


def test_mapping_profile_schema_contract():
    schema = _load_schema("mapping_profile.schema.json")
    assert schema["properties"]["schema"]["const"] == "ns8.mapping.profile.v1"
    assert schema["properties"]["n"]["const"] == 8
    assert schema["properties"]["compose"]["properties"]["mode"]["const"] == "multi_channel_fold"
    assert schema["properties"]["validation"]["properties"]["missing_channel_policy"]["enum"] == [
        "error",
        "quarantine",
    ]


def test_anchor_event_schema_contract():
    schema = _load_schema("anchor_event.schema.json")
    assert schema["properties"]["schema"]["const"] == "ns8.signal.anchor_event.v1"
    anchor_required = set(schema["properties"]["anchor"]["required"])
    for field in ("family", "i", "j", "idx", "A"):
        assert field in anchor_required


def test_signal_quarantine_event_schema_contract():
    schema = _load_schema("signal_quarantine_event.schema.json")
    assert schema["properties"]["schema"]["const"] == "ns8.signal.quarantine_event.v1"
    assert schema["properties"]["reason_code"]["enum"] == [
        "MISSING_CHANNEL",
        "OUT_OF_RANGE",
        "PROFILE_MISMATCH",
    ]
    required = set(schema["required"])
    for field in (
        "observation_hash",
        "t",
        "entity_id",
        "mapping_profile",
        "mapping_profile_hash",
        "domain_pack",
        "domain_pack_hash",
        "run_id",
    ):
        assert field in required
