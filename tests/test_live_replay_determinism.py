import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.live_runner import run_live_capture, run_live_replay, run_live_verify


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_live_capture_and_replay_create_standard_artifacts():
    out_root = _temp_dir("tmp_live_capture_replay")
    capture = run_live_capture("tests/fixtures/live_capture.small.jsonl", out_root=str(out_root))
    assert capture["event_count"] == 2

    replay = run_live_replay(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
    )
    run_dir = Path(replay["out_dir"])
    assert run_dir.exists()
    assert (run_dir / "out.jsonl").exists()
    assert (run_dir / "eval_summary.json").exists()
    assert (run_dir / "report.html").exists()
    assert (run_dir / "receipt.json").exists()
    assert replay["summary"]["count_rows"] == 2
    assert replay["summary"]["invalid_count"] == 0


def test_live_verify_reports_stable_hashes():
    out_root = _temp_dir("tmp_live_verify")
    capture = run_live_capture("tests/fixtures/live_capture.small.jsonl", out_root=str(out_root))
    verify = run_live_verify(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
    )
    assert verify["stable"] is True
    assert verify["mismatched_artifacts"] == []
    assert verify["hashes_first"] == verify["hashes_second"]
    assert verify["exit_code"] == 0


def test_live_replay_quarantine_for_missing_upstream_signal():
    out_root = _temp_dir("tmp_live_quarantine")
    events_path = out_root / "events.invalid_signal.jsonl"
    rows = [
        {
            "event_id": "evt_valid",
            "source": "chat",
            "timestamp_received": "2026-02-20T12:00:00Z",
            "text": "Thanks for your help.",
            "upstream_label": "empathetic",
            "meta": {"session_id": "s1"},
            "privacy_flags": {"contains_pii": False, "allow_store_raw": True},
        },
        {
            "event_id": "evt_missing",
            "source": "chat",
            "timestamp_received": "2026-02-20T12:00:01Z",
            "text": "No upstream signal attached.",
            "meta": {"session_id": "s1"},
            "privacy_flags": {"contains_pii": False, "allow_store_raw": True},
        },
    ]
    events_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    capture = run_live_capture(str(events_path), out_root=str(out_root))
    replay = run_live_replay(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
    )
    assert replay["summary"]["count_rows"] == 1
    assert replay["summary"]["invalid_count"] == 1
    quarantine_path = Path(replay["shadow_policy"]["quarantine_path"])
    assert quarantine_path.exists()
    quarantine_rows = [json.loads(line) for line in quarantine_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(quarantine_rows) == 1
    assert quarantine_rows[0]["error"]["code"] == "missing_upstream_signal"

