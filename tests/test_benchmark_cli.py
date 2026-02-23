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
    assert evidence_path.exists()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert set(evidence["conditions"]) == {"C1", "C2", "C3", "C4"}
    assert "tonesight" in evidence["separation_ratios"]
    assert "quantile" in evidence["separation_ratios"]
