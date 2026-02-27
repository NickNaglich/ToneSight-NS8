import json
from pathlib import Path

import pytest

from tonesight_ns8.domainpacks import load_builtin_domainpack_profile
from tonesight_ns8.errors import InvalidInput
from tonesight_ns8.signal_mapping import map_observation_to_ns8


def _vector_files() -> list[Path]:
    root = Path("tests") / "vectors" / "domainpacks"
    return sorted(root.glob("*/*.json"))


@pytest.mark.parametrize("path", _vector_files(), ids=lambda p: str(p))
def test_domainpack_vector_cases(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    profile_name = str(payload["profile"])
    profile = load_builtin_domainpack_profile(profile_name)
    cases = payload.get("cases", [])
    assert isinstance(cases, list)
    for case in cases:
        obs = case["observation"]
        expected_error = case.get("expected_error")
        if expected_error:
            with pytest.raises(InvalidInput, match=str(expected_error)):
                map_observation_to_ns8(obs, profile)
            continue
        result = map_observation_to_ns8(obs, profile)
        expected = case["expected"]
        assert result["family"] == expected["family"]
        assert result["r"] == expected["r"]
        assert result["c"] == expected["c"]
        assert result["k"] == expected["k"]
        assert result["idx"] == expected["idx"]
        assert result["A"] == expected["A"]
