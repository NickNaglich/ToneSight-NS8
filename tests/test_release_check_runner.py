import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.release_check_runner import run_release_check


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_run_release_check_passes_on_repo_defaults():
    payload = run_release_check()
    assert payload["decision"] == "passed"
    assert payload["failed_checks"] == []
    assert payload["exit_code"] == 0
    names = [row["name"] for row in payload["checks"]]
    assert names == ["dataset_lint", "taxonomy_load", "gate_profiles_config", "nosec_policy"]


def test_run_release_check_fails_on_invalid_dataset():
    root = _temp_dir("tmp_release_check_bad")
    bad_path = root / "bad.jsonl"
    bad_path.write_text('{"id":"dup","target_vad":{"V":9,"A":3,"D":3},"tags":["ok"]}\n', encoding="utf-8")
    payload = run_release_check(goldset_path=str(bad_path))
    assert payload["decision"] == "failed"
    assert payload["exit_code"] == 2
    assert "dataset_lint" in payload["failed_checks"]


def test_run_release_check_writes_output():
    root = _temp_dir("tmp_release_check_out")
    out_path = root / "release_check.json"
    payload = run_release_check(out_path=str(out_path))
    assert payload["release_check_path"] == str(out_path)
    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert loaded["release_check_schema_version"] == "1.0"
