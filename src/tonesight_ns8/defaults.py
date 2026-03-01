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
        return validate_defaults_payload(payload)
    except ValueError as exc:
        raise RuntimeError(f"Invalid defaults config schema at {resolved}: {exc}") from exc


DEFAULTS = _load_defaults()
EVAL_DEFAULTS = DEFAULTS["eval"]
ARTIFACT_DEFAULTS = DEFAULTS["artifacts"]
