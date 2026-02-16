"""Tone taxonomy load/validate/lookup helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .errors import InvalidTaxonomy, UnknownToneLabel

LABEL_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_taxonomy(taxonomy: dict) -> None:
    """Validate taxonomy structure and strict VAD domains."""
    if not isinstance(taxonomy, dict):
        raise InvalidTaxonomy("taxonomy must be object")
    if taxonomy.get("N") != 8:
        raise InvalidTaxonomy("taxonomy.N must be 8")
    tones = taxonomy.get("tones")
    if not isinstance(tones, dict) or not tones:
        raise InvalidTaxonomy("taxonomy.tones must be non-empty object")
    for label, vad in tones.items():
        if not isinstance(label, str):
            raise InvalidTaxonomy("tone labels must be strings")
        if not LABEL_RE.match(label):
            raise InvalidTaxonomy(f"tone label must be lowercase snake_case: {label}")
        if not isinstance(vad, dict) or set(vad.keys()) != {"V", "A", "D"}:
            raise InvalidTaxonomy(f"{label} must define exactly V,A,D")
        for key in ("V", "A", "D"):
            value = vad[key]
            if not isinstance(value, int):
                raise InvalidTaxonomy(f"{label}.{key} must be int")
            if value < 1 or value > 8:
                raise InvalidTaxonomy(f"{label}.{key} must be in 1..8")


def load_taxonomy(path: str) -> dict:
    """Load and validate taxonomy JSON from disk."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_taxonomy(data)
    return data


def get_vad(label: str, taxonomy: dict) -> tuple[int, int, int]:
    """Get VAD tuple for a known tone label."""
    tones = taxonomy.get("tones", {})
    if label not in tones:
        raise UnknownToneLabel(label)
    vad = tones[label]
    return (int(vad["V"]), int(vad["A"]), int(vad["D"]))
