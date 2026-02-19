import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.eval_compare_runner import run_eval_compare
from tonesight_ns8.eval_runner import run_eval


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_run_eval_writes_artifacts():
    out_root = _temp_dir("tmp_runs")
    goldset_path = Path("data/goldset.jsonl")
    expected_rows = sum(1 for line in goldset_path.read_text(encoding="utf-8").splitlines() if line.strip())
    result = run_eval(
        str(goldset_path),
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )

    run_id = result["run_id"]
    run_dir = out_root / run_id
    assert run_dir.exists()

    out_jsonl = run_dir / "out.jsonl"
    summary_json = run_dir / "eval_summary.json"
    report_html = run_dir / "report.html"
    receipt_json = run_dir / "receipt.json"
    assert out_jsonl.exists()
    assert summary_json.exists()
    assert report_html.exists()
    assert receipt_json.exists()

    lines = out_jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == expected_rows
    first_row = json.loads(lines[0])
    assert first_row["delta_v"] >= 0
    assert first_row["delta_a"] >= 0
    assert first_row["delta_d"] >= 0
    assert first_row["threshold_margin"] == 3 - first_row["compliance_l1"]
    assert first_row["delta_v"] + first_row["delta_a"] + first_row["delta_d"] == first_row["compliance_l1"]

    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    assert summary["count_rows"] == expected_rows
    assert summary["threshold_l1"] == 3
    assert 0.0 <= summary["pass_rate"] <= 1.0
    assert summary["fail_count"] == summary["count_rows"] - summary["pass_count"]
    assert summary["fail_rate"] == 1.0 - summary["pass_rate"]
    assert summary["max_l1"] >= summary["median_l1"] >= 0.0
    assert summary["count_with_gold_vad"] + summary["count_without_gold_vad"] == summary["count_rows"]

    receipt = json.loads(receipt_json.read_text(encoding="utf-8"))
    assert receipt["run_id"] == run_id
    assert receipt["row_count"] == expected_rows
    assert len(receipt["taxonomy_hash"]) == 12
    assert len(receipt["defaults_hash"]) == 12
    assert set(receipt["artifacts"].keys()) == {"out_jsonl", "eval_summary_json", "report_html", "receipt_json"}

    html_text = report_html.read_text(encoding="utf-8")
    assert "ToneSight Eval Report" in html_text
    assert run_id in html_text
    assert "rows_with_label" in html_text
    assert "rows_with_gold_vad" in html_text
    assert "distinct_labels" in html_text
    assert "p50_l1" in html_text
    assert "p99_l1" in html_text
    assert "l1_bucket_7_plus" in html_text
    assert "mae_v_gold" in html_text
    assert "mae_a_gold" in html_text
    assert "mae_d_gold" in html_text
    assert "PRESENTATION_PRESET" in html_text
    assert "mode')==='present'" in html_text


def test_run_eval_with_calibration_override():
    root = _temp_dir("tmp_calib")
    root.mkdir(parents=True, exist_ok=True)
    goldset = root / "goldset.jsonl"
    calibration = root / "calibration.json"
    goldset.write_text(
        (
            '{"id":"x1","label":"calm","target_vad":{"V":7,"A":7,"D":7},"gold_vad":{"V":7,"A":7,"D":7}}\n'
        ),
        encoding="utf-8",
    )
    calibration.write_text(
        json.dumps(
            {
                "version": "1.0",
                "label_overrides": {"calm": {"V": 7, "A": 7, "D": 7}},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    base = run_eval(
        str(goldset),
        out_root=str(root / "runs_base"),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    tuned = run_eval(
        str(goldset),
        out_root=str(root / "runs_tuned"),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        calibration_path=str(calibration),
    )
    assert tuned["summary"]["avg_l1"] < base["summary"]["avg_l1"]


def test_run_eval_compare_uses_previous_run():
    out_root = _temp_dir("tmp_eval_compare")
    first = run_eval_compare(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    second = run_eval_compare(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    assert first["previous_run"] is None
    assert first["compare_skipped_reason"] == "no_prior_runs"
    assert first["incompatible_previous_runs"] == []
    assert second["previous_run"] is not None
    assert second["compare_skipped_reason"] is None
    assert second["compare"] is not None


def test_run_eval_compare_skips_incompatible_spec_version():
    out_root = _temp_dir("tmp_eval_compare_spec_mismatch")
    first = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    first_receipt_path = Path(first["out_dir"]) / "receipt.json"
    receipt = json.loads(first_receipt_path.read_text(encoding="utf-8"))
    receipt["spec_version"] = "9.9"
    first_receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    second = run_eval_compare(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    assert second["previous_run"] is None
    assert second["compare"] is None
    assert second["compare_skipped_reason"] == "no_compatible_prior_run"
    assert second["incompatible_previous_runs"]
    assert second["incompatible_previous_runs"][0]["reason"] == "spec_version_mismatch"
