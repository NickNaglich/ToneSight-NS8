"""Deterministic triage export runner for run QA workflows."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _index_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(rows):
        row_id = row.get("id")
        key = str(row_id) if row_id is not None else f"__row_{i}"
        indexed[key] = row
    return indexed


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _single_run_triage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        row_id = row.get("id")
        key = str(row_id) if row_id is not None else f"__row_{i}"
        out.append(
            {
                "id": key,
                "label": row.get("label"),
                "tags": row.get("tags"),
                "delta_v": row.get("delta_v"),
                "delta_a": row.get("delta_a"),
                "delta_d": row.get("delta_d"),
                "threshold_margin": row.get("threshold_margin"),
                "compliance_l1": row.get("compliance_l1"),
                "pass": row.get("pass"),
            }
        )
    return out


def _diff_triage_rows(rows_a: list[dict[str, Any]], rows_b: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id_a = _index_rows(rows_a)
    by_id_b = _index_rows(rows_b)
    out: list[dict[str, Any]] = []
    for row_id in sorted(by_id_b):
        row_b = by_id_b[row_id]
        row_a = by_id_a.get(row_id)
        a_l1 = _to_float(row_a.get("compliance_l1")) if row_a is not None else None
        b_l1 = _to_float(row_b.get("compliance_l1"))
        out.append(
            {
                "id": row_id,
                "label": row_b.get("label"),
                "tags": row_b.get("tags"),
                "delta_v": row_b.get("delta_v"),
                "delta_a": row_b.get("delta_a"),
                "delta_d": row_b.get("delta_d"),
                "threshold_margin": row_b.get("threshold_margin"),
                "compliance_l1": row_b.get("compliance_l1"),
                "compliance_l1_a": a_l1,
                "compliance_l1_b": b_l1,
                "delta_compliance_l1": (b_l1 - a_l1) if a_l1 is not None else None,
                "pass_a": row_a.get("pass") if row_a is not None else None,
                "pass_b": row_b.get("pass"),
            }
        )
    return out


def _default_output_path(run_b: Path, run_a: Path | None, score: str, output_format: str) -> Path:
    filename = f"triage_{score}.{output_format}"
    if run_a is None:
        target = run_b / "triage" / filename
    else:
        target = run_b / "comparisons" / run_a.name / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _sort_rows(rows: list[dict[str, Any]], score: str) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (-_to_float(row.get(score)), str(row.get("id"))))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n"
    path.write_text(payload, encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = sorted({str(k) for row in rows for k in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_triage(
    run_b: str,
    *,
    run_a: str | None = None,
    top_n: int = 50,
    score: str = "compliance_l1",
    output_format: str = "jsonl",
    out_path: str | None = None,
) -> dict[str, Any]:
    """Create deterministic triage exports from one run or a run pair."""
    if output_format not in {"jsonl", "csv"}:
        raise ValueError("output_format must be one of: jsonl, csv")

    run_b_path = Path(run_b)
    rows_b = _read_jsonl(run_b_path / "out.jsonl")
    if run_a is None:
        triage_rows = _single_run_triage_rows(rows_b)
    else:
        rows_a = _read_jsonl(Path(run_a) / "out.jsonl")
        triage_rows = _diff_triage_rows(rows_a, rows_b)

    ranked = _sort_rows(triage_rows, score)
    selected = ranked[: max(0, int(top_n))]

    target = Path(out_path) if out_path else _default_output_path(run_b_path, Path(run_a) if run_a else None, score, output_format)
    target.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "jsonl":
        _write_jsonl(target, selected)
    else:
        _write_csv(target, selected)

    return {
        "spec_version": "1.0",
        "mode": "diff" if run_a else "single",
        "run_b": str(run_b_path),
        "run_a": str(Path(run_a)) if run_a else None,
        "score": score,
        "top_n_requested": max(0, int(top_n)),
        "top_n_returned": len(selected),
        "output_format": output_format,
        "output_path": str(target),
        "triage_preview": selected[: min(5, len(selected))],
    }

