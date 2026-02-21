"""Deterministic canary evaluator for baseline-vs-candidate replay."""

from __future__ import annotations

from typing import Any

from .compare_runner import run_compare
from .gate_runner import run_gate
from .live_runner import run_live_replay


def run_canary(
    capture: str,
    *,
    baseline_out_root: str = "runs/canary/baseline",
    candidate_out_root: str = "runs/canary/candidate",
    baseline_taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json",
    candidate_taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json",
    baseline_threshold_l1: int = 3,
    candidate_threshold_l1: int = 3,
    shadow_strict: str = "quarantine",
    redact: bool = True,
    top_n: int = 10,
    profile: str | None = None,
    gate_profiles_path: str = "config/gate_profiles.json",
    min_pass_rate_delta: float | None = None,
    max_avg_l1_delta: float | None = None,
    max_p95_l1_delta: float | None = None,
    allow_dataset_mismatch: bool = False,
) -> dict[str, Any]:
    """Replay one capture through baseline/candidate flows and gate the delta."""
    baseline = run_live_replay(
        capture,
        out_root=baseline_out_root,
        taxonomy_path=baseline_taxonomy_path,
        threshold_l1=baseline_threshold_l1,
        shadow_strict=shadow_strict,
        redact=redact,
    )
    candidate = run_live_replay(
        capture,
        out_root=candidate_out_root,
        taxonomy_path=candidate_taxonomy_path,
        threshold_l1=candidate_threshold_l1,
        shadow_strict=shadow_strict,
        redact=redact,
    )

    gate = run_gate(
        baseline["out_dir"],
        candidate["out_dir"],
        profile=profile,
        gate_profiles_path=gate_profiles_path,
        min_pass_rate_delta=min_pass_rate_delta,
        max_avg_l1_delta=max_avg_l1_delta,
        max_p95_l1_delta=max_p95_l1_delta,
        top_n=top_n,
        require_dataset_match=not allow_dataset_mismatch,
    )
    compare = run_compare(
        baseline["out_dir"],
        candidate["out_dir"],
        top_n=top_n,
        write_artifact=False,
    )

    return {
        "spec_version": "1.0",
        "capture": {
            "path": capture,
            "baseline_capture_id": baseline.get("capture_id"),
            "candidate_capture_id": candidate.get("capture_id"),
            "same_capture_id": baseline.get("capture_id") == candidate.get("capture_id"),
        },
        "baseline": baseline,
        "candidate": candidate,
        "compare_summary": compare["compare_summary"],
        "gate_result": gate,
        "exit_code": int(gate.get("exit_code", 0)),
    }
