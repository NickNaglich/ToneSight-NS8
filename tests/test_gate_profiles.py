import json
from pathlib import Path

from tonesight_ns8.gate_runner import _load_gate_profiles, run_gate


def test_load_gate_profiles_has_required_profiles():
    profiles = _load_gate_profiles(Path("config/gate_profiles.json"))
    assert "support_chat" in profiles
    assert "sales_chat" in profiles
    assert "strict_regression" in profiles
    assert "coding_agent_drift" in profiles
    assert profiles["coding_agent_drift"]["require_pinned_model_identity"] is True


def test_gate_unknown_profile_raises():
    try:
        run_gate("missing_a", "missing_b", profile="does_not_exist")
    except Exception as exc:
        assert "Unknown gate profile" in str(exc)
