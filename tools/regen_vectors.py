"""Regenerate expected NS8 vector fields from the reference oracle.

Usage:
  python tools/regen_vectors.py --check
  python tools/regen_vectors.py --authorize
  python tools/regen_vectors.py --in vectors/ns8_test_vectors.json --out vectors/ns8_test_vectors.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ns8_ref import InvalidInput, ns8_A, ns8_route

SPEC_PATH = ROOT / "docs" / "SPEC_NS8.md"
CHANGE_LOG_PATH = ROOT / ".agent" / "LOGS" / "CHANGE_LOG.md"
PHASE_PLAN_PATH = ROOT / ".agent" / "TO-DO" / "PHASED_WORKFLOW.md"
PHASE_AUTH_MARKER = "VECTOR_REGEN_AUTHORIZED"


def _extract_spec_version(spec_path: Path) -> str:
    text = spec_path.read_text(encoding="utf-8")
    match = re.search(r'spec_version:\s*"([^"]+)"', text)
    if not match:
        raise RuntimeError(f"Unable to determine spec_version from {spec_path}")
    return match.group(1)


def _assert_regen_authorized(spec_path: Path, change_log_path: Path, phase_plan_path: Path) -> str:
    spec_version = _extract_spec_version(spec_path)
    if spec_version == "1.0":
        raise RuntimeError(
            "Vector regeneration is blocked: spec_version is still 1.0. "
            "Bump docs/SPEC_NS8.md before regenerating vectors."
        )

    change_log = change_log_path.read_text(encoding="utf-8")
    if f"spec_version" not in change_log or spec_version not in change_log:
        raise RuntimeError(
            f"Vector regeneration is blocked: {change_log_path} must document spec_version {spec_version} change."
        )

    phase_plan = phase_plan_path.read_text(encoding="utf-8")
    if PHASE_AUTH_MARKER not in phase_plan or spec_version not in phase_plan:
        raise RuntimeError(
            "Vector regeneration is blocked: phase plan must include "
            f"{PHASE_AUTH_MARKER} and the target spec version ({spec_version})."
        )
    return spec_version


def _recomputed_expectations(item: dict) -> tuple[str, int, int, int]:
    family = item["family"]
    r = int(item["r"])
    c = int(item["c"])
    k = int(item["k"])
    n = int(item.get("N", 8))

    route = ns8_route(family, r, c, k, n)
    a_val = ns8_A(family, r, c, k, n)
    return (route.seed_family, route.r_prime, route.c_prime, a_val)


def check_vectors(in_path: Path) -> list[str]:
    vectors = json.loads(in_path.read_text(encoding="utf-8"))
    mismatches: list[str] = []

    for item in vectors:
        vector_id = str(item.get("id", "<missing-id>"))
        if item.get("expected_error"):
            try:
                ns8_A(item["family"], int(item["r"]), int(item["c"]), int(item["k"]), int(item.get("N", 8)))
                mismatches.append(f"{vector_id}: expected InvalidInput but computation succeeded")
            except InvalidInput:
                pass
            continue

        try:
            seed_family, r_prime, c_prime, expected_a = _recomputed_expectations(item)
        except InvalidInput as exc:
            mismatches.append(f"{vector_id}: valid vector became invalid ({exc})")
            continue

        if item.get("expected_seed_family") != seed_family:
            mismatches.append(
                f"{vector_id}: expected_seed_family={item.get('expected_seed_family')} recomputed={seed_family}"
            )
        if int(item.get("expected_r_prime")) != r_prime:
            mismatches.append(f"{vector_id}: expected_r_prime={item.get('expected_r_prime')} recomputed={r_prime}")
        if int(item.get("expected_c_prime")) != c_prime:
            mismatches.append(f"{vector_id}: expected_c_prime={item.get('expected_c_prime')} recomputed={c_prime}")
        if int(item.get("expected_A")) != expected_a:
            mismatches.append(f"{vector_id}: expected_A={item.get('expected_A')} recomputed={expected_a}")
    return mismatches


def regenerate_vectors(in_path: Path, out_path: Path) -> None:
    vectors = json.loads(in_path.read_text(encoding="utf-8"))
    updated = []

    for vector in vectors:
        item = dict(vector)
        if item.get("expected_error"):
            # Invalid vectors intentionally preserve expected_error contract.
            updated.append(item)
            continue

        try:
            seed_family, r_prime, c_prime, a_val = _recomputed_expectations(item)
        except InvalidInput as exc:
            raise RuntimeError(f"Valid vector became invalid: {item.get('id')} ({exc})") from exc

        item["expected_seed_family"] = seed_family
        item["expected_r_prime"] = r_prime
        item["expected_c_prime"] = c_prime
        item["expected_A"] = a_val
        updated.append(item)

    out_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate NS8 vector expected fields.")
    parser.add_argument("--check", action="store_true", help="Verify vectors against oracle without modifying files.")
    parser.add_argument(
        "--authorize",
        action="store_true",
        help="Allow vector regeneration only when spec/changelog/phase-plan authorization checks pass.",
    )
    parser.add_argument("--in", dest="in_file", default="vectors/ns8_test_vectors.json")
    parser.add_argument("--out", dest="out_file", default="vectors/ns8_test_vectors.json")
    args = parser.parse_args()

    in_path = Path(args.in_file)
    out_path = Path(args.out_file)
    if args.check:
        mismatches = check_vectors(in_path)
        if mismatches:
            details = "\n".join(mismatches[:50])
            raise SystemExit(f"Vector drift detected ({len(mismatches)} mismatch(es)):\n{details}")
        print(f"Vector check passed: {in_path}")
        return

    if not args.authorize:
        raise SystemExit("Refusing to regenerate vectors without --authorize. Use --check for CI stability validation.")
    spec_version = _assert_regen_authorized(SPEC_PATH, CHANGE_LOG_PATH, PHASE_PLAN_PATH)
    regenerate_vectors(in_path, out_path)
    print(f"Regenerated vectors for spec_version {spec_version}: {out_path}")


if __name__ == "__main__":
    main()
