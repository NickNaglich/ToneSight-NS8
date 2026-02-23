import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.data_lint_runner import run_data_lint


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_run_data_lint_clean_goldset_passes():
    payload = run_data_lint("data/goldset.jsonl")
    assert payload["passed"] is True
    assert payload["exit_code"] == 0
    assert payload["violation_count"] == 0
    assert payload["violations"] == []


def test_run_data_lint_detects_structural_and_quality_violations_deterministically():
    root = _temp_dir("tmp_data_lint_bad")
    bad_path = root / "bad.jsonl"
    bad_path.write_text(
        "\n".join(
            [
                '{"id":"dup_1","target_vad":{"V":9,"A":3,"D":3},"tags":["ok"]}',
                '{"id":"dup_1","target_vad":{"V":7,"A":3,"D":3},"tags":["ok"]}',
                '{"target_vad":{"V":7,"A":3,"D":3},"tags":["ok"]}',
                '{"id":"bad_tags","target_vad":{"V":7,"A":3,"D":3},"tags":["ok",0]}',
                '{"id":"broken",',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    payload = run_data_lint(str(bad_path))
    assert payload["passed"] is False
    assert payload["exit_code"] == 2
    assert payload["violation_count"] >= 5
    codes = [row["code"] for row in payload["violations"]]
    assert "invalid_target_vad_bin" in codes
    assert "duplicate_id" in codes
    assert "missing_id" in codes
    assert "invalid_tag_item" in codes
    assert "malformed_json" in codes
    assert [row["line"] for row in payload["violations"]] == sorted(row["line"] for row in payload["violations"])


def test_run_data_lint_writes_summary_json_when_out_path_provided():
    root = _temp_dir("tmp_data_lint_out")
    out_path = root / "lint_summary.json"
    payload = run_data_lint("data/goldset.jsonl", out_path=str(out_path))
    assert payload["lint_summary_path"] == str(out_path)
    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert loaded["passed"] is True
    assert loaded["lint_schema_version"] == "1.0"
