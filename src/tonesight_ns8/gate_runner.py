"""Deterministic CI gate runner based on compare deltas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compare_runner import run_compare


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _compatibility_issues(run_a: Path, run_b: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    receipt_a = _read_json(run_a / "receipt.json")
    receipt_b = _read_json(run_b / "receipt.json")
    issues: list[dict[str, str]] = []

    dataset_a = str(receipt_a.get("dataset_hash", ""))
    dataset_b = str(receipt_b.get("dataset_hash", ""))
    if dataset_a != dataset_b:
        issues.append(
            {
                "reason": "dataset_hash_mismatch",
                "expected_dataset_hash": dataset_a,
                "actual_dataset_hash": dataset_b,
            }
        )

    spec_a = str(receipt_a.get("spec_version", ""))
    spec_b = str(receipt_b.get("spec_version", ""))
    if spec_a != spec_b:
        issues.append(
            {
                "reason": "spec_version_mismatch",
                "expected_spec_version": spec_a,
                "actual_spec_version": spec_b,
            }
        )

    return receipt_a, receipt_b, issues


def run_gate(
    run_a: str,
    run_b: str,
    *,
    min_pass_rate_delta: float = -0.02,
    max_avg_l1_delta: float = 0.2,
    max_p95_l1_delta: float = 0.2,
    top_n: int = 10,
) -> dict[str, Any]:
    """Evaluate deterministic compare deltas and return a CI gate decision."""
    run_a_path = Path(run_a)
    run_b_path = Path(run_b)
    receipt_a, receipt_b, issues = _compatibility_issues(run_a_path, run_b_path)

    base_payload: dict[str, Any] = {
        "spec_version": "1.0",
        "run_a": {
            "path": str(run_a_path),
            "run_id": receipt_a.get("run_id"),
            "dataset_hash": receipt_a.get("dataset_hash"),
            "spec_version": receipt_a.get("spec_version"),
        },
        "run_b": {
            "path": str(run_b_path),
            "run_id": receipt_b.get("run_id"),
            "dataset_hash": receipt_b.get("dataset_hash"),
            "spec_version": receipt_b.get("spec_version"),
        },
        "thresholds": {
            "min_pass_rate_delta": float(min_pass_rate_delta),
            "max_avg_l1_delta": float(max_avg_l1_delta),
            "max_p95_l1_delta": float(max_p95_l1_delta),
        },
    }
    if issues:
        base_payload["decision"] = "incompatible"
        base_payload["incompatibilities"] = issues
        base_payload["violations"] = []
        base_payload["human_summary"] = "Gate skipped: incompatible runs (dataset/spec mismatch)."
        base_payload["exit_code"] = 3
        return base_payload

    compare = run_compare(str(run_a_path), str(run_b_path), top_n=top_n, write_artifact=False)["compare_summary"]
    metrics = compare["metrics"]
    delta_pass_rate = float(metrics.get("delta_pass_rate") or 0.0)
    delta_avg_l1 = float(metrics.get("delta_avg_l1") or 0.0)
    delta_p95_l1 = float(metrics.get("delta_p95_l1") or 0.0)

    violations: list[dict[str, Any]] = []
    if delta_pass_rate < float(min_pass_rate_delta):
        violations.append(
            {
                "metric": "delta_pass_rate",
                "actual": delta_pass_rate,
                "threshold": float(min_pass_rate_delta),
                "operator": ">=",
            }
        )
    if delta_avg_l1 > float(max_avg_l1_delta):
        violations.append(
            {
                "metric": "delta_avg_l1",
                "actual": delta_avg_l1,
                "threshold": float(max_avg_l1_delta),
                "operator": "<=",
            }
        )
    if delta_p95_l1 > float(max_p95_l1_delta):
        violations.append(
            {
                "metric": "delta_p95_l1",
                "actual": delta_p95_l1,
                "threshold": float(max_p95_l1_delta),
                "operator": "<=",
            }
        )

    if violations:
        decision = "regressed"
        exit_code = 2
        summary = f"Gate failed: {len(violations)} threshold violation(s)."
    else:
        decision = "passed"
        exit_code = 0
        summary = "Gate passed: all thresholds satisfied."

    base_payload["decision"] = decision
    base_payload["incompatibilities"] = []
    base_payload["violations"] = violations
    base_payload["metrics"] = {
        "delta_pass_rate": delta_pass_rate,
        "delta_avg_l1": delta_avg_l1,
        "delta_p95_l1": delta_p95_l1,
    }
    base_payload["compare_run_ids"] = {
        "run_a": compare["run_a"]["run_id"],
        "run_b": compare["run_b"]["run_id"],
    }
    base_payload["human_summary"] = summary
    base_payload["exit_code"] = exit_code
    return base_payload

