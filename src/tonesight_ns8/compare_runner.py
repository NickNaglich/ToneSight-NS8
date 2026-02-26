"""Deterministic run-to-run comparison runner."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .compatibility import compatibility_issues
from .ns8 import compute_A

class CompareInputError(ValueError):
    """Deterministic, actionable compare-input error."""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CompareInputError(f"missing_required_file:{path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CompareInputError(f"malformed_json:{path.name}:line={exc.lineno}:col={exc.colno}") from exc
    if not isinstance(payload, dict):
        raise CompareInputError(f"invalid_json_object:{path.name}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise CompareInputError(f"missing_required_file:{path.name}")
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CompareInputError(f"malformed_jsonl:{path.name}:line={i}:col={exc.colno}") from exc
        if not isinstance(row, dict):
            raise CompareInputError(f"invalid_jsonl_row_object:{path.name}:line={i}")
        rows.append(row)
    return rows


def _validate_receipt_compatibility(
    receipt_a: dict[str, Any],
    receipt_b: dict[str, Any],
    *,
    require_dataset_match: bool = True,
    require_pinned_model_identity: bool = False,
) -> None:
    issues = compatibility_issues(
        receipt_a,
        receipt_b,
        require_dataset_match=require_dataset_match,
        require_pinned_model_identity=require_pinned_model_identity,
    )
    if not issues:
        return
    issue = issues[0]
    reason = issue.get("reason", "")
    if reason == "dataset_hash_mismatch":
        raise CompareInputError(
            f"incompatible_receipts:dataset_hash:{issue.get('expected_dataset_hash','')}!={issue.get('actual_dataset_hash','')}"
        )
    if reason == "spec_version_mismatch":
        raise CompareInputError(f"incompatible_receipts:spec_version:{issue.get('expected','')}!={issue.get('actual','')}")
    raise CompareInputError(f"incompatible_receipts:{reason}:{issue.get('expected','')}!={issue.get('actual','')}")


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


def group_l1_stats(rows: list[dict[str, Any]], group_by: str) -> dict[str, dict[str, float]]:
    """Compute deterministic per-group count/avg_l1/fail_rate from out.jsonl rows."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        raw_value = row.get(group_by)
        key = "__missing__" if raw_value in (None, "") else str(raw_value)
        groups.setdefault(key, []).append(row)

    out: dict[str, dict[str, float]] = {}
    for key in sorted(groups):
        group_rows = groups[key]
        n = len(group_rows)
        l1_sum = sum(float(r.get("compliance_l1", 0.0)) for r in group_rows)
        fail_count = sum(1 for r in group_rows if not bool(r.get("pass", False)))
        out[key] = {
            "count": float(n),
            "avg_l1": (l1_sum / n) if n else 0.0,
            "fail_rate": (fail_count / n) if n else 0.0,
        }
    return out


def _trend(delta: float | None, *, higher_is_better: bool) -> str:
    if delta is None:
        return "unknown"
    if delta == 0.0:
        return "unchanged"
    if higher_is_better:
        return "improved" if delta > 0 else "regressed"
    return "improved" if delta < 0 else "regressed"


