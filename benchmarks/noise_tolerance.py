from __future__ import annotations

import argparse
import json

from tonesight_ns8.benchmark_runner import run_noise_tolerance_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic noise tolerance benchmark.")
    parser.add_argument("--goldset", default="data/goldset.jsonl")
    args = parser.parse_args()
    payload = run_noise_tolerance_benchmark(args.goldset)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

