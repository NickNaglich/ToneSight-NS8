import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.cli import main
from tonesight_ns8.gate_runner import run_gate


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


def _mk_run(
    path: Path,
    *,
    run_id: str,
    dataset_hash: str,
    spec_version: str,
    pass_rate: float,
    avg_l1: float,
    p95_l1: float,
    rows: list[dict],
) -> None:
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
        },
    )
    _write_json(
        path / "receipt.json",
        {
            "spec_version": spec_version,
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


def test_run_gate_passed():
    root = _temp_dir("tmp_gate_pass")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows = [{"id": "id_1", "label": "calm", "compliance_l1": 1, "delta_v": 0, "delta_a": 1, "delta_d": 0, "pass": True}]
    _mk_run(
        run_a,
        run_id="run_A",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=1.0,
        p95_l1=1.0,
        rows=rows,
    )
    _mk_run(
        run_b,
        run_id="run_B",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=1.0,
        p95_l1=1.0,
        rows=rows,
    )
    payload = run_gate(str(run_a), str(run_b))
    assert payload["decision"] == "passed"
    assert payload["violations"] == []
    assert payload["incompatibilities"] == []
    assert payload["exit_code"] == 0


def test_run_gate_regressed():
    root = _temp_dir("tmp_gate_regress")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows_a = [{"id": "id_1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    rows_b = [{"id": "id_1", "label": "calm", "compliance_l1": 2, "delta_v": 0, "delta_a": 2, "delta_d": 0, "pass": False}]
    _mk_run(
        run_a,
        run_id="run_A",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows_a,
    )
    _mk_run(
        run_b,
        run_id="run_B",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=0.0,
        avg_l1=2.0,
        p95_l1=2.0,
        rows=rows_b,
    )
    payload = run_gate(str(run_a), str(run_b))
    assert payload["decision"] == "regressed"
    assert payload["exit_code"] == 2
    assert len(payload["violations"]) == 3


def test_run_gate_incompatible():
    root = _temp_dir("tmp_gate_incompat")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows = [{"id": "id_1", "label": "calm", "compliance_l1": 1, "delta_v": 0, "delta_a": 1, "delta_d": 0, "pass": True}]
    _mk_run(
        run_a,
        run_id="run_A",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=1.0,
        p95_l1=1.0,
        rows=rows,
    )
    _mk_run(
        run_b,
        run_id="run_B",
        dataset_hash="def456",
        spec_version="9.9",
        pass_rate=1.0,
        avg_l1=1.0,
        p95_l1=1.0,
        rows=rows,
    )
    payload = run_gate(str(run_a), str(run_b))
    assert payload["decision"] == "incompatible"
    assert payload["exit_code"] == 3
    assert len(payload["incompatibilities"]) == 2


def test_cli_gate_exit_codes(capsys):
    root = _temp_dir("tmp_gate_cli")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows_a = [{"id": "id_1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    rows_b = [{"id": "id_1", "label": "calm", "compliance_l1": 4, "delta_v": 1, "delta_a": 2, "delta_d": 1, "pass": False}]
    _mk_run(
        run_a,
        run_id="run_A",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows_a,
    )
    _mk_run(
        run_b,
        run_id="run_B",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=0.0,
        avg_l1=4.0,
        p95_l1=4.0,
        rows=rows_b,
    )
    rc = main(["gate", "--run-a", str(run_a), "--run-b", str(run_b)])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["decision"] == "regressed"

