import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.cli import main
from tonesight_ns8.compare_runner import run_compare


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


def _mk_run(path: Path, *, run_id: str, rows: list[dict]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _write_json(
        path / "eval_summary.json",
        {
            "run_id": run_id,
            "count_rows": len(rows),
            "threshold_l1": 3,
            "pass_count": sum(1 for row in rows if bool(row.get("pass", False))),
            "pass_rate": sum(1 for row in rows if bool(row.get("pass", False))) / max(1, len(rows)),
            "avg_l1": sum(float(row.get("compliance_l1", 0.0)) for row in rows) / max(1, len(rows)),
            "p95_l1": max(float(row.get("compliance_l1", 0.0)) for row in rows) if rows else 0.0,
        },
    )
    _write_json(
        path / "receipt.json",
        {
            "spec_version": "1.0",
            "run_id": run_id,
            "dataset_hash": "ds123",
            "mapping_id": "ns8",
            "mapping_version": "1.0",
            "taxonomy_hash": "tax123",
            "defaults_spec_version": "1.0",
            "config": {
                "mapping_id": "ns8",
                "mapping_version": "1.0",
                "calibration_path": "",
                "defaults_spec_version": "1.0",
            },
        },
    )
    _write_jsonl(path / "out.jsonl", rows)


def test_run_compare_topology_mode_surfaces_regression_when_l1_is_flat():
    root = _temp_dir("tmp_compare_topology")
    run_a = root / "run_A"
    run_b = root / "run_B"

    target = {"V": 4, "A": 4, "D": 4}
    rows_a = [
        {
            "id": "id_1",
            "label": "calm",
            "target_vad": target,
            "pred_vad": {"V": 3, "A": 3, "D": 4},
            "compliance_l1": 2,
            "delta_v": 1,
            "delta_a": 1,
            "delta_d": 0,
            "pass": True,
        }
    ]
    rows_b = [
        {
            "id": "id_1",
            "label": "calm",
            "target_vad": target,
            "pred_vad": {"V": 2, "A": 4, "D": 4},
            "compliance_l1": 2,
            "delta_v": 2,
            "delta_a": 0,
            "delta_d": 0,
            "pass": True,
        }
    ]
    _mk_run(run_a, run_id="run_A", rows=rows_a)
    _mk_run(run_b, run_id="run_B", rows=rows_b)

    l1_compare = run_compare(str(run_a), str(run_b), distance_mode="l1")
    assert l1_compare["compare_summary"]["distance_mode"] == "l1"
    assert l1_compare["compare_summary"]["top_regressions"] == []

    topology_compare = run_compare(str(run_a), str(run_b), distance_mode="topology")
    assert topology_compare["compare_summary"]["distance_mode"] == "topology"
    assert len(topology_compare["compare_summary"]["top_regressions"]) == 1
    regression = topology_compare["compare_summary"]["top_regressions"][0]
    assert regression["delta_l1"] == 0.0
    assert regression["delta_distance"] > 0.0


def test_cli_compare_accepts_distance_mode(capsys):
    root = _temp_dir("tmp_compare_topology_cli")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows = [
        {
            "id": "id_1",
            "label": "calm",
            "target_vad": {"V": 4, "A": 4, "D": 4},
            "pred_vad": {"V": 4, "A": 4, "D": 4},
            "compliance_l1": 0,
            "delta_v": 0,
            "delta_a": 0,
            "delta_d": 0,
            "pass": True,
        }
    ]
    _mk_run(run_a, run_id="run_A", rows=rows)
    _mk_run(run_b, run_id="run_B", rows=rows)

    rc = main(["compare", str(run_a), str(run_b), "--distance", "topology"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["compare_summary"]["distance_mode"] == "topology"
