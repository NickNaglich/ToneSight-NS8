"""Deterministic end-to-end demo: eval -> compare -> benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tonesight_ns8 import run_benchmark_suite, run_compare, run_eval


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic NS8 drift demo.")
    parser.add_argument("--out-root", default="runs/demo")
    parser.add_argument("--goldset", default="data/goldset.jsonl")
    parser.add_argument("--taxonomy", default="taxonomy/tone_taxonomy.v1.json")
    parser.add_argument("--threshold-a", type=int, default=3, help="Baseline threshold_l1.")
    parser.add_argument("--threshold-b", type=int, default=2, help="Candidate threshold_l1.")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    baseline = run_eval(
        args.goldset,
        out_root=str(out_root),
        taxonomy_path=args.taxonomy,
        threshold_l1=args.threshold_a,
    )
    candidate = run_eval(
        args.goldset,
        out_root=str(out_root),
        taxonomy_path=args.taxonomy,
        threshold_l1=args.threshold_b,
    )
    compare = run_compare(
        baseline["out_dir"],
        candidate["out_dir"],
        top_n=10,
        write_artifact=True,
    )
    benchmark = run_benchmark_suite(
        suite="core",
        out_root=str(out_root),
        goldset_path=args.goldset,
    )

    payload = {
        "spec_version": "1.0",
        "demo": "ns8_drift_demo",
        "baseline_run_id": baseline["run_id"],
        "candidate_run_id": candidate["run_id"],
        "baseline_out_dir": baseline["out_dir"],
        "candidate_out_dir": candidate["out_dir"],
        "compare_summary_path": compare["compare_summary_path"],
        "benchmark_report_path": benchmark["artifacts"]["report"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

