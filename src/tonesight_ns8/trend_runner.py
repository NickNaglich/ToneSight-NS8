"""Deterministic trend rollup runner across historical eval artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compare_runner import group_l1_stats


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _safe_delta(prev: float | int | None, curr: float | int | None) -> float | None:
    if prev is None or curr is None:
        return None
    return float(curr) - float(prev)


def _discover_runs(out_root: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for child in out_root.iterdir():
        if not child.is_dir():
            continue
        summary_path = child / "eval_summary.json"
        receipt_path = child / "receipt.json"
        out_path = child / "out.jsonl"
        if not summary_path.exists() or not receipt_path.exists() or not out_path.exists():
            continue
        summary = _read_json(summary_path)
        receipt = _read_json(receipt_path)
        run_id = str(summary.get("run_id") or child.name)
        runs.append(
            {
                "run_id": run_id,
                "path": str(child),
                "dataset_hash": receipt.get("dataset_hash"),
                "spec_version": receipt.get("spec_version"),
                "summary": summary,
                "out_path": str(out_path),
            }
        )
    runs.sort(key=lambda r: str(r["run_id"]))
    return runs


def run_trend(
    out_root: str,
    *,
    group_by: str | None = None,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Aggregate deterministic run-over-run trend summaries from run artifacts."""
    out_root_path = Path(out_root)
    runs = _discover_runs(out_root_path)
    trend_runs: list[dict[str, Any]] = []
    prev: dict[str, Any] | None = None

    for run in runs:
        summary = run["summary"]
        curr_entry: dict[str, Any] = {
            "run_id": run["run_id"],
            "path": run["path"],
            "dataset_hash": run.get("dataset_hash"),
            "spec_version": run.get("spec_version"),
            "count_rows": summary.get("count_rows"),
            "pass_rate": summary.get("pass_rate"),
            "avg_l1": summary.get("avg_l1"),
            "p95_l1": summary.get("p95_l1"),
            "delta_pass_rate_vs_prev": None,  # nosec B105
            "delta_avg_l1_vs_prev": None,
            "delta_p95_l1_vs_prev": None,
            "delta_skipped_reason": None,
        }

        if prev is not None:
            compatible = (
                str(prev.get("dataset_hash")) == str(run.get("dataset_hash"))
                and str(prev.get("spec_version")) == str(run.get("spec_version"))
            )
            if compatible:
                prev_summary = prev["summary"]
                curr_entry["delta_pass_rate_vs_prev"] = _safe_delta(prev_summary.get("pass_rate"), summary.get("pass_rate"))
                curr_entry["delta_avg_l1_vs_prev"] = _safe_delta(prev_summary.get("avg_l1"), summary.get("avg_l1"))
                curr_entry["delta_p95_l1_vs_prev"] = _safe_delta(prev_summary.get("p95_l1"), summary.get("p95_l1"))
            else:
                curr_entry["delta_skipped_reason"] = "incompatible_prev_run"

        if group_by:
            rows = _read_jsonl(Path(run["out_path"]))
            curr_entry["group_summary"] = group_l1_stats(rows, group_by)

        trend_runs.append(curr_entry)
        prev = run

    payload: dict[str, Any] = {
        "spec_version": "1.0",
        "out_root": str(out_root_path),
        "group_by": group_by,
        "run_count": len(trend_runs),
        "runs": trend_runs,
    }

    target = Path(out_path) if out_path else (out_root_path / "trend_summary.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["trend_summary_path"] = str(target)
    return payload
