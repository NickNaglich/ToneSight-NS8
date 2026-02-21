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
        if (child / "receipt.json").exists() and (child / "eval_summary.json").exists() and (child / "out.jsonl").exists():
            runs.append(child)
    return sorted(runs, key=lambda p: p.name)


def _source_labels(out_rows: list[dict[str, Any]]) -> list[str]:
    values = sorted({str(row.get("source")) for row in out_rows if row.get("source") not in (None, "")})
    return values


def _index_row(run_dir: Path) -> dict[str, Any]:
    receipt = _read_json(run_dir / "receipt.json")
    summary = _read_json(run_dir / "eval_summary.json")
    rows = _read_jsonl(run_dir / "out.jsonl")
    config = receipt.get("config") if isinstance(receipt.get("config"), dict) else {}
    artifacts = receipt.get("artifacts") if isinstance(receipt.get("artifacts"), dict) else {}
    run_id = str(receipt.get("run_id") or summary.get("run_id") or run_dir.name)
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
        "source_label": str(config.get("source_mode") or "eval"),
        "source_labels": _source_labels(rows),
        "metrics": {
            "count_rows": summary.get("count_rows"),
            "pass_rate": summary.get("pass_rate"),
            "avg_l1": summary.get("avg_l1"),
            "p95_l1": summary.get("p95_l1"),
        },
        "artifacts": {
            "out_jsonl": artifacts.get("out_jsonl", str(run_dir / "out.jsonl")),
            "eval_summary_json": artifacts.get("eval_summary_json", str(run_dir / "eval_summary.json")),
            "report_html": artifacts.get("report_html", str(run_dir / "report.html")),
            "receipt_json": artifacts.get("receipt_json", str(run_dir / "receipt.json")),
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
