"""Load deterministic runtime defaults from config/defaults.json."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .defaults_schema import validate_defaults_payload

ROOT = Path(__file__).resolve().parents[2]
DEFAULTS_PATH = ROOT / "config" / "defaults.json"
DEFAULTS_ENV_VAR = "TONESIGHT_DEFAULTS_PATH"
PACKAGE_DEFAULTS_PATH = Path(__file__).resolve().parent / "defaults_data" / "defaults.json"
PACKAGE_DATA_ROOT = Path(__file__).resolve().parent / "package_data"
PACKAGE_TAXONOMY_PATH = PACKAGE_DATA_ROOT / "taxonomy" / "tone_taxonomy.v1.json"
PACKAGE_GOLDSET_PATH = PACKAGE_DATA_ROOT / "data" / "goldset.jsonl"
PACKAGE_VECTORS_PATH = PACKAGE_DATA_ROOT / "vectors" / "ns8_test_vectors.json"
PACKAGE_GATE_PROFILES_PATH = PACKAGE_DATA_ROOT / "config" / "gate_profiles.json"


def _resolve_config_path(configured: str, *, anchor: Path, packaged_fallback: Path) -> str:
    candidate = Path(configured)
    if candidate.is_absolute():
        if candidate.exists():
            return configured
    else:
        if candidate.exists():
            return configured
        anchored = anchor / candidate
        if anchored.exists():
            return str(anchored)
    if packaged_fallback.exists():
        return str(packaged_fallback)
    return configured


def _resolve_defaults_path(path: Path | None = None) -> Path:
    if path is not None:
        return path
    env_path = os.getenv(DEFAULTS_ENV_VAR)
    if env_path:
        return Path(env_path)
    if DEFAULTS_PATH.exists():
        return DEFAULTS_PATH
    if PACKAGE_DEFAULTS_PATH.exists():
        return PACKAGE_DEFAULTS_PATH
    raise RuntimeError(
        f"Missing defaults config: checked {DEFAULTS_PATH} and {PACKAGE_DEFAULTS_PATH}. "
        f"Set {DEFAULTS_ENV_VAR} to an explicit path."
    )


def _load_defaults(path: Path | None = None) -> dict[str, Any]:
    resolved = _resolve_defaults_path(path)
    try:
        raw = resolved.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing defaults config: {resolved}") from exc
    except OSError as exc:
        raise RuntimeError(f"Unable to read defaults config: {resolved}: {exc}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid defaults config JSON at {resolved}: {exc.msg}") from exc

    try:
        parsed = validate_defaults_payload(payload)
    except ValueError as exc:
        raise RuntimeError(f"Invalid defaults config schema at {resolved}: {exc}") from exc

    anchor = resolved.parent
    parsed["eval"]["taxonomy_path"] = _resolve_config_path(
        parsed["eval"]["taxonomy_path"],
        anchor=anchor,
        packaged_fallback=PACKAGE_TAXONOMY_PATH,
    )
    parsed["artifacts"]["taxonomy_path"] = _resolve_config_path(
        parsed["artifacts"]["taxonomy_path"],
        anchor=anchor,
        packaged_fallback=PACKAGE_TAXONOMY_PATH,
    )
    parsed["artifacts"]["goldset_path"] = _resolve_config_path(
        parsed["artifacts"]["goldset_path"],
        anchor=anchor,
        packaged_fallback=PACKAGE_GOLDSET_PATH,
    )
    parsed["artifacts"]["vectors_path"] = _resolve_config_path(
        parsed["artifacts"]["vectors_path"],
        anchor=anchor,
        packaged_fallback=PACKAGE_VECTORS_PATH,
    )
    return parsed


def resolve_gate_profiles_path(path: str = "config/gate_profiles.json") -> str:
    return _resolve_config_path(path, anchor=ROOT, packaged_fallback=PACKAGE_GATE_PROFILES_PATH)


DEFAULTS = _load_defaults()
EVAL_DEFAULTS = DEFAULTS["eval"]
ARTIFACT_DEFAULTS = DEFAULTS["artifacts"]
