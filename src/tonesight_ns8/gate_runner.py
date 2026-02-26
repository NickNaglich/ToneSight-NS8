"""Deterministic CI gate runner based on compare deltas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compatibility import compatibility_issues
from .compare_runner import run_compare

_DEFAULT_THRESHOLDS = {
    "min_pass_rate_delta": -0.02,
    "max_avg_l1_delta": 0.2,
    "max_p95_l1_delta": 0.2,
    "require_pinned_model_identity": False,
    "max_language_mismatch_rate_delta": None,
    "max_verbosity_bin_mean_delta": None,
    "min_tests_presence_rate_delta": None,
    "min_tool_call_rate_delta": None,
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _coding_agent_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    coding_rows = [
        row
        for row in rows
        if row.get("adapter_id") == "coding_agent"
        and isinstance(row.get("coding_agent_features"), dict)
        and isinstance(row.get("coding_agent_bins"), dict)
    ]
    if not coding_rows:
        return {
            "row_count": 0.0,
            "language_mismatch_rate": 0.0,
            "verbosity_bin_mean": 0.0,
            "tests_presence_rate": 0.0,
            "tool_call_rate": 0.0,
        }
    n = float(len(coding_rows))
    mismatch_rate = sum(_to_float(row["coding_agent_features"].get("lang_mismatch")) for row in coding_rows) / n
    verbosity_mean = sum(_to_float(row["coding_agent_bins"].get("verbosity_bin")) for row in coding_rows) / n
    tests_presence_rate = (
        sum(1.0 if _to_float(row["coding_agent_features"].get("test_markers")) > 0.0 else 0.0 for row in coding_rows) / n
    )
    tool_call_rate = (
        sum(1.0 if _to_float(row["coding_agent_features"].get("tool_call_count")) > 0.0 else 0.0 for row in coding_rows) / n
    )
    return {
        "row_count": n,
        "language_mismatch_rate": mismatch_rate,
        "verbosity_bin_mean": verbosity_mean,
        "tests_presence_rate": tests_presence_rate,
        "tool_call_rate": tool_call_rate,
    }


def _compatibility_issues(
    run_a: Path,
    run_b: Path,
    *,
    require_dataset_match: bool = True,
    require_pinned_model_identity: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    receipt_a = _read_json(run_a / "receipt.json")
    receipt_b = _read_json(run_b / "receipt.json")
    issues = compatibility_issues(
        receipt_a,
        receipt_b,
        require_dataset_match=require_dataset_match,
        require_pinned_model_identity=require_pinned_model_identity,
    )
    return receipt_a, receipt_b, issues


def _load_gate_profiles(path: Path) -> dict[str, dict[str, float | bool]]:
    payload = _read_json(path)
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError(f"Invalid gate profiles config at {path}: profiles must be object")
    out: dict[str, dict[str, float | bool]] = {}
    for name, raw in profiles.items():
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid gate profile {name!r}: must be object")
        try:
            out[str(name)] = {
                "min_pass_rate_delta": float(raw["min_pass_rate_delta"]),
                "max_avg_l1_delta": float(raw["max_avg_l1_delta"]),
                "max_p95_l1_delta": float(raw["max_p95_l1_delta"]),
                "require_pinned_model_identity": bool(raw.get("require_pinned_model_identity", False)),
                "max_language_mismatch_rate_delta": (
                    None
                    if raw.get("max_language_mismatch_rate_delta") is None
                    else float(raw.get("max_language_mismatch_rate_delta"))
                ),
                "max_verbosity_bin_mean_delta": (
                    None
                    if raw.get("max_verbosity_bin_mean_delta") is None
                    else float(raw.get("max_verbosity_bin_mean_delta"))
                ),
                "min_tests_presence_rate_delta": (
                    None
                    if raw.get("min_tests_presence_rate_delta") is None
                    else float(raw.get("min_tests_presence_rate_delta"))
                ),
                "min_tool_call_rate_delta": (
                    None
                    if raw.get("min_tool_call_rate_delta") is None
                    else float(raw.get("min_tool_call_rate_delta"))
                ),
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
) -> tuple[dict[str, float | bool], str | None]:
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
    require_pinned_model_identity: bool | None = None,
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
    if require_pinned_model_identity is not None:
        thresholds["require_pinned_model_identity"] = bool(require_pinned_model_identity)

    run_a_path = Path(run_a)
    run_b_path = Path(run_b)
    receipt_a, receipt_b, issues = _compatibility_issues(
        run_a_path,
        run_b_path,
        require_dataset_match=require_dataset_match,
        require_pinned_model_identity=bool(thresholds.get("require_pinned_model_identity", False)),
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
            "require_pinned_model_identity": bool(thresholds.get("require_pinned_model_identity", False)),
            "max_language_mismatch_rate_delta": thresholds.get("max_language_mismatch_rate_delta"),
            "max_verbosity_bin_mean_delta": thresholds.get("max_verbosity_bin_mean_delta"),
            "min_tests_presence_rate_delta": thresholds.get("min_tests_presence_rate_delta"),
            "min_tool_call_rate_delta": thresholds.get("min_tool_call_rate_delta"),
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

    coding_thresholds_enabled = any(
        thresholds.get(key) is not None
        for key in (
            "max_language_mismatch_rate_delta",
            "max_verbosity_bin_mean_delta",
            "min_tests_presence_rate_delta",
            "min_tool_call_rate_delta",
        )
    )
    coding_metrics_payload: dict[str, Any] | None = None
    if coding_thresholds_enabled:
        rows_a = _read_jsonl(run_a_path / "out.jsonl")
        rows_b = _read_jsonl(run_b_path / "out.jsonl")
        metrics_a = _coding_agent_metrics(rows_a)
        metrics_b = _coding_agent_metrics(rows_b)
        if metrics_a["row_count"] <= 0.0 or metrics_b["row_count"] <= 0.0:
            base_payload["decision"] = "incompatible"
            base_payload["incompatibilities"] = [
                {
                    "reason": "coding_agent_metrics_missing",
                    "field": "coding_agent_rows",
                    "expected": str(int(metrics_a["row_count"])),
                    "actual": str(int(metrics_b["row_count"])),
                }
            ]
            base_payload["violations"] = []
            base_payload["human_summary"] = "Gate skipped: missing coding-agent metrics required by selected profile."
            base_payload["exit_code"] = 3
            return base_payload
        coding_metrics_payload = {
            "run_a": metrics_a,
            "run_b": metrics_b,
            "delta": {
                "language_mismatch_rate": metrics_b["language_mismatch_rate"] - metrics_a["language_mismatch_rate"],
                "verbosity_bin_mean": metrics_b["verbosity_bin_mean"] - metrics_a["verbosity_bin_mean"],
                "tests_presence_rate": metrics_b["tests_presence_rate"] - metrics_a["tests_presence_rate"],
                "tool_call_rate": metrics_b["tool_call_rate"] - metrics_a["tool_call_rate"],
            },
        }

    compare = run_compare(
        str(run_a_path),
        str(run_b_path),
        top_n=top_n,
        write_artifact=False,
        require_dataset_match=require_dataset_match,
        require_pinned_model_identity=bool(thresholds.get("require_pinned_model_identity", False)),
    )["compare_summary"]
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
    if coding_metrics_payload is not None:
        coding_delta = coding_metrics_payload["delta"]
        max_mismatch_delta = thresholds.get("max_language_mismatch_rate_delta")
        if max_mismatch_delta is not None and float(coding_delta["language_mismatch_rate"]) > float(max_mismatch_delta):
            violations.append(
                {
                    "metric": "delta_language_mismatch_rate",
                    "actual": float(coding_delta["language_mismatch_rate"]),
                    "threshold": float(max_mismatch_delta),
                    "operator": "<=",
                }
            )
        max_verbosity_delta = thresholds.get("max_verbosity_bin_mean_delta")
        if max_verbosity_delta is not None and float(coding_delta["verbosity_bin_mean"]) > float(max_verbosity_delta):
            violations.append(
                {
                    "metric": "delta_verbosity_bin_mean",
                    "actual": float(coding_delta["verbosity_bin_mean"]),
                    "threshold": float(max_verbosity_delta),
                    "operator": "<=",
                }
            )
        min_tests_delta = thresholds.get("min_tests_presence_rate_delta")
        if min_tests_delta is not None and float(coding_delta["tests_presence_rate"]) < float(min_tests_delta):
            violations.append(
                {
                    "metric": "delta_tests_presence_rate",
                    "actual": float(coding_delta["tests_presence_rate"]),
                    "threshold": float(min_tests_delta),
                    "operator": ">=",
                }
            )
        min_tool_calls_delta = thresholds.get("min_tool_call_rate_delta")
        if min_tool_calls_delta is not None and float(coding_delta["tool_call_rate"]) < float(min_tool_calls_delta):
            violations.append(
                {
                    "metric": "delta_tool_call_rate",
                    "actual": float(coding_delta["tool_call_rate"]),
                    "threshold": float(min_tool_calls_delta),
                    "operator": ">=",
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
    if coding_metrics_payload is not None:
        base_payload["coding_agent_metrics"] = coding_metrics_payload
    base_payload["compare_run_ids"] = {
        "run_a": compare["run_a"]["run_id"],
        "run_b": compare["run_b"]["run_id"],
    }
    base_payload["human_summary"] = summary
    base_payload["exit_code"] = exit_code
    return base_payload
