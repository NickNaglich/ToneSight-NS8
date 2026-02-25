"""Deterministic 1..8 binning for coding-agent feature telemetry."""

from __future__ import annotations

from typing import Any


def _clamp_bin(value: int) -> int:
    return max(1, min(8, int(value)))


def _bin_count(value: int, *, step: int) -> int:
    if value <= 0:
        return 1
    return _clamp_bin(1 + ((int(value) - 1) // int(step)))


def _bin_ratio(value: float) -> int:
    ratio = max(0.0, min(1.0, float(value)))
    return _clamp_bin(int(ratio * 7.0) + 1)


def discretize_coding_agent_features(features: dict[str, Any]) -> dict[str, int]:
    lines = int(features.get("response_lines", 0))
    code_fence_count = int(features.get("code_fence_count", 0))
    imports_count = int(features.get("imports_count", 0))
    test_markers = int(features.get("test_markers", 0))
    error_markers = int(features.get("error_handling_markers", 0))
    comment_ratio = float(features.get("comment_ratio_approx", 0.0))
    tool_calls = int(features.get("tool_call_count", 0))
    lang_mismatch = int(features.get("lang_mismatch", 0))
    diff_present = int(features.get("diff_present", 0))

    return {
        "verbosity_bin": _bin_count(lines, step=20),
        "structure_bin": _bin_count(code_fence_count + imports_count, step=2),
        "tests_bin": _bin_count(test_markers, step=1),
        "error_handling_bin": _bin_count(error_markers, step=1),
        "comment_density_bin": _bin_ratio(comment_ratio),
        "tool_call_bin": _bin_count(tool_calls, step=1),
        "lang_mismatch_bin": 8 if lang_mismatch else 1,
        "diff_bin": 8 if diff_present else 1,
    }

