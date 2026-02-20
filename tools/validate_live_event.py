"""Validate canonical LiveEvent JSONL envelope for shadow-mode ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tonesight_ns8.live_event_validation import LiveEventValidationError, validate_live_event_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ToneSight LiveEvent JSONL contract.")
    parser.add_argument("path", nargs="?", default="tests/fixtures/live_event.valid.jsonl")
    args = parser.parse_args(argv)
    target = Path(args.path)
    try:
        validate_live_event_file(target)
    except LiveEventValidationError as exc:
        payload = {
            "valid": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        }
        print(json.dumps(payload, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps({"valid": True, "path": str(target)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
