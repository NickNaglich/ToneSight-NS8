"""Deterministic pre-release check orchestration."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .data_lint_runner import run_data_lint
from .defaults import EVAL_DEFAULTS
from .taxonomy import load_taxonomy


def _repo_root() -> Path:
    # src/tonesight_ns8/release_check_runner.py -> repo root
    return Path(__file__).resolve().parents[2]


def _check_nosec_policy(root: Path) -> tuple[bool, dict[str, Any]]:
    src_root = root / "src"
    allowlist_path = root / "tools" / "nosec_allowlist.json"
    if not allowlist_path.exists():
        return False, {"reason": f"missing allowlist: {allowlist_path}"}

    payload = json.loads(allowlist_path.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    allowlist: set[tuple[str, str]] = set()
    for entry in entries:
        rel = str(entry["path"]).replace("\\", "/")
        line = str(entry["line"]).strip()
        allowlist.add((rel, line))

    nosec_re = re.compile(r"#\s*nosec\b", re.IGNORECASE)
    required_format_re = re.compile(
        r"#\s*nosec(?:\s+B\d+(?:,\s*B\d+)*)?\s*-\s+.+\s+\[ref:\s*#\d+\]\s*$",
        re.IGNORECASE,
    )

    current: set[tuple[str, str]] = set()
    failures: list[str] = []
    for path in sorted(src_root.rglob("*.py")):
        rel = str(path.relative_to(root)).replace("\\", "/")
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not nosec_re.search(line):
                continue
            pair = (rel, line)
            current.add(pair)
            if pair in allowlist:
                continue
            if required_format_re.search(line):
                continue
            failures.append(f"{rel}: unapproved nosec suppression line")

    stale = sorted(allowlist.difference(current))
    for rel, line in stale:
        failures.append(f"{rel}: stale allowlist entry: {line}")

    if failures:
        return False, {"failure_count": len(failures), "failures": sorted(failures)}
    return True, {"entries_scanned": len(current)}


def _check_gate_profiles(path: Path) -> tuple[bool, dict[str, Any]]:
    if not path.exists():
        return False, {"reason": f"missing gate profiles config: {path}"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or len(profiles) == 0:
        return False, {"reason": "profiles must be non-empty object"}

    missing: list[str] = []
    for name in sorted(profiles):
        row = profiles[name]
        if not isinstance(row, dict):
            missing.append(f"{name}: invalid profile object")
            continue
        for key in ("min_pass_rate_delta", "max_avg_l1_delta", "max_p95_l1_delta"):
            if key not in row:
                missing.append(f"{name}: missing {key}")
    if missing:
        return False, {"failure_count": len(missing), "failures": missing}
    return True, {"profile_count": len(profiles)}


def run_release_check(
    *,
    goldset_path: str = "data/goldset.jsonl",
    taxonomy_path: str = EVAL_DEFAULTS["taxonomy_path"],
    gate_profiles_path: str = "config/gate_profiles.json",
    out_path: str | None = None,
) -> dict[str, Any]:
    """Run deterministic pre-release checks and return machine-readable status."""
    root = _repo_root()

    checks: list[dict[str, Any]] = []

    lint = run_data_lint(goldset_path)
    checks.append(
        {
            "name": "dataset_lint",
            "passed": bool(lint.get("passed", False)),
            "details": {
                "dataset_path": goldset_path,
                "violation_count": int(lint.get("violation_count", 0)),
                "violations_by_code": lint.get("violations_by_code", {}),
            },
        }
    )

    try:
        taxonomy = load_taxonomy(taxonomy_path)
        tax_ok = bool(isinstance(taxonomy, dict) and len(taxonomy) > 0)
        checks.append(
            {
                "name": "taxonomy_load",
                "passed": tax_ok,
                "details": {"taxonomy_path": taxonomy_path, "label_count": len(taxonomy) if tax_ok else 0},
            }
        )
    except Exception as exc:
        checks.append(
            {
                "name": "taxonomy_load",
                "passed": False,
                "details": {"taxonomy_path": taxonomy_path, "error": str(exc)},
            }
        )

    try:
        profiles_ok, profile_details = _check_gate_profiles(Path(gate_profiles_path))
        checks.append(
            {
                "name": "gate_profiles_config",
                "passed": profiles_ok,
                "details": {"gate_profiles_path": gate_profiles_path, **profile_details},
            }
        )
    except Exception as exc:
        checks.append(
            {
                "name": "gate_profiles_config",
                "passed": False,
                "details": {"gate_profiles_path": gate_profiles_path, "error": str(exc)},
            }
        )

    try:
        nosec_ok, nosec_details = _check_nosec_policy(root)
        checks.append({"name": "nosec_policy", "passed": nosec_ok, "details": nosec_details})
    except Exception as exc:
        checks.append({"name": "nosec_policy", "passed": False, "details": {"error": str(exc)}})

    failed = [row["name"] for row in checks if not bool(row["passed"])]
    payload: dict[str, Any] = {
        "spec_version": "1.0",
        "release_check_schema_version": "1.0",
        "decision": "passed" if len(failed) == 0 else "failed",
        "check_count": len(checks),
        "failed_count": len(failed),
        "failed_checks": failed,
        "checks": checks,
        "exit_code": 0 if len(failed) == 0 else 2,
    }

    if out_path:
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["release_check_path"] = str(target)

    return payload
