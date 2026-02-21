"""Thin CLI wrapper over ToneSight NS8 library functions."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .defaults import ARTIFACT_DEFAULTS, EVAL_DEFAULTS
from .mapping import get_mapping, list_mappings
from . import (
    SegmentRecord,
    run_bundle,
    run_canary,
    run_gate,
    run_incident,
    run_compare,
    run_eval_compare,
    run_eval,
    run_live_capture,
    run_live_replay,
    run_live_verify,
    run_index,
    run_retention_purge,
    run_trend,
    run_triage,
    summarize_session,
    summarize_speaker,
    tonesight_from_label,
    tonesight_from_vad,
)

_FAMILIES = ("TLF", "TRF", "BLF", "BRF", "TRB", "TLB", "BLB", "BRB")


def _int_1_to_8(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from exc
    if parsed < 1 or parsed > 8:
        raise argparse.ArgumentTypeError(f"{parsed} is out of range; expected integer in 1..8")
    return parsed


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError(f"{parsed} is invalid; expected integer >= 0")
    return parsed


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    return value


def _trace_from_eval_result(result: dict[str, Any]) -> dict[str, Any]:
    receipt = result.get("receipt", {})
    return {
        "spec_version": receipt.get("spec_version"),
        "dataset_hash": receipt.get("dataset_hash"),
        "taxonomy_hash": receipt.get("taxonomy_hash"),
        "defaults_hash": receipt.get("defaults_hash"),
    }


def _cmd_encode(args: argparse.Namespace) -> dict:
    _ = get_mapping(args.mapping)
    if args.label:
        if not args.taxonomy:
            raise ValueError("--taxonomy is required when --label is provided")
        return tonesight_from_label(
            label=args.label,
            family=args.family,
            r=args.r,
            c=args.c,
            k=args.k,
            taxonomy_path=args.taxonomy,
            mapping_id=args.mapping,
        )

    if args.V is None or args.A is None or args.D is None:
        raise ValueError("Provide either --label/--taxonomy or all of --V --A --D")
    return tonesight_from_vad(
        V=args.V,
        A=args.A,
        D=args.D,
        family=args.family,
        r=args.r,
        c=args.c,
        k=args.k,
        mapping_id=args.mapping,
    )


def _cmd_decode(args: argparse.Namespace) -> dict:
    mapping = get_mapping(args.mapping)
    seed_family, r_prime, c_prime, _ = mapping.resolve_to_seed(args.family, args.r, args.c, args.k, 8)
    anchor = mapping.compute_A(args.family, args.r, args.c, args.k, 8)
    return {
        "spec_version": "1.0",
        "input": {"family": args.family, "r": args.r, "c": args.c, "k": args.k},
        "route": {"seed_family": seed_family, "r_prime": r_prime, "c_prime": c_prime},
        "output": {"A": anchor},
    }


def _cmd_summarize(args: argparse.Namespace) -> dict:
    data = json.loads(Path(args.segments_json).read_text(encoding="utf-8"))
    segments = [SegmentRecord(**item) for item in data]
    speaker = summarize_speaker(segments)
    session = summarize_session(args.session_id, segments, arousal_spike_threshold=args.spike_threshold)
    return {
        "session": _to_jsonable(session),
        "speakers": _to_jsonable(speaker),
    }


def _cmd_eval(args: argparse.Namespace) -> dict:
    result = run_eval(
        goldset_path=args.goldset,
        out_root=args.out_root,
        taxonomy_path=args.taxonomy,
        threshold_l1=args.threshold_l1,
        calibration_path=args.calibration,
        capture_gpu=args.capture_gpu,
        mlflow_tracking_uri=args.mlflow_tracking_uri,
    )
    result["trace"] = _trace_from_eval_result(result)
    return result


def _cmd_compare(args: argparse.Namespace) -> dict:
    return run_compare(
        args.run_a,
        args.run_b,
        top_n=args.top_n,
        write_artifact=args.write,
    )


def _cmd_eval_compare(args: argparse.Namespace) -> dict:
    result = run_eval_compare(
        goldset_path=args.goldset,
        out_root=args.out_root,
        taxonomy_path=args.taxonomy,
        threshold_l1=args.threshold_l1,
        calibration_path=args.calibration,
        capture_gpu=args.capture_gpu,
        mlflow_tracking_uri=args.mlflow_tracking_uri,
        top_n=args.top_n,
    )
    eval_result = result.get("eval", {})
    result["trace"] = _trace_from_eval_result(eval_result) if isinstance(eval_result, dict) else {}
    return result


def _cmd_gate(args: argparse.Namespace) -> dict:
    return run_gate(
        args.run_a,
        args.run_b,
        profile=args.profile,
        gate_profiles_path=args.gate_profiles,
        min_pass_rate_delta=args.min_pass_rate_delta,
        max_avg_l1_delta=args.max_avg_l1_delta,
        max_p95_l1_delta=args.max_p95_l1_delta,
        top_n=args.top_n,
        require_dataset_match=not args.allow_dataset_mismatch,
    )


def _cmd_triage(args: argparse.Namespace) -> dict:
    return run_triage(
        args.run_b,
        run_a=args.run_a,
        top_n=args.top_n,
        score=args.score,
        output_format=args.format,
        out_path=args.out,
    )


def _cmd_bundle(args: argparse.Namespace) -> dict:
    return run_bundle(
        args.run_b,
        run_a=args.run_a,
        out_path=args.out,
        include_source_paths=args.include_source_paths,
    )


def _cmd_trend(args: argparse.Namespace) -> dict:
    return run_trend(
        args.out_root,
        group_by=args.group_by,
        out_path=args.out,
    )


def _cmd_canary(args: argparse.Namespace) -> dict:
    return run_canary(
        args.capture,
        baseline_out_root=args.baseline_out_root,
        candidate_out_root=args.candidate_out_root,
        baseline_taxonomy_path=args.baseline_taxonomy,
        candidate_taxonomy_path=args.candidate_taxonomy,
        baseline_threshold_l1=args.baseline_threshold_l1,
        candidate_threshold_l1=args.candidate_threshold_l1,
        shadow_strict=args.shadow_strict,
        redact=not args.disable_redaction,
        top_n=args.top_n,
        profile=args.profile,
        gate_profiles_path=args.gate_profiles,
        min_pass_rate_delta=args.min_pass_rate_delta,
        max_avg_l1_delta=args.max_avg_l1_delta,
        max_p95_l1_delta=args.max_p95_l1_delta,
        allow_dataset_mismatch=args.allow_dataset_mismatch,
    )


def _cmd_incident(args: argparse.Namespace) -> dict:
    return run_incident(
        args.run_a,
        args.run_b,
        top_n=args.top_n,
        triage_score=args.triage_score,
        triage_format=args.triage_format,
        include_source_paths=args.include_source_paths,
        report_path=args.report,
    )


def _cmd_live_capture(args: argparse.Namespace) -> dict:
    return run_live_capture(
        args.events,
        out_root=args.out_root,
    )


def _cmd_live_replay(args: argparse.Namespace) -> dict:
    return run_live_replay(
        args.capture,
        out_root=args.out_root,
        taxonomy_path=args.taxonomy,
        threshold_l1=args.threshold_l1,
        shadow_strict=args.shadow_strict,
        redact=not args.disable_redaction,
    )


def _cmd_live_verify(args: argparse.Namespace) -> dict:
    return run_live_verify(
        args.capture,
        out_root=args.out_root,
        taxonomy_path=args.taxonomy,
        threshold_l1=args.threshold_l1,
        shadow_strict=args.shadow_strict,
        redact=not args.disable_redaction,
    )


def _cmd_purge(args: argparse.Namespace) -> dict:
    return run_retention_purge(
        out_root=args.out_root,
        older_than_days=args.older_than_days,
        dry_run=not args.apply,
        include_bundles=args.include_bundles,
        include_captures=args.include_captures,
    )


def _cmd_index_runs(args: argparse.Namespace) -> dict:
    return run_index(
        args.out_root,
        out_path=args.out,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tonesight-ns8",
        description="Deterministic NS8 encoding and evaluation toolkit.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    encode = sub.add_parser("encode", help="Emit deterministic receipt from label or VAD.")
    encode.add_argument("--family", required=True, choices=_FAMILIES)
    encode.add_argument("--r", required=True, type=_int_1_to_8)
    encode.add_argument("--c", required=True, type=_int_1_to_8)
    encode.add_argument("--k", required=True, type=_int_1_to_8)
    encode.add_argument("--label")
    encode.add_argument("--taxonomy")
    encode.add_argument("--V", type=_int_1_to_8)
    encode.add_argument("--A", type=_int_1_to_8)
    encode.add_argument("--D", type=_int_1_to_8)
    encode.add_argument("--mapping", default="ns8", choices=list_mappings())
    encode.set_defaults(func=_cmd_encode)

    decode = sub.add_parser("decode", help="Resolve route and anchor from NS8 parameters.")
    decode.add_argument("--family", required=True, choices=_FAMILIES)
    decode.add_argument("--r", required=True, type=_int_1_to_8)
    decode.add_argument("--c", required=True, type=_int_1_to_8)
    decode.add_argument("--k", required=True, type=_int_1_to_8)
    decode.add_argument("--mapping", default="ns8", choices=list_mappings())
    decode.set_defaults(func=_cmd_decode)

    summarize = sub.add_parser("summarize", help="Summarize speakers/session from segment JSON.")
    summarize.add_argument("--segments-json", required=True)
    summarize.add_argument("--session-id", required=True)
    summarize.add_argument("--spike-threshold", type=_int_1_to_8, default=7)
    summarize.set_defaults(func=_cmd_summarize)

    eval_cmd = sub.add_parser("eval", help="Run deterministic goldset eval and write artifacts.")
    eval_cmd.add_argument("--goldset", default=ARTIFACT_DEFAULTS["goldset_path"])
    eval_cmd.add_argument("--out-root", default=EVAL_DEFAULTS["out_root"])
    eval_cmd.add_argument("--taxonomy", default=EVAL_DEFAULTS["taxonomy_path"])
    eval_cmd.add_argument("--threshold-l1", type=_non_negative_int, default=EVAL_DEFAULTS["threshold_l1"])
    eval_cmd.add_argument("--calibration", default=EVAL_DEFAULTS["calibration_path"])
    eval_cmd.add_argument("--capture-gpu", action="store_true")
    eval_cmd.add_argument("--mlflow-tracking-uri")
    eval_cmd.set_defaults(func=_cmd_eval)

    compare_cmd = sub.add_parser("compare", help="Compare two eval runs deterministically.")
    compare_cmd.add_argument("run_a")
    compare_cmd.add_argument("run_b")
    compare_cmd.add_argument("--top-n", type=_non_negative_int, default=10)
    compare_cmd.add_argument("--write", action="store_true")
    compare_cmd.set_defaults(func=_cmd_compare)

    eval_compare_cmd = sub.add_parser(
        "eval-compare",
        help="Run eval and compare against most recent compatible prior run.",
    )
    eval_compare_cmd.add_argument("--goldset", default=ARTIFACT_DEFAULTS["goldset_path"])
    eval_compare_cmd.add_argument("--out-root", default=EVAL_DEFAULTS["out_root"])
    eval_compare_cmd.add_argument("--taxonomy", default=EVAL_DEFAULTS["taxonomy_path"])
    eval_compare_cmd.add_argument("--threshold-l1", type=_non_negative_int, default=EVAL_DEFAULTS["threshold_l1"])
    eval_compare_cmd.add_argument("--calibration", default=EVAL_DEFAULTS["calibration_path"])
    eval_compare_cmd.add_argument("--capture-gpu", action="store_true")
    eval_compare_cmd.add_argument("--mlflow-tracking-uri")
    eval_compare_cmd.add_argument("--top-n", type=_non_negative_int, default=10)
    eval_compare_cmd.set_defaults(func=_cmd_eval_compare)

    gate_cmd = sub.add_parser("gate", help="Run deterministic CI gate checks over compare deltas.")
    gate_cmd.add_argument("--run-a", required=True, help="Baseline run directory path.")
    gate_cmd.add_argument("--run-b", required=True, help="Candidate run directory path.")
    gate_cmd.add_argument("--profile", help="Optional gate profile name from gate profiles config.")
    gate_cmd.add_argument("--gate-profiles", default="config/gate_profiles.json")
    gate_cmd.add_argument("--min-pass-rate-delta", type=float, default=None)
    gate_cmd.add_argument("--max-avg-l1-delta", type=float, default=None)
    gate_cmd.add_argument("--max-p95-l1-delta", type=float, default=None)
    gate_cmd.add_argument(
        "--allow-dataset-mismatch",
        action="store_true",
        help="Disable dataset_hash compatibility gate (useful for live non-goldset comparisons).",
    )
    gate_cmd.add_argument("--top-n", type=_non_negative_int, default=10)
    gate_cmd.set_defaults(func=_cmd_gate)

    triage_cmd = sub.add_parser("triage", help="Export deterministic triage rows from one run or a run pair.")
    triage_cmd.add_argument("--run-b", required=True, help="Candidate/current run directory path.")
    triage_cmd.add_argument("--run-a", help="Optional baseline run directory path for diff triage mode.")
    triage_cmd.add_argument("--top-n", type=_non_negative_int, default=50)
    triage_cmd.add_argument("--score", default="compliance_l1")
    triage_cmd.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
    triage_cmd.add_argument("--out", help="Optional explicit output path.")
    triage_cmd.set_defaults(func=_cmd_triage)

    bundle_cmd = sub.add_parser("bundle", help="Create deterministic forensics bundle zip for a run (and optional compare pair).")
    bundle_cmd.add_argument("--run-b", required=True, help="Candidate/current run directory path.")
    bundle_cmd.add_argument("--run-a", help="Optional baseline run directory path for compare artifact inclusion.")
    bundle_cmd.add_argument("--out", help="Optional explicit bundle output path (.zip).")
    bundle_cmd.add_argument("--include-source-paths", action="store_true", help="Include local source paths in bundle manifest (not external-safe).")
    bundle_cmd.set_defaults(func=_cmd_bundle)

    trend_cmd = sub.add_parser("trend", help="Create deterministic trend rollups across historical runs.")
    trend_cmd.add_argument("--out-root", default=EVAL_DEFAULTS["out_root"])
    trend_cmd.add_argument("--group-by", help="Optional row metadata field for per-run grouping summaries.")
    trend_cmd.add_argument("--out", help="Optional explicit trend summary output path.")
    trend_cmd.set_defaults(func=_cmd_trend)

    canary_cmd = sub.add_parser("canary", help="Replay one capture through baseline/candidate paths and gate compare deltas.")
    canary_cmd.add_argument("--capture", required=True, help="Capture directory or events.raw.jsonl path.")
    canary_cmd.add_argument("--baseline-out-root", default="runs/canary/baseline")
    canary_cmd.add_argument("--candidate-out-root", default="runs/canary/candidate")
    canary_cmd.add_argument("--baseline-taxonomy", default=EVAL_DEFAULTS["taxonomy_path"])
    canary_cmd.add_argument("--candidate-taxonomy", default=EVAL_DEFAULTS["taxonomy_path"])
    canary_cmd.add_argument("--baseline-threshold-l1", type=_non_negative_int, default=EVAL_DEFAULTS["threshold_l1"])
    canary_cmd.add_argument("--candidate-threshold-l1", type=_non_negative_int, default=EVAL_DEFAULTS["threshold_l1"])
    canary_cmd.add_argument("--shadow-strict", choices=("fail", "drop", "quarantine"), default="quarantine")
    canary_cmd.add_argument("--disable-redaction", action="store_true")
    canary_cmd.add_argument("--profile", help="Optional gate profile name from gate profiles config.")
    canary_cmd.add_argument("--gate-profiles", default="config/gate_profiles.json")
    canary_cmd.add_argument("--min-pass-rate-delta", type=float, default=None)
    canary_cmd.add_argument("--max-avg-l1-delta", type=float, default=None)
    canary_cmd.add_argument("--max-p95-l1-delta", type=float, default=None)
    canary_cmd.add_argument("--allow-dataset-mismatch", action="store_true")
    canary_cmd.add_argument("--top-n", type=_non_negative_int, default=10)
    canary_cmd.set_defaults(func=_cmd_canary)

    incident_cmd = sub.add_parser("incident", help="Generate deterministic compare/triage/bundle incident package.")
    incident_cmd.add_argument("--run-a", required=True, help="Baseline run directory path.")
    incident_cmd.add_argument("--run-b", required=True, help="Candidate/current run directory path.")
    incident_cmd.add_argument("--top-n", type=_non_negative_int, default=50)
    incident_cmd.add_argument("--triage-score", default="delta_compliance_l1")
    incident_cmd.add_argument("--triage-format", choices=("jsonl", "csv"), default="jsonl")
    incident_cmd.add_argument("--include-source-paths", action="store_true")
    incident_cmd.add_argument("--report", help="Optional explicit markdown report path.")
    incident_cmd.set_defaults(func=_cmd_incident)

    live_capture_cmd = sub.add_parser("live-capture", help="Validate and persist deterministic live capture artifacts.")
    live_capture_cmd.add_argument("--events", required=True, help="Path to LiveEvent JSONL input.")
    live_capture_cmd.add_argument("--out-root", default=EVAL_DEFAULTS["out_root"])
    live_capture_cmd.set_defaults(func=_cmd_live_capture)

    live_replay_cmd = sub.add_parser("live-replay", help="Replay a capture into deterministic run artifacts.")
    live_replay_cmd.add_argument("--capture", required=True, help="Capture directory or events.raw.jsonl path.")
    live_replay_cmd.add_argument("--out-root", default=EVAL_DEFAULTS["out_root"])
    live_replay_cmd.add_argument("--taxonomy", default=EVAL_DEFAULTS["taxonomy_path"])
    live_replay_cmd.add_argument("--threshold-l1", type=_non_negative_int, default=EVAL_DEFAULTS["threshold_l1"])
    live_replay_cmd.add_argument("--shadow-strict", choices=("fail", "drop", "quarantine"), default="quarantine")
    live_replay_cmd.add_argument("--disable-redaction", action="store_true")
    live_replay_cmd.set_defaults(func=_cmd_live_replay)

    live_verify_cmd = sub.add_parser("live-verify", help="Replay capture twice and assert deterministic artifact hashes.")
    live_verify_cmd.add_argument("--capture", required=True, help="Capture directory or events.raw.jsonl path.")
    live_verify_cmd.add_argument("--out-root", default=EVAL_DEFAULTS["out_root"])
    live_verify_cmd.add_argument("--taxonomy", default=EVAL_DEFAULTS["taxonomy_path"])
    live_verify_cmd.add_argument("--threshold-l1", type=_non_negative_int, default=EVAL_DEFAULTS["threshold_l1"])
    live_verify_cmd.add_argument("--shadow-strict", choices=("fail", "drop", "quarantine"), default="quarantine")
    live_verify_cmd.add_argument("--disable-redaction", action="store_true")
    live_verify_cmd.set_defaults(func=_cmd_live_verify)

    purge_cmd = sub.add_parser("purge", help="Purge old run artifacts with deterministic retention controls.")
    purge_cmd.add_argument("--out-root", default=EVAL_DEFAULTS["out_root"])
    purge_cmd.add_argument("--older-than-days", type=_non_negative_int, default=30)
    purge_cmd.add_argument("--apply", action="store_true", help="Actually delete paths (default is dry-run).")
    purge_cmd.add_argument("--include-bundles", action="store_true", help="Allow purging run directories containing bundles.")
    purge_cmd.add_argument("--include-captures", action="store_true", help="Allow purging capture directories under out-root/captures.")
    purge_cmd.set_defaults(func=_cmd_purge)

    index_cmd = sub.add_parser("index-runs", help="Build deterministic index.jsonl for discovered run artifacts.")
    index_cmd.add_argument("--out-root", default=EVAL_DEFAULTS["out_root"])
    index_cmd.add_argument("--out", help="Optional explicit index output path.")
    index_cmd.set_defaults(func=_cmd_index_runs)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        result = args.func(args)
        exit_code = int(result.pop("exit_code", 0)) if isinstance(result, dict) else 0
    except Exception as exc:
        error = {"error": {"type": exc.__class__.__name__, "message": str(exc)}}
        print(json.dumps(error, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(_to_jsonable(result), indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
