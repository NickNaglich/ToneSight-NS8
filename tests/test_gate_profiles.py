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
    assert profiles["coding_agent_drift"]["max_language_mismatch_rate_delta"] == 0.1
    assert profiles["coding_agent_drift"]["max_verbosity_bin_mean_delta"] == 2.0
    assert profiles["coding_agent_drift"]["min_tests_presence_rate_delta"] == -0.25
    assert profiles["coding_agent_drift"]["min_tool_call_rate_delta"] == -0.25


def test_gate_unknown_profile_raises():
    try:
        run_gate("missing_a", "missing_b", profile="does_not_exist")
    except Exception as exc:
        assert "Unknown gate profile" in str(exc)
