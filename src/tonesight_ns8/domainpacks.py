"""Deterministic mapping profile loading and validation helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import InvalidInput

MAPPING_PROFILE_SCHEMA = "ns8.mapping.profile.v1"
SUPPORTED_COMPOSE_MODE = "multi_channel_fold"
_DOMAINPACKS_DIR = Path(__file__).resolve().parent / "domainpacks_data"
_BUILTIN_DOMAINPACK_PROFILES = {
    "tone_vad_v1": _DOMAINPACKS_DIR / "tone_vad_v1.json",
    "kasbah_env_v1": _DOMAINPACKS_DIR / "kasbah_env_v1.json",
}


def stable_payload_hash(payload: dict[str, Any]) -> str:
    """Return stable short hash for deterministic profile identity."""
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _require_type(value: Any, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise InvalidInput(f"{field} must be {expected.__name__}")


def validate_mapping_profile(profile: dict[str, Any]) -> None:
    """Validate mapping profile using deterministic project constraints."""
    _require_type(profile, dict, "profile")

    schema = profile.get("schema")
    if schema != MAPPING_PROFILE_SCHEMA:
        raise InvalidInput(f"schema must be {MAPPING_PROFILE_SCHEMA!r}")

    name = profile.get("name")
    _require_type(name, str, "name")
    if not name:
        raise InvalidInput("name must be non-empty")

    version = profile.get("version")
    _require_type(version, str, "version")
    if not version.startswith("v"):
        raise InvalidInput("version must start with 'v'")

    n = profile.get("n")
    if n != 8:
        raise InvalidInput("n must be 8")

    channels = profile.get("channels")
    _require_type(channels, dict, "channels")
    if not channels:
        raise InvalidInput("channels must define at least one channel")
    for key, spec in channels.items():
        if not isinstance(key, str) or not key:
            raise InvalidInput("channels keys must be non-empty strings")
        _require_type(spec, dict, f"channels.{key}")
        if "required" not in spec or not isinstance(spec["required"], bool):
            raise InvalidInput(f"channels.{key}.required must be bool")
        chan_range = spec.get("range")
        if chan_range != [1, 8]:
            raise InvalidInput(f"channels.{key}.range must be [1, 8]")

    compose = profile.get("compose")
    _require_type(compose, dict, "compose")
    mode = compose.get("mode")
    if mode != SUPPORTED_COMPOSE_MODE:
        raise InvalidInput(f"compose.mode must be {SUPPORTED_COMPOSE_MODE!r}")
    order = compose.get("channel_order")
    _require_type(order, list, "compose.channel_order")
    if not order:
        raise InvalidInput("compose.channel_order must include at least one channel")
    for channel_name in order:
        if channel_name not in channels:
            raise InvalidInput(f"compose.channel_order references unknown channel: {channel_name!r}")

    validation = profile.get("validation")
    _require_type(validation, dict, "validation")
    if validation.get("reject_on_out_of_range") is not True:
        raise InvalidInput("validation.reject_on_out_of_range must be true")
    missing_policy = validation.get("missing_channel_policy")
    if missing_policy not in ("error", "quarantine"):
        raise InvalidInput("validation.missing_channel_policy must be 'error' or 'quarantine'")


def load_mapping_profile(profile_path: str | Path) -> dict[str, Any]:
    """Load mapping profile JSON and enforce deterministic constraints."""
    path = Path(profile_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InvalidInput(f"mapping profile not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InvalidInput(f"mapping profile is not valid JSON: {path}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise InvalidInput("mapping profile root must be object")
    validate_mapping_profile(payload)
    return payload


def list_builtin_domainpack_profiles() -> tuple[str, ...]:
    """List deterministic built-in domain pack profile ids."""
    return tuple(sorted(_BUILTIN_DOMAINPACK_PROFILES.keys()))


def get_builtin_domainpack_profile_path(profile_name: str) -> Path:
    """Resolve built-in domain pack profile file path."""
    key = str(profile_name).strip()
    if key not in _BUILTIN_DOMAINPACK_PROFILES:
        raise InvalidInput(f"unknown built-in domain pack profile: {profile_name!r}")
    return _BUILTIN_DOMAINPACK_PROFILES[key]


def load_builtin_domainpack_profile(profile_name: str) -> dict[str, Any]:
    """Load built-in domain pack profile by name."""
    return load_mapping_profile(get_builtin_domainpack_profile_path(profile_name))
