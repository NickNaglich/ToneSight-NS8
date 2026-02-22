import json
import shutil
from pathlib import Path
from uuid import uuid4

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
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _mk_run(path: Path, *, run_id: str, dataset_hash: str, taxonomy_hash: str, defaults_spec_version: str) -> None:
    rows = [{"id": "r1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    path.mkdir(parents=True, exist_ok=True)
    _write_json(
        path / "eval_summary.json",
        {"run_id": run_id, "count_rows": 1, "pass_rate": 1.0, "avg_l1": 0.0, "p95_l1": 0.0},
    )
    _write_json(
        path / "receipt.json",
        {
            "spec_version": "1.0",
            "run_id": run_id,
            "dataset_hash": dataset_hash,
            "taxonomy_hash": taxonomy_hash,
            "defaults_spec_version": defaults_spec_version,
            "mapping_id": "ns8",
            "mapping_version": "1.0",
            "config": {
                "mapping_id": "ns8",
                "mapping_version": "1.0",
                "calibration_path": "",
                "defaults_spec_version": defaults_spec_version,
            },
        },
    )
    _write_jsonl(path / "out.jsonl", rows)


def test_eval_receipt_contains_canonical_identity_fields():
    out_root = _temp_dir("tmp_canonical_receipt")
    result = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    receipt = result["receipt"]

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
        assert field in receipt
        assert isinstance(receipt[field], str)
        assert receipt[field] != ""

    assert isinstance(receipt["config"], dict)
    assert receipt["config"]["mapping_id"] == "ns8"
    assert receipt["config"]["mapping_version"] == "1.0"


def test_gate_reports_canonical_identity_mismatch_reasons():
    root = _temp_dir("tmp_canonical_gate")
    run_a = root / "run_A"
    run_b = root / "run_B"

    _mk_run(run_a, run_id="run_A", dataset_hash="same_ds", taxonomy_hash="tax_a", defaults_spec_version="1.0")
    _mk_run(run_b, run_id="run_B", dataset_hash="same_ds", taxonomy_hash="tax_b", defaults_spec_version="2.0")

    payload = run_gate(str(run_a), str(run_b), require_dataset_match=True)
    assert payload["decision"] == "incompatible"
    reasons = {item["reason"] for item in payload["incompatibilities"]}
    assert "taxonomy_identity_mismatch" in reasons
    assert "defaults_schema_version_mismatch" in reasons


def test_gate_allows_dataset_mismatch_when_explicitly_disabled():
    root = _temp_dir("tmp_canonical_dataset_override")
    run_a = root / "run_A"
    run_b = root / "run_B"

    _mk_run(run_a, run_id="run_A", dataset_hash="ds_a", taxonomy_hash="tax_same", defaults_spec_version="1.0")
    _mk_run(run_b, run_id="run_B", dataset_hash="ds_b", taxonomy_hash="tax_same", defaults_spec_version="1.0")

    payload = run_gate(str(run_a), str(run_b), require_dataset_match=False)
    assert payload["decision"] == "passed"
    assert payload["incompatibilities"] == []
