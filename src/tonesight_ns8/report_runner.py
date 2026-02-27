"""Deterministic static reporting over existing run artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .compare_runner import run_compare
from .gate_runner import run_gate

REPORT_SCHEMA_VERSION = "1.0"
TRANSITION_HEATMAP_SCHEMA_VERSION = "1.0"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid_json_object:{path}")
    return payload


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


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


def _pred_a_bin(row: dict[str, Any]) -> int | None:
    pred = row.get("pred_vad")
    if not isinstance(pred, dict):
        return None
    value = pred.get("A")
    if not isinstance(value, int):
        return None
    if value < 1 or value > 8:
        return None
    return value


def _transition_matrix_from_rows(rows: list[dict[str, Any]]) -> tuple[list[list[int]], int]:
    matrix = [[0 for _ in range(8)] for _ in range(8)]
    bins = [_pred_a_bin(row) for row in rows]
    total = 0
    for idx in range(1, len(bins)):
        prev_val = bins[idx - 1]
        curr_val = bins[idx]
        if prev_val is None or curr_val is None:
            continue
        matrix[prev_val - 1][curr_val - 1] += 1
        total += 1
    return matrix, total


def _matrix_delta(matrix_b: list[list[int]], matrix_a: list[list[int]]) -> list[list[int]]:
    return [
        [int(matrix_b[r][c]) - int(matrix_a[r][c]) for c in range(8)]
        for r in range(8)
    ]


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _coding_agent_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    coding_rows = [
        row
        for row in rows
        if row.get("adapter_id") == "coding_agent"
        and isinstance(row.get("coding_agent_features"), dict)
        and isinstance(row.get("coding_agent_bins"), dict)
    ]
    if not coding_rows:
        return {
            "row_count": 0,
            "language_mismatch_rate": 0.0,
            "tests_present_rate": 0.0,
            "tool_call_rate": 0.0,
            "avg_verbosity_bin": 0.0,
            "avg_tests_bin": 0.0,
            "avg_tool_call_bin": 0.0,
        }

    mismatch_count = 0
    tests_present_count = 0
    tool_call_count = 0
    verbosity_sum = 0.0
    tests_bin_sum = 0.0
    tool_call_bin_sum = 0.0
    for row in coding_rows:
        features = row.get("coding_agent_features", {})
        bins = row.get("coding_agent_bins", {})
        mismatch_count += 1 if int(features.get("lang_mismatch", 0)) == 1 else 0
        tests_present_count += 1 if int(features.get("test_markers", 0)) > 0 else 0
        tool_call_count += 1 if int(features.get("tool_calls", 0)) > 0 else 0
        verbosity_sum += _to_float(bins.get("verbosity_bin"))
        tests_bin_sum += _to_float(bins.get("tests_bin"))
        tool_call_bin_sum += _to_float(bins.get("tool_call_bin"))

    total = float(len(coding_rows))
    return {
        "row_count": int(total),
        "language_mismatch_rate": mismatch_count / total,
        "tests_present_rate": tests_present_count / total,
        "tool_call_rate": tool_call_count / total,
        "avg_verbosity_bin": verbosity_sum / total,
        "avg_tests_bin": tests_bin_sum / total,
        "avg_tool_call_bin": tool_call_bin_sum / total,
    }


def _coding_agent_delta(run_a: dict[str, Any], run_b: dict[str, Any]) -> dict[str, float]:
    return {
        "language_mismatch_rate": _to_float(run_b.get("language_mismatch_rate")) - _to_float(run_a.get("language_mismatch_rate")),
        "tests_present_rate": _to_float(run_b.get("tests_present_rate")) - _to_float(run_a.get("tests_present_rate")),
        "tool_call_rate": _to_float(run_b.get("tool_call_rate")) - _to_float(run_a.get("tool_call_rate")),
        "avg_verbosity_bin": _to_float(run_b.get("avg_verbosity_bin")) - _to_float(run_a.get("avg_verbosity_bin")),
        "avg_tests_bin": _to_float(run_b.get("avg_tests_bin")) - _to_float(run_a.get("avg_tests_bin")),
        "avg_tool_call_bin": _to_float(run_b.get("avg_tool_call_bin")) - _to_float(run_a.get("avg_tool_call_bin")),
    }


def run_report(
    run_b: str,
    *,
    run_a: str | None = None,
    out_path: str | None = None,
    top_n: int = 10,
    profile: str | None = None,
    gate_profiles_path: str = "config/gate_profiles.json",
    min_pass_rate_delta: float | None = None,
    max_avg_l1_delta: float | None = None,
    max_p95_l1_delta: float | None = None,
    require_dataset_match: bool = True,
) -> dict[str, Any]:
    """Create a deterministic static report JSON from existing run artifacts."""
    run_b_path = Path(run_b)
    receipt_b = _read_json(run_b_path / "receipt.json")
    eval_summary_path = run_b_path / "eval_summary.json"
    signal_summary_path = run_b_path / "metrics_summary.json"
    out_rows_path = run_b_path / "out.jsonl"
    anchor_rows_path = run_b_path / "anchor_events.jsonl"
    if eval_summary_path.exists() and out_rows_path.exists():
        mode = "eval"
        summary_b = _read_json(eval_summary_path)
        rows_b = _read_jsonl(out_rows_path)
    elif signal_summary_path.exists() and anchor_rows_path.exists():
        mode = "signal"
        summary_b = _read_json(signal_summary_path)
        rows_b = _read_jsonl(anchor_rows_path)
    else:
        raise ValueError(f"run_b missing required eval/signal report inputs: {run_b_path}")

    coding_metrics_b = _coding_agent_metrics(rows_b) if mode == "eval" else {
        "row_count": 0,
        "language_mismatch_rate": 0.0,
        "tests_present_rate": 0.0,
        "tool_call_rate": 0.0,
        "avg_verbosity_bin": 0.0,
        "avg_tests_bin": 0.0,
        "avg_tool_call_bin": 0.0,
    }
    matrix_b, transitions_b = _transition_matrix_from_rows(rows_b if mode == "eval" else [])

    compare_highlights: dict[str, Any] = {
        "available": False,
        "compare_run_ids": None,
        "distance_mode": None,
        "metrics": None,
        "regression_coverage": None,
        "top_regressions": [],
    }
    gate_summary: dict[str, Any] = {
        "available": False,
        "decision": None,
        "thresholds": None,
        "violations": [],
        "incompatibilities": [],
        "human_summary": None,
        "exit_code": 0,
    }

    run_a_path: Path | None = None
    rows_a: list[dict[str, Any]] = []
    matrix_a: list[list[int]] | None = None
    transitions_a: int | None = None
    if run_a and mode == "eval":
        run_a_path = Path(run_a)
        rows_a = _read_jsonl(run_a_path / "out.jsonl")
        coding_metrics_a = _coding_agent_metrics(rows_a)
        matrix_a, transitions_a = _transition_matrix_from_rows(rows_a)
        compare_payload = run_compare(
            str(run_a_path),
            str(run_b_path),
            top_n=top_n,
            distance_mode="l1",
            write_artifact=False,
            require_dataset_match=require_dataset_match,
        )["compare_summary"]
        compare_highlights = {
            "available": True,
            "compare_run_ids": {
                "run_a": compare_payload["run_a"].get("run_id"),
                "run_b": compare_payload["run_b"].get("run_id"),
            },
            "distance_mode": compare_payload.get("distance_mode"),
            "metrics": compare_payload.get("metrics"),
            "regression_coverage": compare_payload.get("regression_coverage"),
            "top_regressions": [
                {
                    "id": row.get("id"),
                    "label": row.get("label"),
                    "delta_distance": row.get("delta_distance"),
                    "delta_l1": row.get("delta_l1"),
                }
                for row in compare_payload.get("top_regressions", [])
            ],
        }
        gate_payload = run_gate(
            str(run_a_path),
            str(run_b_path),
            profile=profile,
            gate_profiles_path=gate_profiles_path,
            min_pass_rate_delta=min_pass_rate_delta,
            max_avg_l1_delta=max_avg_l1_delta,
            max_p95_l1_delta=max_p95_l1_delta,
            top_n=top_n,
            require_dataset_match=require_dataset_match,
        )
        gate_summary = {
            "available": True,
            "decision": gate_payload.get("decision"),
            "thresholds": gate_payload.get("thresholds"),
            "violations": gate_payload.get("violations", []),
            "incompatibilities": gate_payload.get("incompatibilities", []),
            "human_summary": gate_payload.get("human_summary"),
            "exit_code": int(gate_payload.get("exit_code", 0)),
        }
    else:
        coding_metrics_a = None

    transition_heatmap_payload: dict[str, Any] = {
        "transition_heatmap_schema_version": TRANSITION_HEATMAP_SCHEMA_VERSION,
        "mode": "compare" if run_a_path is not None else "single",
        "state_definition": "pred_vad.A(row_i) -> pred_vad.A(row_i+1)",
        "run_b": {
            "run_id": summary_b.get("run_id"),
            "row_count": len(rows_b),
            "transition_count": transitions_b,
            "matrix_8x8": matrix_b,
        },
    }
    if run_a_path is not None and matrix_a is not None and transitions_a is not None:
        transition_heatmap_payload["run_a"] = {
            "run_id": _read_json(run_a_path / "eval_summary.json").get("run_id"),
            "row_count": len(rows_a),
            "transition_count": transitions_a,
            "matrix_8x8": matrix_a,
        }
        transition_heatmap_payload["delta_run_b_minus_run_a_8x8"] = _matrix_delta(matrix_b, matrix_a)

    report_payload: dict[str, Any] = {
        "spec_version": "1.0",
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "run_a_path": str(run_a_path) if run_a_path is not None else None,
        "run_b_path": str(run_b_path),
        "run_b": {
            "run_id": summary_b.get("run_id"),
            "count_rows": summary_b.get("count_rows", summary_b.get("count_anchor_events")),
            "pass_rate": summary_b.get("pass_rate"),
            "avg_l1": summary_b.get("avg_l1", summary_b.get("volatility_mean_step_distance")),
            "p95_l1": summary_b.get("p95_l1", summary_b.get("transition_entropy")),
            "summary_schema_version": summary_b.get("summary_schema_version", summary_b.get("metrics_schema_version")),
            "run_mode": mode,
        },
        "reproducibility": {
            "spec_version": receipt_b.get("spec_version"),
            "receipt_schema_version": receipt_b.get("receipt_schema_version"),
            "dataset_hash": receipt_b.get("dataset_hash"),
            "taxonomy_hash": receipt_b.get("taxonomy_hash"),
            "defaults_hash": receipt_b.get("defaults_hash"),
            "mapping_id": receipt_b.get("mapping_id"),
            "mapping_version": receipt_b.get("mapping_version"),
            "code_revision": receipt_b.get("code_revision"),
        },
        "compare_highlights": compare_highlights,
        "gate_summary": gate_summary,
        "coding_agent_drift": {
            "available": bool(coding_metrics_b.get("row_count", 0) > 0),
            "run_b": coding_metrics_b,
            "run_a": coding_metrics_a,
            "delta_run_b_minus_run_a": _coding_agent_delta(coding_metrics_a, coding_metrics_b)
            if coding_metrics_a is not None
            else None,
        },
        "signal_layer": {
            "available": bool(receipt_b.get("mapping_profile") or (run_b_path / "metrics_summary.json").exists()),
            "mapping_profile": receipt_b.get("mapping_profile"),
            "mapping_profile_hash": receipt_b.get("mapping_profile_hash"),
            "domain_pack": receipt_b.get("domain_pack"),
            "domain_pack_hash": receipt_b.get("domain_pack_hash"),
            "quarantine_count_total": receipt_b.get("quarantine_count_total"),
            "quarantine_counts_by_reason": receipt_b.get("quarantine_counts_by_reason"),
        },
        "artifacts": {
            "run_b_eval_summary_json": str(eval_summary_path) if eval_summary_path.exists() else None,
            "run_b_metrics_summary_json": str(signal_summary_path) if signal_summary_path.exists() else None,
            "run_b_receipt_json": str(run_b_path / "receipt.json"),
        },
    }
    if run_a_path is not None and mode == "eval":
        report_payload["artifacts"]["run_a_receipt_json"] = str(run_a_path / "receipt.json")
        report_name = f"report_{run_a_path.name}_to_{run_b_path.name}.json"
        heatmap_name = f"transition_heatmap_{run_a_path.name}_to_{run_b_path.name}.json"
    else:
        report_name = f"report_{run_b_path.name}.json"
        heatmap_name = f"transition_heatmap_{run_b_path.name}.json"

    target = Path(out_path) if out_path else (run_b_path / "reports" / report_name)
    heatmap_path = target.parent / heatmap_name
    target.parent.mkdir(parents=True, exist_ok=True)
    heatmap_path.write_text(json.dumps(transition_heatmap_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_payload["transition_heatmap"] = {
        "available": True,
        "mode": transition_heatmap_payload["mode"],
        "schema_version": TRANSITION_HEATMAP_SCHEMA_VERSION,
        "transition_count_run_b": transitions_b,
        "transition_count_run_a": transitions_a,
    }
    report_payload["artifacts"]["transition_heatmap_json"] = str(heatmap_path)
    target.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "report_path": str(target),
        "transition_heatmap_path": str(heatmap_path),
        "report_hash": _file_hash(target),
        "transition_heatmap_hash": _file_hash(heatmap_path),
        "report": report_payload,
    }
