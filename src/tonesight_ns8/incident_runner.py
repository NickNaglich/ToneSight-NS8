"""Deterministic incident response package generator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .bundle_runner import run_bundle
from .compare_runner import run_compare
from .triage_runner import run_triage


def _default_incident_report_path(run_b: Path, run_a: Path) -> Path:
    target = run_b / "incidents" / run_a.name / "incident_report.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _incident_markdown(
    *,
    run_a: Path,
    run_b: Path,
    compare_summary_path: str | None,
    triage_output_path: str,
    bundle_path: str,
) -> str:
    return (
        "# ToneSight Incident Report\n\n"
        "## Run Pair\n\n"
        f"- baseline_run: `{run_a}`\n"
        f"- candidate_run: `{run_b}`\n\n"
        "## Artifacts\n\n"
        f"- compare_summary_json: `{compare_summary_path}`\n"
        f"- triage_export: `{triage_output_path}`\n"
        f"- forensics_bundle: `{bundle_path}`\n\n"
        "## Triage Notes Template\n\n"
        "- impact_assessment:\n"
        "- suspected_root_cause:\n"
        "- mitigation_actions:\n"
        "- follow_up_tests:\n"
    )


def run_incident(
    run_a: str,
    run_b: str,
    *,
    top_n: int = 50,
    triage_score: str = "delta_compliance_l1",
    triage_format: str = "jsonl",
    include_source_paths: bool = False,
    report_path: str | None = None,
) -> dict[str, Any]:
    """Create deterministic compare + triage + bundle + markdown incident package."""
    run_a_path = Path(run_a)
    run_b_path = Path(run_b)

    compare = run_compare(str(run_a_path), str(run_b_path), top_n=top_n, write_artifact=True)
    triage = run_triage(
        str(run_b_path),
        run_a=str(run_a_path),
        top_n=top_n,
        score=triage_score,
        output_format=triage_format,
    )
    bundle = run_bundle(
        str(run_b_path),
        run_a=str(run_a_path),
        include_source_paths=include_source_paths,
    )

    incident_report_path = Path(report_path) if report_path else _default_incident_report_path(run_b_path, run_a_path)
    incident_report_path.parent.mkdir(parents=True, exist_ok=True)
    incident_report_path.write_text(
        _incident_markdown(
            run_a=run_a_path,
            run_b=run_b_path,
            compare_summary_path=compare.get("compare_summary_path"),
            triage_output_path=str(triage["output_path"]),
            bundle_path=str(bundle["bundle_path"]),
        ),
        encoding="utf-8",
    )

    return {
        "spec_version": "1.0",
        "run_a": str(run_a_path),
        "run_b": str(run_b_path),
        "compare_summary_path": compare.get("compare_summary_path"),
        "compare_report_path": compare.get("compare_report_path"),
        "triage_output_path": triage["output_path"],
        "bundle_path": bundle["bundle_path"],
        "incident_report_path": str(incident_report_path),
        "triage_preview": triage.get("triage_preview", []),
    }
