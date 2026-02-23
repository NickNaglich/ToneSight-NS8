"""Deterministic incremental stream-state update and snapshot helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .analytics import summarize_session
from .schema import SegmentRecord

STREAM_SCHEMA_VERSION = "1.0"


def _segment_from_obj(payload: SegmentRecord | dict[str, Any]) -> SegmentRecord:
    if isinstance(payload, SegmentRecord):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("stream segment must be SegmentRecord or object")
    return SegmentRecord(**payload)


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


def new_stream_state(
    *,
    session_id: str,
    arousal_spike_threshold: int = 7,
    drift_window_k: int = 2,
) -> dict[str, Any]:
    """Create an empty deterministic stream state."""
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("session_id must be a non-empty string")
    return {
        "stream_schema_version": STREAM_SCHEMA_VERSION,
        "session_id": session_id,
        "arousal_spike_threshold": int(arousal_spike_threshold),
        "drift_window_k": int(drift_window_k),
        "update_count": 0,
        "segments": [],
    }


def snapshot_stream_state(state: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic session snapshot from persisted stream state."""
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    session_id = state.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("state.session_id must be a non-empty string")
    threshold = int(state.get("arousal_spike_threshold", 7))
    drift_window_k = int(state.get("drift_window_k", 2))
    raw_segments = state.get("segments", [])
    if not isinstance(raw_segments, list):
        raise ValueError("state.segments must be a list")
    segments = [_segment_from_obj(item) for item in raw_segments]
    summary = summarize_session(
        session_id,
        segments,
        arousal_spike_threshold=threshold,
        drift_window_k=drift_window_k,
    )
    return _jsonable(summary)


def run_stream_update(
    *,
    session_id: str | None = None,
    state_path: str | None = None,
    out_state_path: str | None = None,
    segments: list[SegmentRecord | dict[str, Any]] | None = None,
    segments_path: str | None = None,
    arousal_spike_threshold: int = 7,
    drift_window_k: int = 2,
) -> dict[str, Any]:
    """Append deterministic segment batches to state and return snapshot."""
    if segments is None and not segments_path:
        raise ValueError("provide segments or segments_path")
    if segments is not None and segments_path:
        raise ValueError("provide only one of segments or segments_path")

    if state_path:
        state = json.loads(Path(state_path).read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            raise ValueError("state file must contain object")
    else:
        if not session_id:
            raise ValueError("session_id is required when state_path is not provided")
        state = new_stream_state(
            session_id=session_id,
            arousal_spike_threshold=arousal_spike_threshold,
            drift_window_k=drift_window_k,
        )

    batch_payload: list[Any]
    if segments_path:
        payload = json.loads(Path(segments_path).read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("segments_path must contain a JSON list")
        batch_payload = payload
    else:
        batch_payload = list(segments or [])

    normalized_batch = [_jsonable(_segment_from_obj(item)) for item in batch_payload]
    existing_segments = state.get("segments", [])
    if not isinstance(existing_segments, list):
        raise ValueError("state.segments must be a list")
    state["segments"] = existing_segments + normalized_batch
    state["update_count"] = int(state.get("update_count", 0)) + 1
    if "stream_schema_version" not in state:
        state["stream_schema_version"] = STREAM_SCHEMA_VERSION

    snapshot = snapshot_stream_state(state)

    final_state_path = out_state_path or state_path
    if final_state_path:
        target = Path(final_state_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "session_id": state["session_id"],
        "stream_schema_version": state["stream_schema_version"],
        "update_count": state["update_count"],
        "batch_count": len(normalized_batch),
        "state_path": final_state_path,
        "state": state,
        "snapshot": snapshot,
    }
