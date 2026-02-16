import json
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.eval_compare_runner import run_eval_compare
from tonesight_ns8.eval_runner import run_eval


def test_run_eval_writes_artifacts():
    out_root = Path(".agent") / f"tmp_runs_{uuid4().hex}"
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
    receipt_json = run_dir / "receipt.json"
    assert out_jsonl.exists()
    assert summary_json.exists()
    assert receipt_json.exists()

    lines = out_jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == expected_rows

    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    assert summary["count_rows"] == expected_rows
    assert summary["threshold_l1"] == 3
    assert 0.0 <= summary["pass_rate"] <= 1.0

    receipt = json.loads(receipt_json.read_text(encoding="utf-8"))
    assert receipt["run_id"] == run_id
    assert receipt["row_count"] == expected_rows
    assert set(receipt["artifacts"].keys()) == {"out_jsonl", "eval_summary_json", "receipt_json"}


def test_run_eval_with_calibration_override():
    root = Path(".agent") / f"tmp_calib_{uuid4().hex}"
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
    out_root = Path(".agent") / f"tmp_eval_compare_{uuid4().hex}"
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
    assert second["previous_run"] is not None
    assert second["compare"] is not None
