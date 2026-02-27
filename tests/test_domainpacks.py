import json
from pathlib import Path
from uuid import uuid4

import pytest

from tonesight_ns8.domainpacks import (
    SUPPORTED_COMPOSE_MODE,
    get_builtin_domainpack_profile_path,
    list_builtin_domainpack_profiles,
    load_builtin_domainpack_profile,
    load_mapping_profile,
    stable_payload_hash,
    validate_mapping_profile,
)
from tonesight_ns8.errors import InvalidInput


def _valid_profile() -> dict:
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
            "mode": SUPPORTED_COMPOSE_MODE,
            "channel_order": ["valence_bin", "arousal_bin", "dominance_bin"],
        },
        "validation": {
            "reject_on_out_of_range": True,
            "missing_channel_policy": "error",
        },
    }


def test_validate_mapping_profile_accepts_valid_payload():
    validate_mapping_profile(_valid_profile())


def test_validate_mapping_profile_rejects_bad_mode():
    payload = _valid_profile()
    payload["compose"]["mode"] = "weighted_blend"
    with pytest.raises(InvalidInput):
        validate_mapping_profile(payload)


def test_stable_payload_hash_is_deterministic_across_key_order():
    a = _valid_profile()
    b = json.loads(json.dumps(_valid_profile(), sort_keys=True))
    assert stable_payload_hash(a) == stable_payload_hash(b)


def test_load_mapping_profile_round_trip():
    root = Path(".agent") / "test_tmp" / f"domainpack_profile_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "profile.json"
    path.write_text(json.dumps(_valid_profile(), indent=2) + "\n", encoding="utf-8")
    loaded = load_mapping_profile(path)
    assert loaded["name"] == "tone_vad"


def test_builtin_domainpack_profiles_load_and_validate():
    profile_ids = list_builtin_domainpack_profiles()
    assert "tone_vad_v1" in profile_ids
    assert "kasbah_env_v1" in profile_ids
    for profile_id in profile_ids:
        path = get_builtin_domainpack_profile_path(profile_id)
        assert path.exists()
        payload = load_builtin_domainpack_profile(profile_id)
        validate_mapping_profile(payload)
