"""Deterministic run index generator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def _run_dirs(out_root: Path) -> list[Path]:
    runs: list[Path] = []
    for child in out_root.iterdir():
        if not child.is_dir():
            continue
        has_eval = (child / "eval_summary.json").exists() and (child / "out.jsonl").exists()
        has_signal = (child / "metrics_summary.json").exists() and (child / "anchor_events.jsonl").exists()
        if (child / "receipt.json").exists() and (has_eval or has_signal):
            runs.append(child)
    return sorted(runs, key=lambda p: p.name)


def _source_labels(out_rows: list[dict[str, Any]]) -> list[str]:
    values = sorted({str(row.get("source")) for row in out_rows if row.get("source") not in (None, "")})
    return values


def _index_row(run_dir: Path) -> dict[str, Any]:
    receipt = _read_json(run_dir / "receipt.json")
    eval_summary_path = run_dir / "eval_summary.json"
    signal_summary_path = run_dir / "metrics_summary.json"
    out_jsonl_path = run_dir / "out.jsonl"
    anchor_events_path = run_dir / "anchor_events.jsonl"
    mode = "eval"
    if eval_summary_path.exists() and out_jsonl_path.exists():
        summary = _read_json(eval_summary_path)
        rows = _read_jsonl(out_jsonl_path)
    elif signal_summary_path.exists() and anchor_events_path.exists():
        mode = "signal"
        summary = _read_json(signal_summary_path)
        rows = _read_jsonl(anchor_events_path)
    else:
        raise FileNotFoundError(f"run_dir missing required eval/signal artifact set: {run_dir}")
    config = receipt.get("config") if isinstance(receipt.get("config"), dict) else {}
    artifacts = receipt.get("artifacts") if isinstance(receipt.get("artifacts"), dict) else {}
    run_id = str(receipt.get("run_id") or summary.get("run_id") or run_dir.name)
    quarantine_total = receipt.get("quarantine_count_total")
    quarantine_by_reason = receipt.get("quarantine_counts_by_reason")
    return {
        "spec_version": "1.0",
        "run_id": run_id,
        "run_path": str(run_dir),
        "run_spec_version": str(receipt.get("spec_version", "")),
        "created_at_utc": receipt.get("created_at_utc"),
        "dataset_hash": receipt.get("dataset_hash"),
        "taxonomy_hash": receipt.get("taxonomy_hash"),
        "defaults_hash": receipt.get("defaults_hash"),
        "mapping_id": str(receipt.get("mapping_id") or config.get("mapping_id") or ""),
        "mapping_version": str(receipt.get("mapping_version") or config.get("mapping_version") or ""),
        "profile_label": str(config.get("profile") or config.get("gate_profile") or ""),
        "source_label": str(config.get("source_mode") or mode),
        "source_labels": _source_labels(rows),
        "signal_layer": {
            "mapping_profile": receipt.get("mapping_profile"),
            "mapping_profile_hash": receipt.get("mapping_profile_hash"),
            "domain_pack": receipt.get("domain_pack"),
            "domain_pack_hash": receipt.get("domain_pack_hash"),
            "quarantine_count_total": quarantine_total if isinstance(quarantine_total, int) else 0,
            "quarantine_counts_by_reason": quarantine_by_reason if isinstance(quarantine_by_reason, dict) else {},
        },
        "metrics": {
            "count_rows": summary.get("count_rows", summary.get("count_anchor_events")),
            "pass_rate": summary.get("pass_rate"),
            "avg_l1": summary.get("avg_l1", summary.get("volatility_mean_step_distance")),
            "p95_l1": summary.get("p95_l1", summary.get("transition_entropy")),
        },
        "artifacts": {
            "out_jsonl": artifacts.get("out_jsonl", str(out_jsonl_path)) if out_jsonl_path.exists() else None,
            "eval_summary_json": artifacts.get("eval_summary_json", str(eval_summary_path)) if eval_summary_path.exists() else None,
            "anchor_events_jsonl": artifacts.get("anchor_events_jsonl", str(anchor_events_path)) if anchor_events_path.exists() else None,
            "metrics_summary_json": artifacts.get("metrics_summary_json", str(signal_summary_path)) if signal_summary_path.exists() else None,
            "report_html": artifacts.get("report_html", str(run_dir / "report.html")),
            "receipt_json": artifacts.get("receipt_json", str(run_dir / "receipt.json")),
            "quarantine_jsonl": artifacts.get("quarantine_jsonl", str(run_dir / "quarantine.jsonl")),
        },
    }


def run_index(
    out_root: str,
    *,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Build deterministic runs index JSONL with one row per run."""
    out_root_path = Path(out_root)
    rows = [_index_row(run_dir) for run_dir in _run_dirs(out_root_path)]
    rows = sorted(rows, key=lambda r: str(r["run_id"]))
    target = Path(out_path) if out_path else (out_root_path / "index.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, sort_keys=True, ensure_ascii=True) for row in rows)
    target.write_text((payload + "\n") if payload else "", encoding="utf-8")
    return {
        "spec_version": "1.0",
        "out_root": str(out_root_path),
        "run_count": len(rows),
        "index_path": str(target),
        "rows_preview": rows[: min(3, len(rows))],
    }


def run_index_json(
    out_root: str,
    *,
    index_jsonl_path: str | None = None,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Build deterministic runs index JSON array from index.jsonl rows."""
    out_root_path = Path(out_root)
    source = Path(index_jsonl_path) if index_jsonl_path else (out_root_path / "index.jsonl")
    if not source.exists():
        raise FileNotFoundError(f"Missing index jsonl: {source}")

    rows = _read_jsonl(source)
    rows = sorted(rows, key=lambda row: str(row.get("run_id", "")))
    target = Path(out_path) if out_path else (out_root_path / "index.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(rows, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return {
        "spec_version": "1.0",
        "out_root": str(out_root_path),
        "run_count": len(rows),
        "index_jsonl_path": str(source),
        "index_json_path": str(target),
        "rows_preview": rows[: min(3, len(rows))],
    }
