"""Regenerate expected NS8 vector fields from the reference oracle.

Usage:
  python tools/regen_vectors.py
  python tools/regen_vectors.py --in vectors/ns8_test_vectors.json --out vectors/ns8_test_vectors.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ns8_ref import InvalidInput, ns8_A, ns8_route


def regenerate_vectors(in_path: Path, out_path: Path) -> None:
    vectors = json.loads(in_path.read_text(encoding="utf-8"))
    updated = []

    for vector in vectors:
        item = dict(vector)
        if item.get("expected_error"):
            # Invalid vectors intentionally preserve expected_error contract.
            updated.append(item)
            continue

        family = item["family"]
        r = int(item["r"])
        c = int(item["c"])
        k = int(item["k"])
        n = int(item.get("N", 8))

        try:
            route = ns8_route(family, r, c, k, n)
            a_val = ns8_A(family, r, c, k, n)
        except InvalidInput as exc:
            raise RuntimeError(f"Valid vector became invalid: {item.get('id')} ({exc})") from exc

        item["expected_seed_family"] = route.seed_family
        item["expected_r_prime"] = route.r_prime
        item["expected_c_prime"] = route.c_prime
        item["expected_A"] = a_val
        updated.append(item)

    out_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate NS8 vector expected fields.")
    parser.add_argument("--in", dest="in_file", default="vectors/ns8_test_vectors.json")
    parser.add_argument("--out", dest="out_file", default="vectors/ns8_test_vectors.json")
    args = parser.parse_args()

    in_path = Path(args.in_file)
    out_path = Path(args.out_file)
    regenerate_vectors(in_path, out_path)


if __name__ == "__main__":
    main()
