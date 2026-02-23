import json
import shutil
from pathlib import Path
from uuid import uuid4

import tonesight_ns8.eval_runner as eval_runner_module
from tonesight_ns8.eval_runner import run_eval
from tonesight_ns8.gate_runner import run_gate


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_artifact_contract_required_fields_and_types():
    out_root = _temp_dir("tmp_artifact_contract")
    result = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )

    out_dir = Path(result["out_dir"])
    receipt = json.loads((out_dir / "receipt.json").read_text(encoding="utf-8"))
    summary = json.loads((out_dir / "eval_summary.json").read_text(encoding="utf-8"))
    first_row = json.loads((out_dir / "out.jsonl").read_text(encoding="utf-8").splitlines()[0])

    for field in (
        "spec_version",
        "run_id",
        "dataset_hash",
        "taxonomy_hash",
        "defaults_hash",
        "defaults_spec_version",
        "mapping_id",
        "mapping_version",
    ):
        assert isinstance(receipt[field], str)
        assert receipt[field] != ""

    assert isinstance(summary["count_rows"], int)
    assert isinstance(summary["pass_rate"], float)
    assert isinstance(summary["avg_l1"], float)
    assert isinstance(summary["p95_l1"], float)

    for field, expected_type in (
        ("id", (str, type(None))),
        ("label", (str, type(None))),
        ("target_vad", dict),
        ("pred_vad", dict),
        ("delta_v", int),
        ("delta_a", int),
        ("delta_d", int),
        ("compliance_l1", int),
        ("threshold_margin", int),
        ("pass", bool),
    ):
        assert isinstance(first_row[field], expected_type)


def test_artifact_contract_additive_fields_do_not_break_parsing():
    out_root = _temp_dir("tmp_artifact_additive")
    result = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    out_dir = Path(result["out_dir"])

    receipt_path = out_dir / "receipt.json"
    summary_path = out_dir / "eval_summary.json"
    row_path = out_dir / "out.jsonl"

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in row_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    receipt["x_future_additive_field"] = "ok"
    summary["x_future_additive_metric"] = 0.123
    rows[0]["x_future_additive_explainability"] = {"bucket": "candidate"}

    _write_json(receipt_path, receipt)
    _write_json(summary_path, summary)
    _write_jsonl(row_path, rows)

    reparsed_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    reparsed_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    reparsed_rows = [json.loads(line) for line in row_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert reparsed_receipt["x_future_additive_field"] == "ok"
    assert isinstance(reparsed_summary["x_future_additive_metric"], float)
    assert reparsed_rows[0]["x_future_additive_explainability"]["bucket"] == "candidate"


def test_artifact_contract_legacy_receipt_shape_is_compatible():
    root = _temp_dir("tmp_artifact_legacy")
    run_a = root / "run_A"
    run_b = root / "run_B"
    run_a.mkdir(parents=True, exist_ok=True)
    run_b.mkdir(parents=True, exist_ok=True)

    rows = [{"id": "r1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    summary = {"run_id": "run_A", "count_rows": 1, "pass_rate": 1.0, "avg_l1": 0.0, "p95_l1": 0.0}

    _write_json(run_a / "eval_summary.json", summary)
    _write_json(run_b / "eval_summary.json", {**summary, "run_id": "run_B"})
    _write_jsonl(run_a / "out.jsonl", rows)
    _write_jsonl(run_b / "out.jsonl", rows)

    # Legacy shape: identity fields only in config, no top-level mapping/taxonomy/defaults fields.
    legacy_receipt = {
        "spec_version": "1.0",
        "run_id": "run_A",
        "dataset_hash": "same_dataset",
        "config": {
            "mapping_id": "ns8",
            "mapping_version": "1.0",
            "taxonomy_path": "taxonomy/tone_taxonomy.v1.json",
            "defaults_spec_version": "1.0",
            "calibration_path": "",
        },
    }
    _write_json(run_a / "receipt.json", legacy_receipt)
    _write_json(run_b / "receipt.json", {**legacy_receipt, "run_id": "run_B"})

    payload = run_gate(str(run_a), str(run_b), require_dataset_match=True)
    assert payload["decision"] == "passed"
    assert payload["incompatibilities"] == []


def test_receipt_code_revision_present_when_available(monkeypatch):
    monkeypatch.setattr(eval_runner_module, "get_code_revision", lambda: "deadbeefcafe")
    out_root = _temp_dir("tmp_artifact_code_revision_present")
    result = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    out_dir = Path(result["out_dir"])
    receipt = json.loads((out_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["code_revision"] == "deadbeefcafe"


def test_receipt_code_revision_omitted_when_unavailable(monkeypatch):
    monkeypatch.setattr(eval_runner_module, "get_code_revision", lambda: None)
    out_root = _temp_dir("tmp_artifact_code_revision_absent")
    result = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    out_dir = Path(result["out_dir"])
    receipt = json.loads((out_dir / "receipt.json").read_text(encoding="utf-8"))
    assert "code_revision" not in receipt
