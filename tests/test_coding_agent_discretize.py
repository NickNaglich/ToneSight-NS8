from tonesight_ns8.coding_agent_adapter import bins_to_vad
from tonesight_ns8.coding_agent_discretize import discretize_coding_agent_features


def test_discretize_output_bins_in_range():
    features = {
        "response_lines": 45,
        "code_fence_count": 2,
        "imports_count": 3,
        "test_markers": 1,
        "error_handling_markers": 2,
        "comment_ratio_approx": 0.25,
        "tool_call_count": 2,
        "lang_mismatch": 0,
        "diff_present": 1,
    }
    bins = discretize_coding_agent_features(features)
    assert all(1 <= value <= 8 for value in bins.values())
    assert bins["lang_mismatch_bin"] == 1
    assert bins["diff_bin"] == 8


def test_bins_to_vad_is_stable_and_bounded():
    bins = {
        "verbosity_bin": 8,
        "structure_bin": 7,
        "tests_bin": 6,
        "error_handling_bin": 6,
        "comment_density_bin": 2,
        "tool_call_bin": 4,
        "lang_mismatch_bin": 8,
        "diff_bin": 8,
    }
    first = bins_to_vad(bins)
    second = bins_to_vad(bins)
    assert first == second
    assert all(1 <= value <= 8 for value in first)


def test_discretize_threshold_boundaries_are_stable():
    features = {
        "response_lines": 20,
        "code_fence_count": 1,
        "imports_count": 1,
        "test_markers": 0,
        "error_handling_markers": 0,
        "comment_ratio_approx": 1.0,
        "tool_call_count": 0,
        "lang_mismatch": 1,
        "diff_present": 0,
    }
    bins = discretize_coding_agent_features(features)
    assert bins["verbosity_bin"] == 1
    assert bins["structure_bin"] == 1
    assert bins["tests_bin"] == 1
    assert bins["error_handling_bin"] == 1
    assert bins["comment_density_bin"] == 8
    assert bins["tool_call_bin"] == 1
    assert bins["lang_mismatch_bin"] == 8
    assert bins["diff_bin"] == 1
