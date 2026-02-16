"""Validate defaults config JSON schema and basic types."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tonesight_ns8.defaults_schema import validate_defaults_payload


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("config/defaults.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_defaults_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
