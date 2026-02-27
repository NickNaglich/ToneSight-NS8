"""Deterministic signal observation to NS8 parameter mapping."""

from __future__ import annotations

from typing import Any

from .domainpacks import stable_payload_hash, validate_mapping_profile
from .errors import InvalidInput
from .ns8 import compute_A

NS8_FAMILY_DEFAULT = "TLF"


def _require_channel_int(name: str, value: Any) -> int:
    if not isinstance(value, int):
        raise InvalidInput(f"channel {name!r} must be integer in 1..8")
    if value < 1 or value > 8:
        raise InvalidInput(f"channel {name!r} out of range: {value} (expected 1..8)")
    return value


def fold_channels(channels: dict[str, Any], channel_order: list[str], n: int = 8) -> int:
    """Deterministically fold ordered channels into a 1..(n*n) index."""
    if n != 8:
        raise InvalidInput("n must be 8")
    if not channel_order:
        raise InvalidInput("channel_order must be non-empty")
    state = 0
    for name in channel_order:
        value = channels.get(name)
        state = (state * n) + (_require_channel_int(name, value) - 1)
    return (state % (n * n)) + 1


def _derive_k(channels: dict[str, Any], channel_order: list[str], n: int = 8) -> int:
    """Derive deterministic k in 1..8 from folded state remainder."""
    state = 0
    for name in channel_order:
        value = channels.get(name)
        state = (state * n) + (_require_channel_int(name, value) - 1)
    return ((state // (n * n)) % n) + 1


def map_observation_to_ns8(observation: dict[str, Any], mapping_profile: dict[str, Any]) -> dict[str, Any]:
    """Map signal observation channels into deterministic NS8 params + anchor."""
    if not isinstance(observation, dict):
        raise InvalidInput("observation must be object")
    validate_mapping_profile(mapping_profile)

    channels = observation.get("channels")
    if not isinstance(channels, dict) or not channels:
        raise InvalidInput("observation.channels must be non-empty object")

    profile_channels = mapping_profile["channels"]
    missing_required = [name for name, spec in profile_channels.items() if spec["required"] and channels.get(name) is None]
    if missing_required:
        raise InvalidInput(f"missing required channels: {', '.join(sorted(missing_required))}")

    order = list(mapping_profile["compose"]["channel_order"])
    idx = fold_channels(channels, order, n=8)
    r = ((idx - 1) // 8) + 1
    c = ((idx - 1) % 8) + 1
    k = _derive_k(channels, order, n=8)
    family = NS8_FAMILY_DEFAULT
    anchor = compute_A(family, r, c, k, 8)

    return {
        "family": family,
        "r": r,
        "c": c,
        "k": k,
        "idx": idx,
        "A": anchor,
        "mapping_profile": mapping_profile["name"],
        "mapping_profile_hash": stable_payload_hash(mapping_profile),
    }
