import hashlib
import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.report_runner import run_report
from tonesight_ns8.eval_runner import run_eval


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _sha256_12(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def test_run_report_single_run_is_deterministic():
    out_root = _temp_dir("tmp_report_single")
    eval_payload = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    run_b = str(out_root / eval_payload["run_id"])

    report_1 = run_report(run_b)
    report_2 = run_report(run_b)

    report_path = Path(report_1["report_path"])
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["report_schema_version"] == "1.0"
    assert payload["compare_highlights"]["available"] is False
    assert payload["gate_summary"]["available"] is False
    assert report_1["report_path"] == report_2["report_path"]
    assert report_1["report_hash"] == report_2["report_hash"] == _sha256_12(report_path)


def test_run_report_with_compare_and_gate_highlights():
    out_root = _temp_dir("tmp_report_compare")
    eval_a = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    eval_b = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=2,
    )
    run_a = str(out_root / eval_a["run_id"])
    run_b = str(out_root / eval_b["run_id"])

    report = run_report(run_b, run_a=run_a, top_n=5)
    report_path = Path(report["report_path"])
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["compare_highlights"]["available"] is True
    assert payload["gate_summary"]["available"] is True
    assert payload["compare_highlights"]["distance_mode"] == "l1"
    assert payload["compare_highlights"]["regression_coverage"]["top_n_requested"] == 5
    assert payload["gate_summary"]["decision"] in {"passed", "regressed", "incompatible"}
