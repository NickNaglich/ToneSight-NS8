import json
import shutil
from pathlib import Path
from uuid import uuid4

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


def _mk_live_run(
    path: Path,
    *,
    run_id: str,
    dataset_hash: str,
    taxonomy_hash: str,
    defaults_spec_version: str,
    provider: str | None = None,
    model_tag: str | None = None,
    model_digest: str | None = None,
    generation_settings: dict | None = None,
) -> None:
    rows = [{"id": "evt1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    path.mkdir(parents=True, exist_ok=True)
    _write_json(
        path / "eval_summary.json",
        {
            "run_id": run_id,
            "count_rows": len(rows),
            "pass_rate": 1.0,
            "avg_l1": 0.0,
            "p95_l1": 0.0,
        },
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
            "provider": provider,
            "model_tag": model_tag,
            "model_digest": model_digest,
            "generation_settings": generation_settings if isinstance(generation_settings, dict) else {},
            "config": {
                "mapping_id": "ns8",
                "mapping_version": "1.0",
                "calibration_path": "",
                "defaults_spec_version": defaults_spec_version,
                "provider": provider,
                "model_tag": model_tag,
                "model_digest": model_digest,
                "generation_settings": generation_settings if isinstance(generation_settings, dict) else {},
            },
        },
    )
    _write_jsonl(path / "out.jsonl", rows)


def test_live_compare_rejects_identity_mismatch():
    root = _temp_dir("tmp_live_compare_compat")
    run_a = root / "run_live_A"
    run_b = root / "run_live_B"
    _mk_live_run(run_a, run_id="run_live_A", dataset_hash="live_hash_a", taxonomy_hash="tax_a", defaults_spec_version="1.0")
    _mk_live_run(run_b, run_id="run_live_B", dataset_hash="live_hash_b", taxonomy_hash="tax_b", defaults_spec_version="2.0")

    payload = run_gate(str(run_a), str(run_b), require_dataset_match=False)
    assert payload["decision"] == "incompatible"
    reasons = {item["reason"] for item in payload["incompatibilities"]}
    assert "taxonomy_identity_mismatch" in reasons
    assert "defaults_schema_version_mismatch" in reasons


def test_live_compare_rejects_pinned_model_identity_mismatch():
    root = _temp_dir("tmp_live_compare_pinned")
    run_a = root / "run_live_A"
    run_b = root / "run_live_B"
    _mk_live_run(
        run_a,
        run_id="run_live_A",
        dataset_hash="same",
        taxonomy_hash="tax_same",
        defaults_spec_version="1.0",
        provider="ollama",
        model_tag="qwen3-coder:latest",
        model_digest="sha256:aaa",
        generation_settings={"temperature": 0, "seed": 7},
    )
    _mk_live_run(
        run_b,
        run_id="run_live_B",
        dataset_hash="same",
        taxonomy_hash="tax_same",
        defaults_spec_version="1.0",
        provider="ollama",
        model_tag="qwen3-coder:latest",
        model_digest="sha256:bbb",
        generation_settings={"temperature": 0, "seed": 7},
    )

    payload = run_gate(str(run_a), str(run_b), require_dataset_match=True, require_pinned_model_identity=True)
    assert payload["decision"] == "incompatible"
    reasons = {item["reason"] for item in payload["incompatibilities"]}
    assert "model_identity_mismatch" in reasons
