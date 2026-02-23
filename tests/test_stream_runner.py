import json
import shutil
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.analytics import summarize_session
from tonesight_ns8.schema import SegmentRecord
from tonesight_ns8.stream_runner import run_stream_update


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _segments() -> list[dict]:
    return [
        {
            "segment_id": "seg_001",
            "speaker_id": "spk_a",
            "start_sec": 0.0,
            "end_sec": 1.0,
            "V": 7,
            "A": 3,
            "D": 3,
            "ns8_A": 2,
        },
        {
            "segment_id": "seg_002",
            "speaker_id": "spk_b",
            "start_sec": 1.0,
            "end_sec": 2.0,
            "V": 3,
            "A": 7,
            "D": 4,
            "ns8_A": 6,
        },
        {
            "segment_id": "seg_003",
            "speaker_id": "spk_a",
            "start_sec": 2.0,
            "end_sec": 3.0,
            "V": 6,
            "A": 4,
            "D": 4,
            "ns8_A": 3,
        },
    ]


def test_stream_update_snapshot_matches_session_summary():
    root = _temp_dir("tmp_stream_summary_match")
    state_path = root / "stream_state.json"
    all_segments = _segments()
    batch_1 = all_segments[:2]
    batch_2 = all_segments[2:]

    first = run_stream_update(
        session_id="sess_stream_01",
        segments=batch_1,
        arousal_spike_threshold=7,
        drift_window_k=2,
        out_state_path=str(state_path),
    )
    second = run_stream_update(
        state_path=str(state_path),
        segments=batch_2,
        out_state_path=str(state_path),
    )

    # Rebuild expected summary from full batch.
    expected = summarize_session(
        "sess_stream_01",
        [SegmentRecord(**row) for row in all_segments],
        arousal_spike_threshold=7,
        drift_window_k=2,
    )
    assert second["snapshot"] == asdict(expected)


def test_stream_update_state_file_roundtrip_is_deterministic():
    root = _temp_dir("tmp_stream_state")
    state_path = root / "stream_state.json"
    seg_path = root / "segments.json"
    seg_payload = _segments()
    seg_path.write_text(json.dumps(seg_payload, indent=2) + "\n", encoding="utf-8")

    first = run_stream_update(
        session_id="sess_stream_file",
        segments_path=str(seg_path),
        out_state_path=str(state_path),
    )
    second = run_stream_update(state_path=str(state_path), segments=[], out_state_path=str(state_path))
    # Empty update batch increments update_count while preserving prior snapshot.
    assert first["snapshot"] == second["snapshot"]
    assert second["update_count"] == first["update_count"] + 1
