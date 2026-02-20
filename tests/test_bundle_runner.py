import json
import shutil
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from tonesight_ns8.bundle_runner import run_bundle
from tonesight_ns8.cli import main


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


def _mk_run(path: Path, *, run_id: str, dataset_hash: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    rows = [{"id": "id_1", "label": "calm", "compliance_l1": 1, "delta_v": 0, "delta_a": 1, "delta_d": 0, "threshold_margin": 2, "pass": True}]
    _write_json(path / "eval_summary.json", {"run_id": run_id, "count_rows": 1, "pass_rate": 1.0, "avg_l1": 1.0, "p95_l1": 1.0})
    _write_json(
        path / "receipt.json",
        {
            "spec_version": "1.0",
            "run_id": run_id,
            "dataset_path": "data/goldset.jsonl",
            "dataset_hash": dataset_hash,
            "row_count": 1,
            "config": {"threshold_l1": 3, "taxonomy_path": "taxonomy/tone_taxonomy.v1.json"},
            "artifacts": {
                "out_jsonl": str(path / "out.jsonl"),
                "eval_summary_json": str(path / "eval_summary.json"),
                "report_html": str(path / "report.html"),
                "receipt_json": str(path / "receipt.json"),
            },
        },
    )
    _write_jsonl(path / "out.jsonl", rows)
    (path / "report.html").write_text("<!doctype html><html><body>report</body></html>\n", encoding="utf-8")


def _mk_compare(run_b: Path, run_a: Path) -> None:
    compare_root = run_b / "comparisons" / run_a.name
    compare_root.mkdir(parents=True, exist_ok=True)
    _write_json(compare_root / "compare_summary.json", {"spec_version": "1.0"})
    (compare_root / "compare_report.html").write_text("<!doctype html><html><body>compare</body></html>\n", encoding="utf-8")


def test_run_bundle_run_only_and_manifest_deterministic():
    root = _temp_dir("tmp_bundle_run_only")
    run_b = root / "run_B"
    _mk_run(run_b, run_id="run_B", dataset_hash="abc123")

    out_zip = root / "bundle.zip"
    payload1 = run_bundle(str(run_b), out_path=str(out_zip))
    payload2 = run_bundle(str(run_b), out_path=str(out_zip))
    assert payload1["mode"] == "run_only"
    assert payload1["manifest"] == payload2["manifest"]

    with ZipFile(out_zip, "r") as zf:
        names = sorted(zf.namelist())
        assert names == ["manifest.json", "run/eval_summary.json", "run/out.jsonl", "run/receipt.json", "run/report.html"]
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["file_count"] == 4
        assert manifest["external_safe"] is True
        assert len(manifest["files"]) == 4
        assert all("source_path" not in item for item in manifest["files"])


def test_run_bundle_with_compare_artifacts():
    root = _temp_dir("tmp_bundle_compare")
    run_a = root / "run_A"
    run_b = root / "run_B"
    _mk_run(run_a, run_id="run_A", dataset_hash="abc123")
    _mk_run(run_b, run_id="run_B", dataset_hash="abc123")
    _mk_compare(run_b, run_a)

    payload = run_bundle(str(run_b), run_a=str(run_a))
    bundle_path = Path(payload["bundle_path"])
    assert payload["mode"] == "run_compare"
    assert bundle_path.exists()
    with ZipFile(bundle_path, "r") as zf:
        names = sorted(zf.namelist())
        assert "compare/compare_summary.json" in names
        assert "compare/compare_report.html" in names
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["file_count"] == 6


def test_run_bundle_include_source_paths():
    root = _temp_dir("tmp_bundle_source_paths")
    run_b = root / "run_B"
    _mk_run(run_b, run_id="run_B", dataset_hash="abc123")

    out_zip = root / "bundle_with_paths.zip"
    run_bundle(str(run_b), out_path=str(out_zip), include_source_paths=True)
    with ZipFile(out_zip, "r") as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
    assert manifest["external_safe"] is False
    assert all("source_path" in item for item in manifest["files"])


def test_cli_bundle(capsys):
    root = _temp_dir("tmp_bundle_cli")
    run_b = root / "run_B"
    _mk_run(run_b, run_id="run_B", dataset_hash="abc123")
    rc = main(["bundle", "--run-b", str(run_b)])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["mode"] == "run_only"
    assert Path(payload["bundle_path"]).exists()
    assert payload["external_safe"] is True
