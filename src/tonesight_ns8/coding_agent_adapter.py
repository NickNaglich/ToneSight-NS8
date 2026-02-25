"""Deterministic coding-agent adapter: feature extraction + binning + VAD mapping."""

from __future__ import annotations

from typing import Any

from .coding_agent_discretize import discretize_coding_agent_features
from .coding_agent_features import extract_coding_agent_features

CODING_AGENT_ADAPTER_ID = "coding_agent"
CODING_AGENT_ADAPTER_VERSION = "1.0"


def _clamp_bin(value: int) -> int:
    return max(1, min(8, int(value)))


def bins_to_vad(bins: dict[str, int]) -> tuple[int, int, int]:
    mismatch_inverse = 9 - int(bins["lang_mismatch_bin"])
    valence = round((mismatch_inverse + int(bins["tests_bin"]) + int(bins["error_handling_bin"])) / 3.0)
    arousal = round((int(bins["verbosity_bin"]) + int(bins["diff_bin"]) + int(bins["tool_call_bin"])) / 3.0)
    dominance = round((int(bins["structure_bin"]) + int(bins["error_handling_bin"]) + mismatch_inverse) / 3.0)
    return (_clamp_bin(valence), _clamp_bin(arousal), _clamp_bin(dominance))


def adapt_coding_agent_event(event: dict[str, Any]) -> dict[str, Any]:
    features = extract_coding_agent_features(event)
    bins = discretize_coding_agent_features(features)
    vad = bins_to_vad(bins)
    return {
        "adapter_id": CODING_AGENT_ADAPTER_ID,
        "adapter_version": CODING_AGENT_ADAPTER_VERSION,
        "features": features,
        "bins": bins,
        "vad": {"V": vad[0], "A": vad[1], "D": vad[2]},
    }

