"""Generate deterministic runs/index.json from runs/index.jsonl."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tonesight_ns8.run_index import run_index_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate deterministic index.json from index.jsonl.",
    )
    parser.add_argument("--out-root", default="runs", help="Runs artifact root directory.")
    parser.add_argument("--index-jsonl", help="Optional explicit index.jsonl source path.")
    parser.add_argument("--out", help="Optional explicit output path for index.json.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_index_json(
        args.out_root,
        index_jsonl_path=args.index_jsonl,
        out_path=args.out,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
