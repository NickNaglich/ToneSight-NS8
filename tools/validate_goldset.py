"""Validate deterministic goldset JSONL structure and basic quality constraints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = ("id", "target_vad", "gold_vad", "label", "tags")
REQUIRED_VAD_KEYS = ("V", "A", "D")


def _fail(message: str) -> None:
    raise ValueError(message)


def _validate_vad(vad: Any, *, row_num: int, field: str) -> None:
    if not isinstance(vad, dict):
        _fail(f"row {row_num}: {field} must be an object")
    for key in REQUIRED_VAD_KEYS:
        value = vad.get(key)
        if not isinstance(value, int):
            _fail(f"row {row_num}: {field}.{key} must be int")
        if value < 1 or value > 8:
            _fail(f"row {row_num}: {field}.{key} must be in 1..8")


def validate_goldset(path: Path) -> None:
    if not path.exists():
        _fail(f"missing goldset file: {path}")

    seen_ids: set[str] = set()
    lines = path.read_text(encoding="utf-8").splitlines()
    row_count = 0
    for row_num, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        row_count += 1
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            _fail(f"row {row_num}: invalid JSON ({exc.msg})")
        if not isinstance(payload, dict):
            _fail(f"row {row_num}: row must be a JSON object")

        for key in REQUIRED_TOP_LEVEL:
            if key not in payload:
                _fail(f"row {row_num}: missing required field '{key}'")

        row_id = str(payload["id"])
        if row_id in seen_ids:
            _fail(f"row {row_num}: duplicate id '{row_id}'")
        seen_ids.add(row_id)

        _validate_vad(payload["target_vad"], row_num=row_num, field="target_vad")
        _validate_vad(payload["gold_vad"], row_num=row_num, field="gold_vad")

        label = payload["label"]
        if not isinstance(label, str) or not label.strip():
            _fail(f"row {row_num}: label must be non-empty string")

        tags = payload["tags"]
        if not isinstance(tags, list) or not tags:
            _fail(f"row {row_num}: tags must be a non-empty list")
        if not all(isinstance(t, str) and t.strip() for t in tags):
            _fail(f"row {row_num}: tags must contain only non-empty strings")

        # Tag policy constraints for deterministic eval strata.
        tag_set = set(tags)
        if "hard_negative" in tag_set and "mismatch" not in tag_set:
            _fail(f"row {row_num}: hard_negative rows must include mismatch tag")
        if "boundary" in tag_set and not (
            {"structured_strata", "positive_anchor", "negative_anchor"} & tag_set
        ):
            _fail(f"row {row_num}: boundary rows must include structured or anchor tag")

    if row_count == 0:
        _fail("goldset must contain at least one non-empty row")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ToneSight goldset JSONL contract.")
    parser.add_argument("path", nargs="?", default="data/goldset.jsonl")
    args = parser.parse_args(argv)
    try:
        validate_goldset(Path(args.path))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"goldset valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
