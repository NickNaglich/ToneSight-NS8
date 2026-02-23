"""Deterministic dataset quality linting for goldset-style JSONL files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

LINT_SCHEMA_VERSION = "1.0"


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _is_int_bin(value: Any) -> bool:
    return isinstance(value, int) and 1 <= int(value) <= 8


def run_data_lint(
    dataset_path: str,
    *,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Lint dataset rows deterministically and return machine-readable summary."""
    path = Path(dataset_path)
    violations: list[dict[str, Any]] = []
    if not path.exists():
        payload: dict[str, Any] = {
            "spec_version": "1.0",
            "lint_schema_version": LINT_SCHEMA_VERSION,
            "dataset_path": str(path),
            "dataset_hash": None,
            "passed": False,
            "row_count_total": 0,
            "row_count_valid": 0,
            "violation_count": 1,
            "violations_by_code": {"missing_file": 1},
            "violations": [
                {
                    "line": 0,
                    "code": "missing_file",
                    "message": f"dataset file not found: {path}",
                }
            ],
            "exit_code": 2,
        }
        return payload

    seen_ids: set[str] = set()
    row_count_total = 0
    valid_line_count = 0
    for line_num, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        row_count_total += 1
        row_has_violation = False

        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            violations.append(
                {
                    "line": line_num,
                    "code": "malformed_json",
                    "message": f"invalid JSON ({exc.msg})",
                }
            )
            continue

        if not isinstance(payload, dict):
            violations.append({"line": line_num, "code": "invalid_row_type", "message": "row must be JSON object"})
            continue

        row_id = payload.get("id")
        if not isinstance(row_id, str) or not row_id.strip():
            row_has_violation = True
            violations.append({"line": line_num, "code": "missing_id", "message": "id must be non-empty string"})
            row_id = None
        else:
            row_id = row_id.strip()
            if row_id in seen_ids:
                row_has_violation = True
                violations.append({"line": line_num, "code": "duplicate_id", "message": f"duplicate id '{row_id}'"})
            else:
                seen_ids.add(row_id)

        target_vad = payload.get("target_vad")
        if not isinstance(target_vad, dict):
            row_has_violation = True
            violations.append(
                {
                    "line": line_num,
                    "code": "invalid_target_vad",
                    "message": "target_vad must be object with V/A/D in 1..8",
                }
            )
        else:
            for key in ("V", "A", "D"):
                if not _is_int_bin(target_vad.get(key)):
                    row_has_violation = True
                    violations.append(
                        {
                            "line": line_num,
                            "code": "invalid_target_vad_bin",
                            "message": f"target_vad.{key} must be int in 1..8",
                        }
                    )

        gold_vad = payload.get("gold_vad")
        if gold_vad is not None:
            if not isinstance(gold_vad, dict):
                row_has_violation = True
                violations.append(
                    {
                        "line": line_num,
                        "code": "invalid_gold_vad",
                        "message": "gold_vad must be object with V/A/D in 1..8 when present",
                    }
                )
            else:
                for key in ("V", "A", "D"):
                    if not _is_int_bin(gold_vad.get(key)):
                        row_has_violation = True
                        violations.append(
                            {
                                "line": line_num,
                                "code": "invalid_gold_vad_bin",
                                "message": f"gold_vad.{key} must be int in 1..8",
                            }
                        )

        tags = payload.get("tags")
        if not isinstance(tags, list) or len(tags) == 0:
            row_has_violation = True
            violations.append(
                {"line": line_num, "code": "invalid_tags", "message": "tags must be non-empty list of strings"}
            )
        else:
            for idx, item in enumerate(tags):
                if not isinstance(item, str) or not item.strip():
                    row_has_violation = True
                    violations.append(
                        {
                            "line": line_num,
                            "code": "invalid_tag_item",
                            "message": f"tags[{idx}] must be non-empty string",
                        }
                    )

        if not row_has_violation:
            valid_line_count += 1

    violations.sort(key=lambda item: (int(item.get("line", 0)), str(item.get("code", "")), str(item.get("message", ""))))
    violations_by_code: dict[str, int] = {}
    for item in violations:
        code = str(item["code"])
        violations_by_code[code] = int(violations_by_code.get(code, 0)) + 1
    violations_by_code = {k: violations_by_code[k] for k in sorted(violations_by_code)}

    output: dict[str, Any] = {
        "spec_version": "1.0",
        "lint_schema_version": LINT_SCHEMA_VERSION,
        "dataset_path": str(path),
        "dataset_hash": _file_hash(path),
        "passed": len(violations) == 0,
        "row_count_total": row_count_total,
        "row_count_valid": valid_line_count,
        "violation_count": len(violations),
        "violations_by_code": violations_by_code,
        "violations": violations,
        "exit_code": 0 if len(violations) == 0 else 2,
    }

    if out_path:
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        output["lint_summary_path"] = str(target)

    return output
