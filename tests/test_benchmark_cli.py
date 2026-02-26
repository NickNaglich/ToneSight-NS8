import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.cli import main


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_cli_benchmark_core_writes_expected_artifacts(capsys):
    out_root = _temp_dir("tmp_benchmark_cli")
    rc = main(
        [
            "benchmark",
            "--suite",
            "core",
            "--out-root",
            str(out_root),
            "--goldset",
            "data/goldset.jsonl",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["suite"] == "core"
    assert payload["sample_count"] > 0

    report_path = Path(payload["artifacts"]["report"])
    assert report_path.exists()
    for key in ("noise_tolerance", "drift_injection", "model_swap_robustness", "baselines", "transition_coherence"):
        artifact_path = Path(payload["artifacts"][key])
        assert artifact_path.exists()

    report_file_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_file_payload["suite"] == "core"
    assert set(report_file_payload["results"]) == {
        "noise_tolerance",
        "drift_injection",
        "model_swap_robustness",
        "baselines",
        "transition_coherence",
    }

    coherence = report_file_payload["results"]["transition_coherence"]
    assert "base" in coherence
    assert "scenarios" in coherence
    assert set(coherence["base"]) == {"ns8", "equal_width", "quantile"}


def test_cli_benchmark_core_is_repeatable(capsys):
    out_root = _temp_dir("tmp_benchmark_repeatable")
    rc_first = main(
        [
            "benchmark",
            "--suite",
            "core",
            "--out-root",
            str(out_root),
            "--goldset",
            "data/goldset.jsonl",
        ]
    )
    first_payload = json.loads(capsys.readouterr().out)
    assert rc_first == 0
    first_report_bytes = Path(first_payload["artifacts"]["report"]).read_bytes()

    rc_second = main(
        [
            "benchmark",
            "--suite",
            "core",
            "--out-root",
            str(out_root),
            "--goldset",
            "data/goldset.jsonl",
        ]
    )
    second_payload = json.loads(capsys.readouterr().out)
    assert rc_second == 0
    second_report_bytes = Path(second_payload["artifacts"]["report"]).read_bytes()

    assert first_payload["artifacts"] == second_payload["artifacts"]
    assert first_report_bytes == second_report_bytes


def test_cli_benchmark_killer_stability_writes_evidence(capsys):
    out_root = _temp_dir("tmp_killer_stability_cli")
    rc = main(
        [
            "benchmark",
            "--suite",
            "killer_stability",
            "--out-root",
            str(out_root),
            "--goldset",
            "data/goldset.jsonl",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["suite"] == "killer_stability"
    evidence_path = Path(payload["artifacts"]["evidence"])
    robustness_path = Path(payload["artifacts"]["robustness_summary"])
    robustness_html_path = Path(payload["artifacts"]["robustness_report_html"])
    assert evidence_path.exists()
    assert robustness_path.exists()
    assert robustness_html_path.exists()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert set(evidence["conditions"]) == {"C1", "C2", "C3", "C4"}
    assert "tonesight" in evidence["separation_ratios"]
    assert "quantile" in evidence["separation_ratios"]
    summary = evidence["robustness_sweep"]["summary"]
    assert "absolute_criteria_pass_rate" in summary
    assert "tonesight_loss_tag_counts" in summary


def test_cli_benchmark_killer_stability_accepts_overrides(capsys):
    out_root = _temp_dir("tmp_killer_stability_cli_overrides")
    rc = main(
        [
            "benchmark",
            "--suite",
            "killer_stability",
            "--out-root",
            str(out_root),
            "--goldset",
            "data/goldset.jsonl",
            "--killer-profiles",
            "default,boundary_jitter",
            "--killer-seeds",
            "0,1",
            "--killer-primary-strength",
            "0.25",
            "--killer-sweep-strengths",
            "0.1,0.2,0.3",
            "--killer-sample-multiplier",
            "2",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["sample_count"] == 500
    evidence_path = Path(payload["artifacts"]["evidence"])
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["config"]["sample_multiplier"] == 2
    assert evidence["config"]["primary_drift_strength"] == 0.25
    assert evidence["config"]["drift_sweep_strengths"] == [0.1, 0.2, 0.3]
    assert evidence["config"]["robustness"]["profiles"] == ["default", "boundary_jitter"]
    assert evidence["config"]["robustness"]["seeds"] == [0, 1]


def test_cli_benchmark_killer_stability_pseudo_real_trace_demo(capsys):
    out_root = _temp_dir("tmp_killer_stability_cli_pseudo_real")
    rc = main(
        [
            "benchmark",
            "--suite",
            "killer_stability",
            "--out-root",
            str(out_root),
            "--goldset",
            "data/pseudo_real_trace.jsonl",
            "--killer-profiles",
            "default,phase_flip_cycle",
            "--killer-seeds",
            "0,1",
            "--killer-sweep-strengths",
            "0.1,0.2",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    evidence = json.loads(Path(payload["artifacts"]["evidence"]).read_text(encoding="utf-8"))
    assert evidence["dataset_path"].replace("\\", "/").endswith("data/pseudo_real_trace.jsonl")
    assert evidence["config"]["robustness"]["profiles"] == ["default", "phase_flip_cycle"]


def test_cli_benchmark_coding_agent_drift_writes_expected_artifacts(capsys):
    out_root = _temp_dir("tmp_coding_agent_drift_cli")
    rc = main(
        [
            "benchmark",
            "--suite",
            "coding_agent_drift",
            "--out-root",
            str(out_root),
            "--coding-baseline-events",
            "tests/fixtures/live_event.coding_agent.python.jsonl",
            "--coding-candidate-events",
            "tests/fixtures/live_event.coding_agent.typescript.jsonl,tests/fixtures/live_event.coding_agent.mismatch.jsonl",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["suite"] == "coding_agent_drift"
    report_path = Path(payload["artifacts"]["report"])
    evidence_path = Path(payload["artifacts"]["evidence"])
    assert report_path.exists()
    assert evidence_path.exists()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["suite"] == "coding_agent_drift"
    assert evidence["baseline"]["count_events"] == 2
    assert len(evidence["candidates"]) == 2
    mismatch_key = next(
        key for key in evidence["candidates"] if key.replace("\\", "/").endswith("live_event.coding_agent.mismatch.jsonl")
    )
    mismatch_metrics = evidence["candidates"][mismatch_key]["metrics"]
    assert mismatch_metrics["language_mismatch_rate"] > 0.0
    assert "gate_ready" in evidence
    assert "aggregate_deltas" in evidence["gate_ready"]
    assert "max_language_mismatch_rate_delta" in evidence["gate_ready"]["aggregate_deltas"]
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert "gate_ready" in report_payload["results"]


def test_cli_benchmark_coding_agent_drift_is_repeatable(capsys):
    out_root = _temp_dir("tmp_coding_agent_drift_repeatable")
    argv = [
        "benchmark",
        "--suite",
        "coding_agent_drift",
        "--out-root",
        str(out_root),
        "--coding-baseline-events",
        "tests/fixtures/live_event.coding_agent.python.jsonl",
        "--coding-candidate-events",
        "tests/fixtures/live_event.coding_agent.typescript.jsonl,tests/fixtures/live_event.coding_agent.mismatch.jsonl",
    ]
    rc_first = main(argv)
    first_payload = json.loads(capsys.readouterr().out)
    assert rc_first == 0
    first_report = Path(first_payload["artifacts"]["report"]).read_bytes()
    first_evidence = Path(first_payload["artifacts"]["evidence"]).read_bytes()

    rc_second = main(argv)
    second_payload = json.loads(capsys.readouterr().out)
    assert rc_second == 0
    second_report = Path(second_payload["artifacts"]["report"]).read_bytes()
    second_evidence = Path(second_payload["artifacts"]["evidence"]).read_bytes()

    assert first_payload["artifacts"] == second_payload["artifacts"]
    assert first_report == second_report
    assert first_evidence == second_evidence
