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
    run_compare,
    run_eval_compare,
    run_eval,
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
    return run_eval(
        goldset_path=args.goldset,
        out_root=args.out_root,
        taxonomy_path=args.taxonomy,
        threshold_l1=args.threshold_l1,
        calibration_path=args.calibration,
        capture_gpu=args.capture_gpu,
        mlflow_tracking_uri=args.mlflow_tracking_uri,
    )


def _cmd_compare(args: argparse.Namespace) -> dict:
    return run_compare(
        args.run_a,
        args.run_b,
        top_n=args.top_n,
        write_artifact=args.write,
    )


def _cmd_eval_compare(args: argparse.Namespace) -> dict:
    return run_eval_compare(
        goldset_path=args.goldset,
        out_root=args.out_root,
        taxonomy_path=args.taxonomy,
        threshold_l1=args.threshold_l1,
        calibration_path=args.calibration,
        capture_gpu=args.capture_gpu,
        mlflow_tracking_uri=args.mlflow_tracking_uri,
        top_n=args.top_n,
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        result = args.func(args)
    except Exception as exc:
        error = {"error": {"type": exc.__class__.__name__, "message": str(exc)}}
        print(json.dumps(error, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(_to_jsonable(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
