"""Validate canonical LiveEvent JSONL envelope for shadow-mode ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("event_id", "source", "timestamp_received", "meta", "privacy_flags")
REQUIRED_VAD_KEYS = ("V", "A", "D")


class LiveEventValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _fail(code: str, message: str) -> None:
    raise LiveEventValidationError(code, message)


def _is_iso8601(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _validate_vad(vad: Any, *, row_num: int, field: str) -> None:
    if not isinstance(vad, dict):
        _fail("invalid_type", f"row {row_num}: {field} must be an object")
    for key in REQUIRED_VAD_KEYS:
        value = vad.get(key)
        if not isinstance(value, int):
            _fail("invalid_type", f"row {row_num}: {field}.{key} must be int")
        if value < 1 or value > 8:
            _fail("invalid_range", f"row {row_num}: {field}.{key} must be in 1..8")


def _validate_segments(segments: Any, *, row_num: int) -> None:
    if not isinstance(segments, list) or not segments:
        _fail("invalid_type", f"row {row_num}: segments must be a non-empty list")
    for i, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            _fail("invalid_type", f"row {row_num}: segments[{i}] must be an object")
        sid = segment.get("id")
        text = segment.get("text")
        if not isinstance(sid, str) or not sid.strip():
            _fail("invalid_type", f"row {row_num}: segments[{i}].id must be non-empty string")
        if not isinstance(text, str) or not text.strip():
            _fail("invalid_type", f"row {row_num}: segments[{i}].text must be non-empty string")


def _validate_event(payload: dict[str, Any], *, row_num: int) -> None:
    for key in REQUIRED_FIELDS:
        if key not in payload:
            _fail("missing_required", f"row {row_num}: missing required field '{key}'")

    event_id = payload["event_id"]
    if not isinstance(event_id, str) or not event_id.strip():
        _fail("invalid_type", f"row {row_num}: event_id must be non-empty string")

    source = payload["source"]
    if not isinstance(source, str) or not source.strip():
        _fail("invalid_type", f"row {row_num}: source must be non-empty string")

    timestamp_received = payload["timestamp_received"]
    if not isinstance(timestamp_received, str) or not _is_iso8601(timestamp_received):
        _fail("invalid_timestamp", f"row {row_num}: timestamp_received must be ISO-8601 string")

    timestamp_emitted = payload.get("timestamp_emitted")
    if timestamp_emitted is not None:
        if not isinstance(timestamp_emitted, str) or not _is_iso8601(timestamp_emitted):
            _fail("invalid_timestamp", f"row {row_num}: timestamp_emitted must be ISO-8601 string")

    meta = payload["meta"]
    if not isinstance(meta, dict):
        _fail("invalid_type", f"row {row_num}: meta must be an object")
    for key in ("session_id", "agent_id", "user_id"):
        if key in meta and (not isinstance(meta[key], str) or not str(meta[key]).strip()):
            _fail("invalid_type", f"row {row_num}: meta.{key} must be non-empty string when present")

    privacy_flags = payload["privacy_flags"]
    if not isinstance(privacy_flags, dict):
        _fail("invalid_type", f"row {row_num}: privacy_flags must be an object")
    for key in ("contains_pii", "allow_store_raw"):
        value = privacy_flags.get(key)
        if not isinstance(value, bool):
            _fail("invalid_type", f"row {row_num}: privacy_flags.{key} must be boolean")

    has_text = isinstance(payload.get("text"), str) and bool(payload.get("text", "").strip())
    has_segments = payload.get("segments") is not None
    if not has_text and not has_segments:
        _fail("content_missing", f"row {row_num}: either text or segments is required")
    if has_segments:
        _validate_segments(payload.get("segments"), row_num=row_num)

    if "upstream_vad" in payload and payload.get("upstream_vad") is not None:
        _validate_vad(payload.get("upstream_vad"), row_num=row_num, field="upstream_vad")

    if "upstream_label" in payload and payload.get("upstream_label") is not None:
        label = payload.get("upstream_label")
        if not isinstance(label, str) or not label.strip():
            _fail("invalid_type", f"row {row_num}: upstream_label must be non-empty string when present")


def validate_live_event_file(path: Path) -> None:
    if not path.exists():
        _fail("file_not_found", f"missing live event file: {path}")

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
            _fail("invalid_json", f"row {row_num}: invalid JSON ({exc.msg})")
        if not isinstance(payload, dict):
            _fail("row_not_object", f"row {row_num}: row must be a JSON object")
        _validate_event(payload, row_num=row_num)
    if row_count == 0:
        _fail("empty_file", "live event file must contain at least one non-empty row")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ToneSight LiveEvent JSONL contract.")
    parser.add_argument("path", nargs="?", default="tests/fixtures/live_event.valid.jsonl")
    args = parser.parse_args(argv)
    target = Path(args.path)
    try:
        validate_live_event_file(target)
    except LiveEventValidationError as exc:
        payload = {
            "valid": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        }
        print(json.dumps(payload, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps({"valid": True, "path": str(target)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

