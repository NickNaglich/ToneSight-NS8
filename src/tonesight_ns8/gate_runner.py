"""Deterministic CI gate runner based on compare deltas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compare_runner import run_compare

_DEFAULT_THRESHOLDS = {
    "min_pass_rate_delta": -0.02,
    "max_avg_l1_delta": 0.2,
    "max_p95_l1_delta": 0.2,
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _receipt_config(receipt: dict[str, Any]) -> dict[str, Any]:
    raw = receipt.get("config")
    if isinstance(raw, dict):
        return raw
    return {}


def _identity_fields(receipt: dict[str, Any]) -> dict[str, str]:
    config = _receipt_config(receipt)
    spec_version = _as_str(receipt.get("spec_version"))
    mapping_id = _as_str(receipt.get("mapping_id") or config.get("mapping_id") or "ns8")
    mapping_version = _as_str(receipt.get("mapping_version") or config.get("mapping_version") or spec_version)
    taxonomy_identity = _as_str(receipt.get("taxonomy_hash") or config.get("taxonomy_path"))
    calibration_identity = _as_str(config.get("calibration_path"))
    defaults_schema_version = _as_str(
        receipt.get("defaults_spec_version") or config.get("defaults_spec_version") or receipt.get("defaults_hash")
    )
    return {
        "spec_version": spec_version,
        "mapping_id": mapping_id,
        "mapping_version": mapping_version,
        "taxonomy_identity": taxonomy_identity,
        "calibration_identity": calibration_identity,
        "defaults_schema_version": defaults_schema_version,
    }


def _compatibility_issues(
    run_a: Path,
    run_b: Path,
    *,
    require_dataset_match: bool = True,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    receipt_a = _read_json(run_a / "receipt.json")
    receipt_b = _read_json(run_b / "receipt.json")
    issues: list[dict[str, str]] = []

    dataset_a = str(receipt_a.get("dataset_hash", ""))
    dataset_b = str(receipt_b.get("dataset_hash", ""))
    if require_dataset_match and dataset_a != dataset_b:
        issues.append(
            {
                "reason": "dataset_hash_mismatch",
                "expected_dataset_hash": dataset_a,
                "actual_dataset_hash": dataset_b,
            }
        )

    fields_a = _identity_fields(receipt_a)
    fields_b = _identity_fields(receipt_b)
    field_mismatch_reasons = {
        "spec_version": "spec_version_mismatch",
        "mapping_id": "mapping_id_mismatch",
        "mapping_version": "mapping_version_mismatch",
        "taxonomy_identity": "taxonomy_identity_mismatch",
        "calibration_identity": "calibration_identity_mismatch",
        "defaults_schema_version": "defaults_schema_version_mismatch",
    }
    for field in (
        "spec_version",
        "mapping_id",
        "mapping_version",
        "taxonomy_identity",
        "calibration_identity",
        "defaults_schema_version",
    ):
        if fields_a[field] != fields_b[field]:
            issues.append(
                {
                    "reason": field_mismatch_reasons[field],
                    "field": field,
                    "expected": fields_a[field],
                    "actual": fields_b[field],
                }
            )

    return receipt_a, receipt_b, issues


def _load_gate_profiles(path: Path) -> dict[str, dict[str, float]]:
    payload = _read_json(path)
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError(f"Invalid gate profiles config at {path}: profiles must be object")
    out: dict[str, dict[str, float]] = {}
    for name, raw in profiles.items():
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid gate profile {name!r}: must be object")
        try:
            out[str(name)] = {
                "min_pass_rate_delta": float(raw["min_pass_rate_delta"]),
                "max_avg_l1_delta": float(raw["max_avg_l1_delta"]),
                "max_p95_l1_delta": float(raw["max_p95_l1_delta"]),
            }
        except KeyError as exc:
            raise ValueError(f"Invalid gate profile {name!r}: missing {exc.args[0]}") from exc
    return out


def _resolve_thresholds(
    *,
    profile: str | None,
    gate_profiles_path: str,
    min_pass_rate_delta: float | None,
    max_avg_l1_delta: float | None,
    max_p95_l1_delta: float | None,
) -> tuple[dict[str, float], str | None]:
    resolved = dict(_DEFAULT_THRESHOLDS)
    selected_profile: str | None = None
    if profile:
        profiles = _load_gate_profiles(Path(gate_profiles_path))
        if profile not in profiles:
            raise ValueError(f"Unknown gate profile: {profile}")
        resolved.update(profiles[profile])
        selected_profile = profile
    if min_pass_rate_delta is not None:
        resolved["min_pass_rate_delta"] = float(min_pass_rate_delta)
    if max_avg_l1_delta is not None:
        resolved["max_avg_l1_delta"] = float(max_avg_l1_delta)
    if max_p95_l1_delta is not None:
        resolved["max_p95_l1_delta"] = float(max_p95_l1_delta)
    return resolved, selected_profile


def run_gate(
    run_a: str,
    run_b: str,
    *,
    profile: str | None = None,
    gate_profiles_path: str = "config/gate_profiles.json",
    min_pass_rate_delta: float | None = None,
    max_avg_l1_delta: float | None = None,
    max_p95_l1_delta: float | None = None,
    top_n: int = 10,
    require_dataset_match: bool = True,
) -> dict[str, Any]:
    """Evaluate deterministic compare deltas and return a CI gate decision."""
    thresholds, selected_profile = _resolve_thresholds(
        profile=profile,
        gate_profiles_path=gate_profiles_path,
        min_pass_rate_delta=min_pass_rate_delta,
        max_avg_l1_delta=max_avg_l1_delta,
        max_p95_l1_delta=max_p95_l1_delta,
    )

    run_a_path = Path(run_a)
    run_b_path = Path(run_b)
    receipt_a, receipt_b, issues = _compatibility_issues(
        run_a_path,
        run_b_path,
        require_dataset_match=require_dataset_match,
    )

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
            "min_pass_rate_delta": float(thresholds["min_pass_rate_delta"]),
            "max_avg_l1_delta": float(thresholds["max_avg_l1_delta"]),
            "max_p95_l1_delta": float(thresholds["max_p95_l1_delta"]),
        },
        "profile": selected_profile,
        "gate_profiles_path": gate_profiles_path if selected_profile else None,
        "require_dataset_match": require_dataset_match,
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
    if delta_pass_rate < float(thresholds["min_pass_rate_delta"]):
        violations.append(
            {
                "metric": "delta_pass_rate",
                "actual": delta_pass_rate,
                "threshold": float(thresholds["min_pass_rate_delta"]),
                "operator": ">=",
            }
        )
    if delta_avg_l1 > float(thresholds["max_avg_l1_delta"]):
        violations.append(
            {
                "metric": "delta_avg_l1",
                "actual": delta_avg_l1,
                "threshold": float(thresholds["max_avg_l1_delta"]),
                "operator": "<=",
            }
        )
    if delta_p95_l1 > float(thresholds["max_p95_l1_delta"]):
        violations.append(
            {
                "metric": "delta_p95_l1",
                "actual": delta_p95_l1,
                "threshold": float(thresholds["max_p95_l1_delta"]),
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
