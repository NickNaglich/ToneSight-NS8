import pytest

from tonesight_ns8.domainpacks import stable_payload_hash
from tonesight_ns8.errors import InvalidInput
from tonesight_ns8.signal_mapping import fold_channels, map_observation_to_ns8


def _profile() -> dict:
    return {
        "schema": "ns8.mapping.profile.v1",
        "name": "tone_vad",
        "version": "v1",
        "n": 8,
        "channels": {
            "valence_bin": {"required": True, "range": [1, 8]},
            "arousal_bin": {"required": True, "range": [1, 8]},
            "dominance_bin": {"required": True, "range": [1, 8]},
        },
        "compose": {
            "mode": "multi_channel_fold",
            "channel_order": ["valence_bin", "arousal_bin", "dominance_bin"],
        },
        "validation": {
            "reject_on_out_of_range": True,
            "missing_channel_policy": "quarantine",
        },
    }


def _observation() -> dict:
    return {
        "schema": "ns8.signal.observation.v1",
        "t": "2026-02-27T00:00:00Z",
        "domain": "tone",
        "entity_type": "speaker",
        "entity_id": "spk_1",
        "stream_id": "session_1",
        "channels": {
            "valence_bin": 3,
            "arousal_bin": 6,
            "dominance_bin": 4,
        },
    }


def test_fold_channels_is_deterministic():
    channels = {"a": 3, "b": 6, "c": 4}
    idx_1 = fold_channels(channels, ["a", "b", "c"], n=8)
    idx_2 = fold_channels(channels, ["a", "b", "c"], n=8)
    assert idx_1 == idx_2
    assert 1 <= idx_1 <= 64


def test_map_observation_to_ns8_emits_valid_ns8_params():
    profile = _profile()
    result = map_observation_to_ns8(_observation(), profile)
    assert result["family"] == "TLF"
    assert 1 <= result["r"] <= 8
    assert 1 <= result["c"] <= 8
    assert 1 <= result["k"] <= 8
    assert 1 <= result["idx"] <= 64
    assert 1 <= result["A"] <= 8
    assert result["mapping_profile"] == "tone_vad"
    assert result["mapping_profile_hash"] == stable_payload_hash(profile)


def test_map_observation_rejects_missing_required_channel():
    observation = _observation()
    observation["channels"].pop("dominance_bin")
    with pytest.raises(InvalidInput):
        map_observation_to_ns8(observation, _profile())


def test_map_observation_rejects_out_of_range_channel():
    observation = _observation()
    observation["channels"]["arousal_bin"] = 9
    with pytest.raises(InvalidInput):
        map_observation_to_ns8(observation, _profile())
