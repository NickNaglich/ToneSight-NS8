import os
import shutil
import time
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.retention import run_retention_purge


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _touch_old(path: Path, days_old: int) -> None:
    ts = time.time() - (days_old * 86400)
    os.utime(path, (ts, ts))


def test_retention_dry_run_skips_bundles_and_captures_by_default():
    out_root = _temp_dir("tmp_retention_dry")
    old_run = out_root / "run_001"
    old_run.mkdir(parents=True, exist_ok=True)
    (old_run / "out.jsonl").write_text("{}", encoding="utf-8")
    _touch_old(old_run, 45)
    _touch_old(old_run / "out.jsonl", 45)

    old_run_with_bundle = out_root / "run_002"
    (old_run_with_bundle / "bundles").mkdir(parents=True, exist_ok=True)
    (old_run_with_bundle / "bundles" / "bundle_marker.txt").write_text("x", encoding="utf-8")
    _touch_old(old_run_with_bundle, 45)
    _touch_old(old_run_with_bundle / "bundles", 45)
    _touch_old(old_run_with_bundle / "bundles" / "bundle_marker.txt", 45)

    old_capture = out_root / "captures" / "capture_001"
    old_capture.mkdir(parents=True, exist_ok=True)
    (old_capture / "events.raw.jsonl").write_text("{}", encoding="utf-8")
    _touch_old(old_capture, 45)
    _touch_old(old_capture / "events.raw.jsonl", 45)

    result = run_retention_purge(out_root=str(out_root), older_than_days=30, dry_run=True)
    actions = {Path(item["path"]).name: item["action"] for item in result["evaluated"]}
    assert actions["run_001"] == "delete"
    assert actions["run_002"] == "skip"
    assert actions["capture_001"] == "skip"
    assert result["would_delete_count"] == 1
    assert result["deleted_count"] == 0
    assert old_run.exists()


def test_retention_apply_deletes_when_explicitly_included():
    out_root = _temp_dir("tmp_retention_apply")
    old_run = out_root / "run_003"
    (old_run / "bundles").mkdir(parents=True, exist_ok=True)
    (old_run / "bundles" / "bundle_marker.txt").write_text("x", encoding="utf-8")
    _touch_old(old_run, 60)
    _touch_old(old_run / "bundles", 60)
    _touch_old(old_run / "bundles" / "bundle_marker.txt", 60)

    old_capture = out_root / "captures" / "capture_003"
    old_capture.mkdir(parents=True, exist_ok=True)
    (old_capture / "events.raw.jsonl").write_text("{}", encoding="utf-8")
    _touch_old(old_capture, 60)
    _touch_old(old_capture / "events.raw.jsonl", 60)

    result = run_retention_purge(
        out_root=str(out_root),
        older_than_days=30,
        dry_run=False,
        include_bundles=True,
        include_captures=True,
    )
    assert result["would_delete_count"] == 2
    assert result["deleted_count"] + result["failed_count"] == 2
