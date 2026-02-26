import json
import shutil
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from tonesight_ns8.cli import main
from tonesight_ns8.run_index import run_index, run_index_json
from tonesight_ns8.ui_package_runner import run_ui_package


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _mk_run(path: Path, *, run_id: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _write_json(
        path / "receipt.json",
        {
            "spec_version": "1.0",
            "run_id": run_id,
            "dataset_hash": "ds",
            "taxonomy_hash": "tx",
            "defaults_hash": "df",
            "artifacts": {
                "out_jsonl": str(path / "out.jsonl"),
                "eval_summary_json": str(path / "eval_summary.json"),
                "report_html": str(path / "report.html"),
                "receipt_json": str(path / "receipt.json"),
            },
        },
    )
    _write_json(path / "eval_summary.json", {"run_id": run_id, "pass_rate": 1.0, "count_rows": 1, "avg_l1": 0.0, "p95_l1": 0.0})
    _write_jsonl(path / "out.jsonl", [{"id": "row_1", "pass": True}])
    (path / "report.html").write_text(f"<html><body>{run_id}</body></html>\n", encoding="utf-8")
    (path / "events.raw.jsonl").write_text('{"id":"raw"}\n', encoding="utf-8")


def test_run_ui_package_includes_ui_server_and_safe_artifacts_only_by_default():
    out_root = _temp_dir("tmp_ui_package")
    run_a = out_root / "run_a"
    run_b = out_root / "run_b"
    _mk_run(run_a, run_id="run_a")
    _mk_run(run_b, run_id="run_b")
    _write_json(out_root / "run_b" / "comparisons" / "run_a" / "compare_summary.json", {"delta_pass_rate": -0.1})
    _write_json(out_root / "run_b" / "comparisons" / "run_a" / "gate_result.json", {"decision": "regressed", "exit_code": 2})
    (out_root / "run_b" / "comparisons" / "run_a" / "compare_report.html").write_text("<html>compare</html>\n", encoding="utf-8")
    run_index(str(out_root))
    run_index_json(str(out_root))

    payload = run_ui_package(str(out_root))
    package_path = Path(payload["package_path"])
    assert package_path.exists()
    assert payload["mode"] == "ui_demo_static"
    assert payload["external_safe"] is True

    with ZipFile(package_path, "r") as zipf:
        names = sorted(zipf.namelist())
        assert "ui/index.html" in names
        assert "server/app.py" in names
        assert "runs/index.json" in names
        assert "runs/run_a/receipt.json" in names
        assert "runs/run_b/comparisons/run_a/compare_summary.json" in names
        assert "runs/run_b/comparisons/run_a/gate_result.json" in names
        assert "runs/run_b/comparisons/run_a/compare_report.html" in names
        assert "runs/run_a/out.jsonl" not in names
        assert "runs/run_a/events.raw.jsonl" not in names
        manifest = json.loads(zipf.read("manifest.json").decode("utf-8"))
        assert manifest["file_count"] == payload["file_count"]
        assert manifest["external_safe"] is True


def test_cli_ui_package_writes_zip(capsys):
    out_root = _temp_dir("tmp_ui_package_cli")
    _mk_run(out_root / "run_a", run_id="run_a")
    run_index(str(out_root))
    run_index_json(str(out_root))

    rc = main(["ui-package", "--out-root", str(out_root)])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["mode"] == "ui_demo_static"
    assert Path(payload["package_path"]).exists()