def _component_delta(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value is None:
        return None
    return float(value)


def _anchor_ring_distance(a: int, b: int) -> float:
    delta = abs(int(a) - int(b))
    return float(min(delta, 8 - delta))


def _anchor_from_vad(vad: Any) -> int | None:
    if not isinstance(vad, dict):
        return None
    try:
        v = int(vad["V"])
        a = int(vad["A"])
        d = int(vad["D"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (1 <= v <= 8 and 1 <= a <= 8 and 1 <= d <= 8):
        return None
    return int(compute_A("TLF", v, a, d, 8))


def _row_distance(row: dict[str, Any], mode: str) -> float:
    if mode == "l1":
        return float(row.get("compliance_l1", 0.0))
    if mode != "topology":
        raise ValueError(f"Unsupported distance mode: {mode}")

    pred_anchor = _anchor_from_vad(row.get("pred_vad"))
    target_anchor = _anchor_from_vad(row.get("target_vad"))
    if pred_anchor is not None and target_anchor is not None:
        return _anchor_ring_distance(pred_anchor, target_anchor)
    return float(row.get("compliance_l1", 0.0))


def _render_compare_report_html(compare_summary: dict[str, Any]) -> str:
    run_a = compare_summary["run_a"]
    run_b = compare_summary["run_b"]
    metrics = compare_summary["metrics"]
    coverage = compare_summary["regression_coverage"]
    regressions = compare_summary["top_regressions"]
    per_label = compare_summary["per_label_delta"]
    distance_mode = compare_summary.get("distance_mode", "l1")
    title = f"ToneSight Compare Report: {run_a.get('run_id')} -> {run_b.get('run_id')}"
    def _bar_width(value: Any, scale: float = 0.35) -> int:
        try:
            magnitude = abs(float(value))
        except (TypeError, ValueError):
            magnitude = 0.0
        return max(2, min(100, int(round(magnitude * 100 * scale))))

    def _bar_color(value: Any) -> str:
        try:
            val = float(value)
        except (TypeError, ValueError):
            return "#94a3b8"
        return "#2f9e44" if val <= 0 else "#c92a2a"

    delta_blocks = [
        ("delta_pass_rate", metrics.get("delta_pass_rate")),
        ("delta_avg_l1", metrics.get("delta_avg_l1")),
        ("delta_p95_l1", metrics.get("delta_p95_l1")),
    ]
    delta_bars_html = "".join(
        (
            '<div class="bar-kpi">'
            f'<div class="k">{html.escape(name)}</div>'
            f'<div class="v">{value}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{_bar_width(value)}%;background:{_bar_color(value)}"></div></div>'
            "</div>"
        )
        for name, value in delta_blocks
    )
    rows_html = "".join(
        (
            "<tr>"
            f"<td>{html.escape(str(r.get('id')))}</td>"
            f"<td>{html.escape(str(r.get('label')))}</td>"
            f"<td>{r.get('l1_a')}</td>"
            f"<td>{r.get('l1_b')}</td>"
            f"<td>{r.get('delta_l1')}</td>"
            f"<td>{r.get('delta_v')}</td>"
            f"<td>{r.get('delta_a')}</td>"
            f"<td>{r.get('delta_d')}</td>"
            "</tr>"
        )
        for r in regressions
    )
    labels_html = "".join(
        (
            "<tr>"
            f"<td>{html.escape(label)}</td>"
            f"<td>{payload.get('delta_avg_l1')}</td>"
            f"<td>{payload.get('delta_count')}</td>"
            "</tr>"
        )
        for label, payload in sorted(per_label.items())
    )
    if not rows_html:
        rows_html = '<tr><td colspan="8">No regressions in top_n window.</td></tr>'
    if not labels_html:
        labels_html = '<tr><td colspan="3">No shared labels between runs.</td></tr>'
    trend_state = str(metrics.get("pass_rate_trend", "unknown"))
    badge = "PASS"
    if trend_state == "regressed":
        badge = "REGRESSED"
    elif trend_state == "unknown":
        badge = "INCOMPATIBLE"
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        f"<title>{html.escape(title)}</title>\n"
        "<style>\n"
        ":root{--bg:#f3f6fb;--card:#ffffff;--ink:#12243c;--muted:#51657f;--line:#ced9e8;--ok:#2f9e44;--bad:#c92a2a;--warn:#e67700;}\n"
        "*{box-sizing:border-box} body{margin:0;font-family:Segoe UI,Trebuchet MS,sans-serif;background:radial-gradient(circle at 12% 12%,#e0e9f7 0%,#f6f9ff 55%,#fbfdff 100%);color:var(--ink)}\n"
        ".wrap{max-width:1220px;margin:0 auto;padding:16px}.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:12px}\n"
        ".top{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}.badge{padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700;color:#fff}\n"
        ".badge.pass{background:var(--ok)}.badge.regressed{background:var(--bad)}.badge.incompatible{background:var(--warn)}\n"
        ".meta{color:var(--muted);font-size:12px}.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.kpi{border:1px solid var(--line);border-radius:8px;padding:8px;background:#f9fbff}\n"
        ".bars{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:8px}.bar-kpi{border:1px solid var(--line);border-radius:8px;padding:8px;background:#f9fbff}\n"
        ".bar-track{height:8px;background:#e7eefb;border-radius:999px;overflow:hidden;margin-top:6px}.bar-fill{height:8px;border-radius:999px}\n"
        ".k{font-size:11px;color:var(--muted)}.v{font-weight:700;font-size:15px;margin-top:2px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}\n"
        "table{width:100%;border-collapse:collapse}th,td{border:1px solid var(--line);padding:6px;text-align:left;font-size:12px}th{background:#f1f6ff}\n"
        "@media (max-width:900px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.grid2{grid-template-columns:1fr}}\n"
        "</style>\n"
        "</head>\n"
        "<body><main class=\"wrap\">\n"
        "<section class=\"panel top\">"
        f"<div><h1 style=\"margin:0\">Compare Report</h1><div class=\"meta\">{html.escape(title)}</div></div>"
        f"<span class=\"badge {'pass' if badge=='PASS' else ('regressed' if badge=='REGRESSED' else 'incompatible')}\">{badge}</span>"
        "</section>\n"
        "<section class=\"panel\">"
        "<div class=\"grid2\">"
        f"<div><div class=\"k\">run_a</div><div class=\"v\">{html.escape(str(run_a.get('run_id')))}</div><div class=\"meta\">{html.escape(str(run_a.get('path')))}</div></div>"
        f"<div><div class=\"k\">run_b</div><div class=\"v\">{html.escape(str(run_b.get('run_id')))}</div><div class=\"meta\">{html.escape(str(run_b.get('path')))}</div></div>"
        "</div>"
        f"<div class=\"meta\" style=\"margin-top:8px\">distance_mode: {html.escape(str(distance_mode))}</div>"
        "</section>\n"
        "<section class=\"panel\"><h2 style=\"margin:0 0 8px\">Delta KPIs</h2>"
        "<div class=\"kpis\">"
        f"<div class=\"kpi\"><div class=\"k\">delta_pass_rate</div><div class=\"v\">{metrics.get('delta_pass_rate')}</div></div>"
        f"<div class=\"kpi\"><div class=\"k\">delta_avg_l1</div><div class=\"v\">{metrics.get('delta_avg_l1')}</div></div>"
        f"<div class=\"kpi\"><div class=\"k\">delta_p95_l1</div><div class=\"v\">{metrics.get('delta_p95_l1')}</div></div>"
        f"<div class=\"kpi\"><div class=\"k\">pass_rate_trend</div><div class=\"v\">{metrics.get('pass_rate_trend')}</div></div>"
        "</div>"
        f"<div class=\"bars\">{delta_bars_html}</div>"
        "</section>\n"
        "<section class=\"panel\"><h2 style=\"margin:0 0 8px\">Regression Coverage</h2>"
        "<div class=\"kpis\">"
        f"<div class=\"kpi\"><div class=\"k\">total</div><div class=\"v\">{coverage.get('regression_count_total')}</div></div>"
        f"<div class=\"kpi\"><div class=\"k\">top_n_requested</div><div class=\"v\">{coverage.get('top_n_requested')}</div></div>"
        f"<div class=\"kpi\"><div class=\"k\">top_n_returned</div><div class=\"v\">{coverage.get('top_n_returned')}</div></div>"
        f"<div class=\"kpi\"><div class=\"k\">truncated</div><div class=\"v\">{coverage.get('truncated')}</div></div>"
        "</div></section>\n"
        '<section class="panel">\n'
        "<h2 style=\"margin:0 0 8px\">Top Regressions</h2>\n"
        "<table><thead><tr><th>id</th><th>label</th><th>l1_a</th><th>l1_b</th><th>delta_l1</th><th>delta_v</th><th>delta_a</th><th>delta_d</th></tr></thead><tbody>\n"
        f"{rows_html}\n"
        "</tbody></table>\n"
        "</section>\n"
        '<section class="panel">\n'
        "<h2 style=\"margin:0 0 8px\">Per-Label Delta</h2>\n"
        "<table><thead><tr><th>label</th><th>delta_avg_l1</th><th>delta_count</th></tr></thead><tbody>\n"
        f"{labels_html}\n"
        "</tbody></table>\n"
        "</section>\n"
        "</main></body>\n"
        "</html>\n"
    )


def run_compare(
    run_a: str,
    run_b: str,
    *,
    top_n: int = 10,
    distance_mode: str = "l1",
    write_artifact: bool = False,
    require_dataset_match: bool = True,
    require_pinned_model_identity: bool = False,
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
    _validate_receipt_compatibility(
        receipt_a,
        receipt_b,
        require_dataset_match=require_dataset_match,
        require_pinned_model_identity=require_pinned_model_identity,
    )

    by_id_a = _index_rows(out_a)
    by_id_b = _index_rows(out_b)
    ids_common = sorted(set(by_id_a).intersection(by_id_b))

    regressions: list[dict[str, Any]] = []
    for row_id in ids_common:
        a_row = by_id_a[row_id]
        b_row = by_id_b[row_id]
        l1_a = float(a_row.get("compliance_l1", 0.0))
        l1_b = float(b_row.get("compliance_l1", 0.0))
        distance_a = _row_distance(a_row, distance_mode)
        distance_b = _row_distance(b_row, distance_mode)
        delta_l1 = l1_b - l1_a
        delta_distance = distance_b - distance_a
        if delta_distance <= 0:
            continue
        regressions.append(
            {
                "id": row_id,
                "label": b_row.get("label"),
                "l1_a": l1_a,
                "l1_b": l1_b,
                "delta_l1": delta_l1,
                "distance_a": distance_a,
                "distance_b": distance_b,
                "delta_distance": delta_distance,
                "delta_v": _safe_delta(_component_delta(a_row, "delta_v"), _component_delta(b_row, "delta_v")),
                "delta_a": _safe_delta(_component_delta(a_row, "delta_a"), _component_delta(b_row, "delta_a")),
                "delta_d": _safe_delta(_component_delta(a_row, "delta_d"), _component_delta(b_row, "delta_d")),
            }
        )

    regressions.sort(key=lambda row: (-row["delta_distance"], str(row["id"])))
    regression_count_total = len(regressions)
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

    delta_pass_rate = _safe_delta(summary_a.get("pass_rate"), summary_b.get("pass_rate"))
    delta_avg_l1 = _safe_delta(summary_a.get("avg_l1"), summary_b.get("avg_l1"))
    delta_p95_l1 = _safe_delta(summary_a.get("p95_l1"), summary_b.get("p95_l1"))

    compare_summary: dict[str, Any] = {
        "spec_version": "1.0",
        "distance_mode": distance_mode,
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
            "delta_pass_rate": delta_pass_rate,
            "delta_avg_l1": delta_avg_l1,
            "delta_p95_l1": delta_p95_l1,
            "pass_rate_trend": _trend(delta_pass_rate, higher_is_better=True),
            "avg_l1_trend": _trend(delta_avg_l1, higher_is_better=False),
            "p95_l1_trend": _trend(delta_p95_l1, higher_is_better=False),
        },
        "rows": {
            "count_a": len(out_a),
            "count_b": len(out_b),
            "count_common_ids": len(ids_common),
            "count_only_in_a": len(set(by_id_a).difference(by_id_b)),
            "count_only_in_b": len(set(by_id_b).difference(by_id_a)),
        },
        "per_label_delta": per_label_delta,
        "regression_coverage": {
            "regression_count_total": regression_count_total,
            "top_n_requested": max(0, int(top_n)),
            "top_n_returned": len(regressions),
            "truncated": regression_count_total > len(regressions),
        },
        "top_regressions": regressions,
    }

    compare_path: str | None = None
    compare_report_path: str | None = None
    if write_artifact:
        parent = run_b_path / "comparisons" / run_a_path.name
        parent.mkdir(parents=True, exist_ok=True)
        target = parent / "compare_summary.json"
        target.write_text(json.dumps(compare_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        compare_path = str(target)
        report_target = parent / "compare_report.html"
        report_target.write_text(_render_compare_report_html(compare_summary), encoding="utf-8")
        compare_report_path = str(report_target)

    return {
        "compare_summary": compare_summary,
        "compare_summary_path": compare_path,
        "compare_report_path": compare_report_path,
    }
