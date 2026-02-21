import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.incident_runner import run_incident


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


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
            "pass_rate": 1.0,
            "avg_l1": sum(float(r.get("compliance_l1", 0.0)) for r in rows) / max(1, len(rows)),
            "p95_l1": max(float(r.get("compliance_l1", 0.0)) for r in rows),
        },
    )
    _write_json(
        path / "receipt.json",
        {
            "spec_version": "1.0",
            "run_id": run_id,
            "dataset_hash": "abc123",
            "taxonomy_hash": "tax123",
            "defaults_hash": "def123",
        },
    )
    _write_jsonl(path / "out.jsonl", rows)
    (path / "report.html").write_text("<html><body>report</body></html>\n", encoding="utf-8")


def test_run_incident_writes_expected_artifact_references():
    root = _temp_dir("tmp_incident")
    run_a = root / "run_A"
    run_b = root / "run_B"
    _mk_run(
        run_a,
        run_id="run_A",
        rows=[{"id": "r1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}],
    )
    _mk_run(
        run_b,
        run_id="run_B",
        rows=[{"id": "r1", "label": "calm", "compliance_l1": 2, "delta_v": 0, "delta_a": 2, "delta_d": 0, "pass": False}],
    )

    payload = run_incident(str(run_a), str(run_b), top_n=10)
    assert Path(payload["compare_summary_path"]).exists()
    assert Path(payload["compare_report_path"]).exists()
    assert Path(payload["triage_output_path"]).exists()
    assert Path(payload["bundle_path"]).exists()
    assert Path(payload["incident_report_path"]).exists()

    report_text = Path(payload["incident_report_path"]).read_text(encoding="utf-8")
    assert "ToneSight Incident Report" in report_text
    assert "triage_export" in report_text
    assert "forensics_bundle" in report_text
