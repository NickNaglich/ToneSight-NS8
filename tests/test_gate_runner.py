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
    taxonomy_hash: str = "tax123",
    defaults_hash: str = "def123",
    defaults_spec_version: str = "1.0",
    mapping_id: str = "ns8",
    mapping_version: str = "1.0",
    calibration_path: str | None = None,
    provider: str | None = None,
    model_tag: str | None = None,
    model_digest: str | None = None,
    model_version: str | None = None,
    generation_settings: dict | None = None,
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
            "taxonomy_hash": taxonomy_hash,
            "defaults_hash": defaults_hash,
            "defaults_spec_version": defaults_spec_version,
            "mapping_id": mapping_id,
            "mapping_version": mapping_version,
            "row_count": len(rows),
            "provider": provider,
            "model_tag": model_tag,
            "model_digest": model_digest,
            "model_version": model_version,
            "generation_settings": generation_settings if isinstance(generation_settings, dict) else {},
            "config": {
                "threshold_l1": 3,
                "taxonomy_path": "taxonomy/tone_taxonomy.v1.json",
                "calibration_path": calibration_path,
                "mapping_id": mapping_id,
                "mapping_version": mapping_version,
                "defaults_spec_version": defaults_spec_version,
                "provider": provider,
                "model_tag": model_tag,
                "model_digest": model_digest,
                "model_version": model_version,
                "generation_settings": generation_settings if isinstance(generation_settings, dict) else {},
            },
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
    reasons = {item["reason"] for item in payload["incompatibilities"]}
    assert "dataset_hash_mismatch" in reasons
    assert "spec_version_mismatch" in reasons


