import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from tonesight_ns8.live_shadow_policy import apply_shadow_policy


def _invalid_event() -> dict:
    return {
        "event": {"event_id": "bad_evt"},
        "error": {"code": "missing_required", "message": "missing required field 'source'"},
    }


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_shadow_policy_fail_raises():
    with pytest.raises(ValueError):
        apply_shadow_policy(
            mode="fail",
            valid_events=[],
            invalid_events=[_invalid_event()],
        )


def test_shadow_policy_drop_counts_only():
    result = apply_shadow_policy(
        mode="drop",
        valid_events=[{"event_id": "ok"}],
        invalid_events=[_invalid_event()],
    )
    assert result["mode"] == "drop"
    assert result["accepted_count"] == 1
    assert result["invalid_count"] == 1
    assert result["quarantined_count"] == 0
    assert result["quarantine_path"] is None


def test_shadow_policy_quarantine_writes_deterministic_jsonl():
    quarantine_path = _temp_dir("tmp_shadow_quarantine") / "q.jsonl"
    invalid = [_invalid_event()]
    result = apply_shadow_policy(
        mode="quarantine",
        valid_events=[],
        invalid_events=invalid,
        quarantine_path=str(quarantine_path),
    )
    assert result["mode"] == "quarantine"
    assert result["quarantined_count"] == 1
    assert result["quarantine_path"] == str(quarantine_path)
    lines = [line for line in quarantine_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["error"]["code"] == "missing_required"
