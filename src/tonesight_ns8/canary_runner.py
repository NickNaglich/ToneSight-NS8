"""Deterministic canary evaluator for baseline-vs-candidate replay."""

from __future__ import annotations

from typing import Any

from .compare_runner import run_compare
from .gate_runner import _resolve_thresholds, run_gate
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
    adapter: str = "upstream_signal",
    require_pinned_model_identity: bool = False,
) -> dict[str, Any]:
    """Replay one capture through baseline/candidate flows and gate the delta."""
    # Use the gate's native profile policy for every stage of this canary.
    thresholds, _ = _resolve_thresholds(
        profile=profile,
        gate_profiles_path=gate_profiles_path,
        min_pass_rate_delta=min_pass_rate_delta,
        max_avg_l1_delta=max_avg_l1_delta,
        max_p95_l1_delta=max_p95_l1_delta,
    )
    effective_pinned = require_pinned_model_identity or bool(thresholds["require_pinned_model_identity"])
    baseline = run_live_replay(
        capture,
        out_root=baseline_out_root,
        taxonomy_path=baseline_taxonomy_path,
        threshold_l1=baseline_threshold_l1,
        shadow_strict=shadow_strict,
        redact=redact,
        adapter=adapter,
        require_pinned_model_identity=effective_pinned,
    )
    candidate = run_live_replay(
        capture,
        out_root=candidate_out_root,
        taxonomy_path=candidate_taxonomy_path,
        threshold_l1=candidate_threshold_l1,
        shadow_strict=shadow_strict,
        redact=redact,
        adapter=adapter,
        require_pinned_model_identity=effective_pinned,
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
        require_pinned_model_identity=True if require_pinned_model_identity else None,
    )
    compare = run_compare(
        baseline["out_dir"],
        candidate["out_dir"],
        top_n=top_n,
        write_artifact=False,
        require_dataset_match=not allow_dataset_mismatch,
        require_pinned_model_identity=effective_pinned,
    )

    # Native replay exposes capture identity in summary/receipt, not at top level.
    capture_ids = []
    for replay in (baseline, candidate):
        capture_id = replay.get("summary", {}).get("capture_id") or replay.get("receipt", {}).get("capture_id")
        capture_ids.append(capture_id if isinstance(capture_id, str) and capture_id.strip() else None)
    baseline_capture_id, candidate_capture_id = capture_ids

    return {
        "spec_version": "1.0",
        "replay_policy": {
            "adapter": adapter,
            "require_pinned_model_identity": bool(effective_pinned),
        },
        "evidence_scope": {
            "operation": "recorded_capture_replay",
            "live_model_execution": "not_attested_by_canary",
            "model_identity_attestation": "not_performed_by_canary",
        },
        "capture": {
            "path": capture,
            "baseline_capture_id": baseline_capture_id,
            "candidate_capture_id": candidate_capture_id,
            "same_capture_id": baseline_capture_id is not None and baseline_capture_id == candidate_capture_id,
        },
        "baseline": baseline,
        "candidate": candidate,
        "compare_summary": compare["compare_summary"],
        "gate_result": gate,
        "exit_code": int(gate.get("exit_code", 0)),
    }