def test_run_gate_profile_and_override_thresholds():
    root = _temp_dir("tmp_gate_profile")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows_a = [{"id": "id_1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    rows_b = [{"id": "id_1", "label": "calm", "compliance_l1": 1, "delta_v": 0, "delta_a": 1, "delta_d": 0, "pass": True}]
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
        pass_rate=0.99,
        avg_l1=0.2,
        p95_l1=0.2,
        rows=rows_b,
    )
    payload = run_gate(
        str(run_a),
        str(run_b),
        profile="strict_regression",
        max_avg_l1_delta=0.3,
    )
    assert payload["profile"] == "strict_regression"
    assert payload["thresholds"]["max_avg_l1_delta"] == 0.3


def test_run_gate_incompatible_live_identity_fields():
    root = _temp_dir("tmp_gate_live_identity")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows = [{"id": "id_1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    _mk_run(
        run_a,
        run_id="run_A",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows,
        taxonomy_hash="tax_a",
        defaults_spec_version="1.0",
        mapping_id="ns8",
        mapping_version="1.0",
        calibration_path="",
    )
    _mk_run(
        run_b,
        run_id="run_B",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows,
        taxonomy_hash="tax_b",
        defaults_spec_version="2.0",
        mapping_id="custom",
        mapping_version="9.9",
        calibration_path="config/calib.v2.json",
    )
    payload = run_gate(str(run_a), str(run_b))
    assert payload["decision"] == "incompatible"
    reasons = {item["reason"] for item in payload["incompatibilities"]}
    assert "mapping_id_mismatch" in reasons
    assert "mapping_version_mismatch" in reasons
    assert "taxonomy_identity_mismatch" in reasons
    assert "defaults_schema_version_mismatch" in reasons
    assert "calibration_identity_mismatch" in reasons


def test_run_gate_live_dataset_mismatch_allowed():
    root = _temp_dir("tmp_gate_live_allow_dataset")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows = [{"id": "id_1", "label": "calm", "compliance_l1": 1, "delta_v": 0, "delta_a": 1, "delta_d": 0, "pass": True}]
    _mk_run(
        run_a,
        run_id="run_A",
        dataset_hash="live_a",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=1.0,
        p95_l1=1.0,
        rows=rows,
    )
    _mk_run(
        run_b,
        run_id="run_B",
        dataset_hash="live_b",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=1.0,
        p95_l1=1.0,
        rows=rows,
    )
    payload = run_gate(str(run_a), str(run_b), require_dataset_match=False)
    assert payload["decision"] == "passed"


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


def test_cli_gate_profile(capsys):
    root = _temp_dir("tmp_gate_cli_profile")
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
    rc = main(["gate", "--run-a", str(run_a), "--run-b", str(run_b), "--profile", "support_chat"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["profile"] == "support_chat"


def test_run_gate_require_pinned_identity_missing_is_incompatible():
    root = _temp_dir("tmp_gate_pinned_missing")
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
    payload = run_gate(str(run_a), str(run_b), require_pinned_model_identity=True)
    assert payload["decision"] == "incompatible"
    reasons = {item["reason"] for item in payload["incompatibilities"]}
    assert "pinned_model_identity_missing" in reasons


def test_run_gate_profile_coding_agent_drift_requires_pinned_identity():
    root = _temp_dir("tmp_gate_profile_coding_agent")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows = [{"id": "id_1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    _mk_run(
        run_a,
        run_id="run_A",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows,
        provider="ollama",
        model_tag="qwen3-coder:latest",
        model_digest="sha256:111",
        generation_settings={"temperature": 0, "top_p": 1},
    )
    _mk_run(
        run_b,
        run_id="run_B",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows,
        provider="ollama",
        model_tag="qwen3-coder:latest",
        model_digest="sha256:222",
        generation_settings={"temperature": 0, "top_p": 1},
    )
    payload = run_gate(str(run_a), str(run_b), profile="coding_agent_drift")
    assert payload["decision"] == "incompatible"
    reasons = {item["reason"] for item in payload["incompatibilities"]}
    assert "model_identity_mismatch" in reasons


def test_run_gate_profile_coding_agent_drift_applies_behavioral_thresholds():
    root = _temp_dir("tmp_gate_profile_coding_agent_behavior")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows_a = [
        {
            "id": "id_1",
            "label": "calm",
            "compliance_l1": 0,
            "delta_v": 0,
            "delta_a": 0,
            "delta_d": 0,
            "pass": True,
            "adapter_id": "coding_agent",
            "coding_agent_features": {"lang_mismatch": 0, "test_markers": 1, "tool_call_count": 1},
            "coding_agent_bins": {"verbosity_bin": 2, "tests_bin": 4, "tool_call_bin": 3},
        }
    ]
    rows_b = [
        {
            "id": "id_1",
            "label": "calm",
            "compliance_l1": 0,
            "delta_v": 0,
            "delta_a": 0,
            "delta_d": 0,
            "pass": True,
            "adapter_id": "coding_agent",
            "coding_agent_features": {"lang_mismatch": 1, "test_markers": 0, "tool_call_count": 0},
            "coding_agent_bins": {"verbosity_bin": 6, "tests_bin": 1, "tool_call_bin": 1},
        }
    ]
    _mk_run(
        run_a,
        run_id="run_A",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows_a,
        provider="ollama",
        model_tag="qwen3-coder:latest",
        model_digest="sha256:stable",
        generation_settings={"temperature": 0, "top_p": 1},
    )
    _mk_run(
        run_b,
        run_id="run_B",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows_b,
        provider="ollama",
        model_tag="qwen3-coder:latest",
        model_digest="sha256:stable",
        generation_settings={"temperature": 0, "top_p": 1},
    )
    payload = run_gate(str(run_a), str(run_b), profile="coding_agent_drift")
    assert payload["decision"] == "regressed"
    metrics = {item["metric"] for item in payload["violations"]}
    assert "delta_language_mismatch_rate" in metrics
    assert "delta_tests_presence_rate" in metrics
    assert "delta_tool_call_rate" in metrics
    assert payload["coding_agent_metrics"]["delta"]["language_mismatch_rate"] == 1.0


def test_run_gate_profile_coding_agent_drift_missing_coding_metrics_is_incompatible():
    root = _temp_dir("tmp_gate_profile_coding_agent_missing_metrics")
    run_a = root / "run_A"
    run_b = root / "run_B"
    rows = [{"id": "id_1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    _mk_run(
        run_a,
        run_id="run_A",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows,
        provider="ollama",
        model_tag="qwen3-coder:latest",
        model_digest="sha256:stable",
        generation_settings={"temperature": 0, "top_p": 1},
    )
    _mk_run(
        run_b,
        run_id="run_B",
        dataset_hash="abc123",
        spec_version="1.0",
        pass_rate=1.0,
        avg_l1=0.0,
        p95_l1=0.0,
        rows=rows,
        provider="ollama",
        model_tag="qwen3-coder:latest",
        model_digest="sha256:stable",
        generation_settings={"temperature": 0, "top_p": 1},
    )
    payload = run_gate(str(run_a), str(run_b), profile="coding_agent_drift")
    assert payload["decision"] == "incompatible"
    reasons = {item["reason"] for item in payload["incompatibilities"]}
    assert "coding_agent_metrics_missing" in reasons
