import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.cli import main
from tonesight_ns8.trend_runner import run_trend


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


def _mk_run(path: Path, *, run_id: str, dataset_hash: str, spec_version: str, pass_rate: float, avg_l1: float, p95_l1: float, rows: list[dict]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _write_json(
        path / "eval_summary.json",
        {
            "run_id": run_id,
            "count_rows": len(rows),
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
            "dataset_hash": dataset_hash,
        },
    )
    _write_jsonl(path / "out.jsonl", rows)


def test_run_trend_ordering_and_deltas():
    out_root = _temp_dir("tmp_trend_runs")
    rows = [{"id": "id_1", "source": "s1", "compliance_l1": 1, "pass": True}]
    _mk_run(out_root / "x2", run_id="run_20260101T000002Z_x", dataset_hash="abc123", spec_version="1.0", pass_rate=0.8, avg_l1=1.2, p95_l1=2.0, rows=rows)
    _mk_run(out_root / "x1", run_id="run_20260101T000001Z_x", dataset_hash="abc123", spec_version="1.0", pass_rate=0.9, avg_l1=1.0, p95_l1=1.5, rows=rows)

    payload = run_trend(str(out_root))
    assert payload["run_count"] == 2
    assert [r["run_id"] for r in payload["runs"]] == ["run_20260101T000001Z_x", "run_20260101T000002Z_x"]
    assert payload["runs"][1]["delta_pass_rate_vs_prev"] == -0.09999999999999998
    assert payload["runs"][1]["delta_avg_l1_vs_prev"] == 0.19999999999999996
    assert payload["runs"][1]["delta_p95_l1_vs_prev"] == 0.5
    assert Path(payload["trend_summary_path"]).exists()


def test_run_trend_group_summary_and_incompatible_skip():
    out_root = _temp_dir("tmp_trend_group")
    rows_a = [
        {"id": "id_1", "source": "agent_a", "compliance_l1": 1, "pass": True},
        {"id": "id_2", "source": "agent_a", "compliance_l1": 3, "pass": False},
        {"id": "id_3", "source": "", "compliance_l1": 2, "pass": True},
    ]
    rows_b = [{"id": "id_4", "source": "agent_b", "compliance_l1": 1, "pass": True}]
    _mk_run(out_root / "a", run_id="run_20260101T000001Z_x", dataset_hash="abc123", spec_version="1.0", pass_rate=0.6, avg_l1=2.0, p95_l1=3.0, rows=rows_a)
    _mk_run(out_root / "b", run_id="run_20260101T000002Z_x", dataset_hash="def456", spec_version="1.0", pass_rate=1.0, avg_l1=1.0, p95_l1=1.0, rows=rows_b)

    payload = run_trend(str(out_root), group_by="source")
    first_groups = payload["runs"][0]["group_summary"]
    assert "__missing__" in first_groups
    assert "agent_a" in first_groups
    assert first_groups["agent_a"]["count"] == 2.0
    assert first_groups["agent_a"]["fail_rate"] == 0.5
    assert payload["runs"][1]["delta_skipped_reason"] == "incompatible_prev_run"


def test_cli_trend(capsys):
    out_root = _temp_dir("tmp_trend_cli")
    rows = [{"id": "id_1", "agent": "a1", "compliance_l1": 1, "pass": True}]
    _mk_run(out_root / "r1", run_id="run_20260101T000001Z_x", dataset_hash="abc123", spec_version="1.0", pass_rate=1.0, avg_l1=1.0, p95_l1=1.0, rows=rows)
    rc = main(["trend", "--out-root", str(out_root), "--group-by", "agent"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["group_by"] == "agent"
    assert Path(payload["trend_summary_path"]).exists()

