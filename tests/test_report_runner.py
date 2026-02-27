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


def _mk_min_run(path: Path, *, run_id: str, rows: list[dict]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "eval_summary.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "count_rows": len(rows),
                "pass_rate": 1.0,
                "avg_l1": 0.0,
                "p95_l1": 0.0,
                "summary_schema_version": "1.0",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "receipt.json").write_text(
        json.dumps(
            {
                "spec_version": "1.0",
                "receipt_schema_version": "1.0",
                "run_id": run_id,
                "dataset_hash": "same",
                "taxonomy_hash": "tax",
                "defaults_hash": "def",
                "mapping_id": "ns8",
                "mapping_version": "1.0",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "out.jsonl").write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


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
    assert payload["transition_heatmap"]["available"] is True
    assert payload["transition_heatmap"]["mode"] == "single"
    assert payload["compare_highlights"]["available"] is False
    assert payload["gate_summary"]["available"] is False
    assert report_1["report_path"] == report_2["report_path"]
    assert report_1["transition_heatmap_path"] == report_2["transition_heatmap_path"]
    assert report_1["transition_heatmap_hash"] == report_2["transition_heatmap_hash"] == _sha256_12(
        Path(report_1["transition_heatmap_path"])
    )
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
    assert payload["transition_heatmap"]["available"] is True
    assert payload["transition_heatmap"]["mode"] == "compare"
    heatmap_payload = json.loads(Path(report["transition_heatmap_path"]).read_text(encoding="utf-8"))
    assert heatmap_payload["transition_heatmap_schema_version"] == "1.0"
    assert len(heatmap_payload["run_b"]["matrix_8x8"]) == 8
    assert all(len(row) == 8 for row in heatmap_payload["run_b"]["matrix_8x8"])
    assert "delta_run_b_minus_run_a_8x8" in heatmap_payload


def test_run_report_includes_coding_agent_drift_slices_when_present():
    out_root = _temp_dir("tmp_report_coding_drift")
    run_a = out_root / "run_A"
    run_b = out_root / "run_B"
    rows_a = [
        {
            "id": "evt_1",
            "pred_vad": {"V": 4, "A": 3, "D": 4},
            "target_vad": {"V": 4, "A": 3, "D": 4},
            "compliance_l1": 0,
            "delta_v": 0,
            "delta_a": 0,
            "delta_d": 0,
            "adapter_id": "coding_agent",
            "coding_agent_features": {
                "lang_detected": "python",
                "lang_expected": "python",
                "lang_mismatch": 0,
                "test_markers": 1,
                "tool_calls": 1,
            },
            "coding_agent_bins": {"verbosity_bin": 3, "tests_bin": 4, "tool_call_bin": 4},
        }
    ]
    rows_b = [
        {
            "id": "evt_1",
            "pred_vad": {"V": 4, "A": 3, "D": 4},
            "target_vad": {"V": 4, "A": 3, "D": 4},
            "compliance_l1": 0,
            "delta_v": 0,
            "delta_a": 0,
            "delta_d": 0,
            "adapter_id": "coding_agent",
            "coding_agent_features": {
                "lang_detected": "typescript",
                "lang_expected": "python",
                "lang_mismatch": 1,
                "test_markers": 0,
                "tool_calls": 0,
            },
            "coding_agent_bins": {"verbosity_bin": 6, "tests_bin": 1, "tool_call_bin": 1},
        }
    ]
    _mk_min_run(run_a, run_id="run_A", rows=rows_a)
    _mk_min_run(run_b, run_id="run_B", rows=rows_b)

    payload = run_report(str(run_b), run_a=str(run_a), require_dataset_match=False)["report"]
    assert payload["coding_agent_drift"]["available"] is True
    assert payload["coding_agent_drift"]["run_b"]["language_mismatch_rate"] == 1.0
    assert payload["coding_agent_drift"]["run_a"]["language_mismatch_rate"] == 0.0
    assert payload["coding_agent_drift"]["delta_run_b_minus_run_a"]["language_mismatch_rate"] == 1.0


def test_run_report_supports_signal_mode_artifacts():
    out_root = _temp_dir("tmp_report_signal")
    run_signal = out_root / "run_signal_A"
    run_signal.mkdir(parents=True, exist_ok=True)
    (run_signal / "receipt.json").write_text(
        json.dumps(
            {
                "spec_version": "1.0",
                "receipt_schema_version": "1.0",
                "run_id": "run_signal_A",
                "dataset_hash": "sig123",
                "mapping_profile": "tone_vad",
                "mapping_profile_hash": "abc123",
                "domain_pack": "tone_vad_v1",
                "domain_pack_hash": "def456",
                "quarantine_count_total": 1,
                "quarantine_counts_by_reason": {"MISSING_CHANNEL": 1},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_signal / "metrics_summary.json").write_text(
        json.dumps(
            {
                "run_id": "run_signal_A",
                "metrics_schema_version": "1.0",
                "count_anchor_events": 2,
                "count_quarantine": 1,
                "volatility_mean_step_distance": 0.0,
                "transition_entropy": 0.0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_signal / "anchor_events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "schema": "ns8.signal.anchor_event.v1",
                        "t": "2026-02-27T12:00:00Z",
                        "entity_id": "spk_1",
                        "anchor": {"family": "TLF", "i": 6, "j": 4, "idx": 44, "A": 1},
                        "inputs": {"channels": {"valence_bin": 3, "arousal_bin": 6, "dominance_bin": 4}},
                        "derived": {"step_distance": 0, "transition_type": "initial"},
                    }
                )
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    payload = run_report(str(run_signal))["report"]
    assert payload["run_b"]["run_mode"] == "signal"
    assert payload["signal_layer"]["available"] is True
    assert payload["signal_layer"]["mapping_profile"] == "tone_vad"
    assert payload["signal_layer"]["quarantine_count_total"] == 1
    assert payload["compare_highlights"]["available"] is False
