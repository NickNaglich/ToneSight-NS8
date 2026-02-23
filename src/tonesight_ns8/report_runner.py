"""Deterministic static reporting over existing run artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .compare_runner import run_compare
from .gate_runner import run_gate

REPORT_SCHEMA_VERSION = "1.0"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid_json_object:{path}")
    return payload


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


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
    summary_b = _read_json(run_b_path / "eval_summary.json")
    receipt_b = _read_json(run_b_path / "receipt.json")

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
    if run_a:
        run_a_path = Path(run_a)
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

    report_payload: dict[str, Any] = {
        "spec_version": "1.0",
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "run_a_path": str(run_a_path) if run_a_path is not None else None,
        "run_b_path": str(run_b_path),
        "run_b": {
            "run_id": summary_b.get("run_id"),
            "count_rows": summary_b.get("count_rows"),
            "pass_rate": summary_b.get("pass_rate"),
            "avg_l1": summary_b.get("avg_l1"),
            "p95_l1": summary_b.get("p95_l1"),
            "summary_schema_version": summary_b.get("summary_schema_version"),
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
        "artifacts": {
            "run_b_eval_summary_json": str(run_b_path / "eval_summary.json"),
            "run_b_receipt_json": str(run_b_path / "receipt.json"),
        },
    }
    if run_a_path is not None:
        report_payload["artifacts"]["run_a_receipt_json"] = str(run_a_path / "receipt.json")
        report_name = f"report_{run_a_path.name}_to_{run_b_path.name}.json"
    else:
        report_name = f"report_{run_b_path.name}.json"

    target = Path(out_path) if out_path else (run_b_path / "reports" / report_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "report_path": str(target),
        "report_hash": _file_hash(target),
        "report": report_payload,
    }
