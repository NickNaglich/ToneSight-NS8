import json
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.cli import main
from tonesight_ns8.compare_runner import run_compare


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _mk_run(path: Path, *, run_id: str, dataset_hash: str, pass_rate: float, avg_l1: float, p95_l1: float, rows: list[dict]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _write_json(
        path / "eval_summary.json",
        {
            "run_id": run_id,
            "count_rows": len(rows),
            "threshold_l1": 3,
            "pass_count": int(round(pass_rate * len(rows))),
            "pass_rate": pass_rate,
            "avg_l1": avg_l1,
            "p95_l1": p95_l1,
            "avg_accuracy_l1": None,
        },
    )
    _write_json(
        path / "receipt.json",
        {
            "spec_version": "1.0",
            "run_id": run_id,
            "dataset_path": "data/goldset.jsonl",
            "dataset_hash": dataset_hash,
            "row_count": len(rows),
            "config": {"threshold_l1": 3, "taxonomy_path": "taxonomy/tone_taxonomy.v1.json"},
            "artifacts": {
                "out_jsonl": str(path / "out.jsonl"),
                "eval_summary_json": str(path / "eval_summary.json"),
                "receipt_json": str(path / "receipt.json"),
            },
        },
    )
    _write_jsonl(path / "out.jsonl", rows)


def test_run_compare_metrics_and_regressions():
    root = Path(".agent") / f"tmp_compare_{uuid4().hex}"
    run_a = root / "run_A"
    run_b = root / "run_B"

    rows_a = [
        {"id": "id_1", "label": "empathetic", "compliance_l1": 1, "pass": True},
        {"id": "id_2", "label": "assertive", "compliance_l1": 0, "pass": True},
        {"id": "id_3", "label": "empathetic", "compliance_l1": 2, "pass": True},
    ]
    rows_b = [
        {"id": "id_1", "label": "empathetic", "compliance_l1": 3, "pass": True},
        {"id": "id_2", "label": "assertive", "compliance_l1": 0, "pass": True},
        {"id": "id_3", "label": "empathetic", "compliance_l1": 4, "pass": False},
    ]

    _mk_run(run_a, run_id="run_A", dataset_hash="abc123", pass_rate=1.0, avg_l1=1.0, p95_l1=2.0, rows=rows_a)
    _mk_run(run_b, run_id="run_B", dataset_hash="abc123", pass_rate=0.67, avg_l1=2.33, p95_l1=4.0, rows=rows_b)

    result = run_compare(str(run_a), str(run_b), top_n=1, write_artifact=True)
    summary = result["compare_summary"]

    assert summary["metrics"]["delta_pass_rate"] < 0
    assert summary["metrics"]["delta_avg_l1"] > 0
    assert summary["metrics"]["delta_p95_l1"] > 0
    assert summary["rows"]["count_common_ids"] == 3

    # Stable tie-breaker: same delta_l1 picks lexicographically smaller id first.
    assert summary["top_regressions"][0]["id"] == "id_1"
    assert "empathetic" in summary["per_label_delta"]

    compare_path = Path(result["compare_summary_path"])
    assert compare_path.exists()
    file_payload = json.loads(compare_path.read_text(encoding="utf-8"))
    assert file_payload["metrics"] == summary["metrics"]


def test_cli_compare(capsys):
    root = Path(".agent") / f"tmp_compare_cli_{uuid4().hex}"
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows = [{"id": "id_1", "label": "calm", "compliance_l1": 1, "pass": True}]

    _mk_run(run_a, run_id="run_A", dataset_hash="abc123", pass_rate=1.0, avg_l1=1.0, p95_l1=1.0, rows=rows)
    _mk_run(run_b, run_id="run_B", dataset_hash="abc123", pass_rate=1.0, avg_l1=1.0, p95_l1=1.0, rows=rows)

    rc = main(["compare", str(run_a), str(run_b), "--top-n", "5", "--write"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["compare_summary"]["run_a"]["run_id"] == "run_A"
    assert payload["compare_summary_path"] is not None
