import csv
import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.cli import main
from tonesight_ns8.triage_runner import run_triage


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _mk_run(path: Path, *, run_id: str, dataset_hash: str, rows: list[dict]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _write_json(
        path / "eval_summary.json",
        {
            "run_id": run_id,
            "count_rows": len(rows),
            "threshold_l1": 3,
            "pass_count": sum(1 for row in rows if row.get("pass")),
            "pass_rate": 0.0,
            "avg_l1": 0.0,
            "p95_l1": 0.0,
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


def test_run_triage_single_jsonl_ordering():
    root = _temp_dir("tmp_triage_single")
    run_b = root / "run_B"
    rows = [
        {"id": "id_2", "label": "calm", "tags": ["a"], "delta_v": 1, "delta_a": 0, "delta_d": 0, "threshold_margin": 1, "compliance_l1": 2, "pass": True},
        {"id": "id_1", "label": "calm", "tags": ["b"], "delta_v": 2, "delta_a": 0, "delta_d": 0, "threshold_margin": -1, "compliance_l1": 2, "pass": False},
        {"id": "id_3", "label": "calm", "tags": ["c"], "delta_v": 0, "delta_a": 0, "delta_d": 0, "threshold_margin": 3, "compliance_l1": 0, "pass": True},
    ]
    _mk_run(run_b, run_id="run_B", dataset_hash="abc123", rows=rows)

    payload = run_triage(str(run_b), top_n=3, output_format="jsonl")
    assert payload["mode"] == "single"
    out_path = Path(payload["output_path"])
    assert out_path.exists()
    exported = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [row["id"] for row in exported] == ["id_1", "id_2", "id_3"]
    assert set(["delta_v", "delta_a", "delta_d", "threshold_margin", "label", "tags"]).issubset(exported[0].keys())


def test_run_triage_diff_csv_schema():
    root = _temp_dir("tmp_triage_diff")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows_a = [
        {"id": "id_1", "label": "calm", "tags": ["a"], "delta_v": 0, "delta_a": 0, "delta_d": 0, "threshold_margin": 3, "compliance_l1": 0, "pass": True},
        {"id": "id_2", "label": "firm", "tags": ["b"], "delta_v": 1, "delta_a": 0, "delta_d": 0, "threshold_margin": 2, "compliance_l1": 1, "pass": True},
    ]
    rows_b = [
        {"id": "id_1", "label": "calm", "tags": ["a"], "delta_v": 2, "delta_a": 0, "delta_d": 0, "threshold_margin": -1, "compliance_l1": 2, "pass": False},
        {"id": "id_2", "label": "firm", "tags": ["b"], "delta_v": 1, "delta_a": 2, "delta_d": 0, "threshold_margin": 0, "compliance_l1": 3, "pass": True},
    ]
    _mk_run(run_a, run_id="run_A", dataset_hash="abc123", rows=rows_a)
    _mk_run(run_b, run_id="run_B", dataset_hash="abc123", rows=rows_b)

    payload = run_triage(str(run_b), run_a=str(run_a), top_n=2, output_format="csv")
    assert payload["mode"] == "diff"
    out_path = Path(payload["output_path"])
    assert out_path.exists()
    with out_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert len(rows) == 2
    assert "delta_compliance_l1" in reader.fieldnames
    assert "delta_v" in reader.fieldnames
    assert rows[0]["id"] == "id_2"


def test_cli_triage(capsys):
    root = _temp_dir("tmp_triage_cli")
    run_b = root / "run_B"
    rows = [{"id": "id_1", "label": "calm", "tags": ["t"], "delta_v": 0, "delta_a": 0, "delta_d": 1, "threshold_margin": 2, "compliance_l1": 1, "pass": True}]
    _mk_run(run_b, run_id="run_B", dataset_hash="abc123", rows=rows)
    rc = main(["triage", "--run-b", str(run_b), "--top-n", "1", "--format", "jsonl"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["top_n_returned"] == 1
    assert Path(payload["output_path"]).exists()

