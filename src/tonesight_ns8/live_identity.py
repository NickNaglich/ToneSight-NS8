"""Deterministic identity and hashing helpers for LiveEvent envelopes."""

from __future__ import annotations

import hashlib
import json
from typing import Any


VOLATILE_FIELDS = {"timestamp_received"}


def canonical_live_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return canonicalized LiveEvent payload used for stable identity hashing."""
    payload = {k: v for k, v in event.items() if k not in VOLATILE_FIELDS}
    return payload


def stable_event_hash(event: dict[str, Any]) -> str:
    """Compute deterministic hash for a live event excluding volatile fields."""
    canonical = canonical_live_event(event)
    encoded = json.dumps(canonical, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

