"""Deterministic run-to-run comparison runner."""

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


def _index_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(rows):
        row_id = row.get("id")
        key = str(row_id) if row_id is not None else f"__row_{i}"
        indexed[key] = row
    return indexed


def _safe_delta(a: float | int | None, b: float | int | None) -> float | None:
    if a is None or b is None:
        return None
    return float(b) - float(a)


def _label_stats(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    labels: dict[str, list[float]] = {}
    for row in rows:
        label = row.get("label")
        if not label:
            continue
        labels.setdefault(str(label), []).append(float(row.get("compliance_l1", 0.0)))

    out: dict[str, dict[str, float]] = {}
    for label in sorted(labels):
        values = labels[label]
        n = len(values)
        out[label] = {
            "count": float(n),
            "avg_l1": (sum(values) / n) if n else 0.0,
        }
    return out


def run_compare(
    run_a: str,
    run_b: str,
    *,
    top_n: int = 10,
    write_artifact: bool = False,
) -> dict[str, Any]:
    """Compare two eval runs deterministically."""
    run_a_path = Path(run_a)
    run_b_path = Path(run_b)

    summary_a = _read_json(run_a_path / "eval_summary.json")
    summary_b = _read_json(run_b_path / "eval_summary.json")
    receipt_a = _read_json(run_a_path / "receipt.json")
    receipt_b = _read_json(run_b_path / "receipt.json")
    out_a = _read_jsonl(run_a_path / "out.jsonl")
    out_b = _read_jsonl(run_b_path / "out.jsonl")

    by_id_a = _index_rows(out_a)
    by_id_b = _index_rows(out_b)
    ids_common = sorted(set(by_id_a).intersection(by_id_b))

    regressions: list[dict[str, Any]] = []
    for row_id in ids_common:
        a_row = by_id_a[row_id]
        b_row = by_id_b[row_id]
        delta = float(b_row.get("compliance_l1", 0.0)) - float(a_row.get("compliance_l1", 0.0))
        if delta <= 0:
            continue
        regressions.append(
            {
                "id": row_id,
                "label": b_row.get("label"),
                "l1_a": float(a_row.get("compliance_l1", 0.0)),
                "l1_b": float(b_row.get("compliance_l1", 0.0)),
                "delta_l1": delta,
            }
        )

    regressions.sort(key=lambda row: (-row["delta_l1"], str(row["id"])))
    regressions = regressions[: max(0, int(top_n))]

    labels_a = _label_stats(out_a)
    labels_b = _label_stats(out_b)
    labels_common = sorted(set(labels_a).intersection(labels_b))
    per_label_delta: dict[str, dict[str, float | None]] = {}
    for label in labels_common:
        per_label_delta[label] = {
            "delta_avg_l1": _safe_delta(labels_a[label]["avg_l1"], labels_b[label]["avg_l1"]),
            "delta_count": _safe_delta(labels_a[label]["count"], labels_b[label]["count"]),
        }

    compare_summary: dict[str, Any] = {
        "spec_version": "1.0",
        "run_a": {
            "path": str(run_a_path),
            "run_id": summary_a.get("run_id"),
            "dataset_hash": receipt_a.get("dataset_hash"),
        },
        "run_b": {
            "path": str(run_b_path),
            "run_id": summary_b.get("run_id"),
            "dataset_hash": receipt_b.get("dataset_hash"),
        },
        "metrics": {
            "delta_pass_rate": _safe_delta(summary_a.get("pass_rate"), summary_b.get("pass_rate")),
            "delta_avg_l1": _safe_delta(summary_a.get("avg_l1"), summary_b.get("avg_l1")),
            "delta_p95_l1": _safe_delta(summary_a.get("p95_l1"), summary_b.get("p95_l1")),
        },
        "rows": {
            "count_a": len(out_a),
            "count_b": len(out_b),
            "count_common_ids": len(ids_common),
        },
        "per_label_delta": per_label_delta,
        "top_regressions": regressions,
    }

    compare_path: str | None = None
    if write_artifact:
        parent = run_b_path / "comparisons" / run_a_path.name
        parent.mkdir(parents=True, exist_ok=True)
        target = parent / "compare_summary.json"
        target.write_text(json.dumps(compare_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        compare_path = str(target)

    return {
        "compare_summary": compare_summary,
        "compare_summary_path": compare_path,
    }
