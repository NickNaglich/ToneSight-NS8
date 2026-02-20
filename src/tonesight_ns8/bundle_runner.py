"""Deterministic run/compare forensics bundle generator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from zipfile import ZIP_STORED, ZipFile, ZipInfo


_FIXED_ZIP_DT = (1980, 1, 1, 0, 0, 0)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _required_run_files(run_path: Path) -> list[tuple[str, Path]]:
    return [
        ("run/receipt.json", run_path / "receipt.json"),
        ("run/eval_summary.json", run_path / "eval_summary.json"),
        ("run/report.html", run_path / "report.html"),
        ("run/out.jsonl", run_path / "out.jsonl"),
    ]


def _optional_compare_files(run_b: Path, run_a: Path | None) -> list[tuple[str, Path]]:
    if run_a is None:
        return []
    compare_root = run_b / "comparisons" / run_a.name
    return [
        ("compare/compare_summary.json", compare_root / "compare_summary.json"),
        ("compare/compare_report.html", compare_root / "compare_report.html"),
    ]


def _default_bundle_path(run_b: Path, run_a: Path | None) -> Path:
    target_dir = run_b / "bundles"
    target_dir.mkdir(parents=True, exist_ok=True)
    if run_a is None:
        return target_dir / "forensics_bundle.zip"
    return target_dir / f"forensics_bundle__vs__{run_a.name}.zip"


def _zip_write_bytes(zipf: ZipFile, archive_name: str, data: bytes) -> None:
    info = ZipInfo(filename=archive_name)
    info.date_time = _FIXED_ZIP_DT
    info.compress_type = ZIP_STORED
    zipf.writestr(info, data)


def run_bundle(
    run_b: str,
    *,
    run_a: str | None = None,
    out_path: str | None = None,
    include_source_paths: bool = False,
) -> dict[str, Any]:
    """Create a deterministic forensics bundle zip from run artifacts."""
    run_b_path = Path(run_b)
    run_a_path = Path(run_a) if run_a else None
    bundle_path = Path(out_path) if out_path else _default_bundle_path(run_b_path, run_a_path)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)

    required_files = _required_run_files(run_b_path)
    optional_compare = _optional_compare_files(run_b_path, run_a_path)
    files: list[tuple[str, Path]] = required_files + optional_compare

    missing = [str(path) for _, path in files if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required bundle artifacts: {', '.join(sorted(missing))}")

    manifest_files: list[dict[str, Any]] = []
    file_payloads: list[tuple[str, bytes]] = []
    for archive_name, src_path in sorted(files, key=lambda item: item[0]):
        data = _read_bytes(src_path)
        file_payloads.append((archive_name, data))
        manifest_files.append(
            {
                "archive_path": archive_name,
                "sha256": _sha256_bytes(data),
                "size_bytes": len(data),
            }
        )
        if include_source_paths:
            manifest_files[-1]["source_path"] = str(src_path)

    manifest = {
        "spec_version": "1.0",
        "bundle_version": "1.0",
        "run_b": str(run_b_path),
        "run_a": str(run_a_path) if run_a_path else None,
        "external_safe": not include_source_paths,
        "file_count": len(manifest_files),
        "files": manifest_files,
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode("utf-8")

    with ZipFile(bundle_path, mode="w", compression=ZIP_STORED) as zipf:
        for archive_name, data in file_payloads:
            _zip_write_bytes(zipf, archive_name, data)
        _zip_write_bytes(zipf, "manifest.json", manifest_bytes)

    return {
        "spec_version": "1.0",
        "bundle_path": str(bundle_path),
        "mode": "run_compare" if run_a_path else "run_only",
        "file_count": len(manifest_files),
        "manifest_path": "manifest.json",
        "external_safe": not include_source_paths,
        "manifest": manifest,
    }
