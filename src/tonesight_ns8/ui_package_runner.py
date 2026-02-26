"""Deterministic static UI demo package generator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from .run_index import run_index, run_index_json

_FIXED_ZIP_TIME = (2020, 1, 1, 0, 0, 0)
_SAFE_RUN_FILES = ("receipt.json", "eval_summary.json", "report.html")
_SAFE_COMPARE_FILES = ("compare_summary.json", "compare_report.html", "gate_result.json")
_RAW_RUN_FILES = ("out.jsonl", "events.raw.jsonl", "quarantine.jsonl")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _is_run_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    return (path / "receipt.json").exists() and (path / "eval_summary.json").exists()


def _iter_files_sorted(path: Path) -> list[Path]:
    return sorted((p for p in path.rglob("*") if p.is_file()), key=lambda p: p.as_posix())


def _ui_server_files() -> list[tuple[str, Path]]:
    root = _repo_root()
    pairs: list[tuple[str, Path]] = []
    for rel in ("ui", "server"):
        source = root / rel
        if not source.exists():
            continue
        for file_path in _iter_files_sorted(source):
            if "__pycache__" in file_path.parts:
                continue
            archive_path = file_path.relative_to(root).as_posix()
            pairs.append((archive_path, file_path))
    return pairs


def _run_artifact_files(out_root: Path, *, include_raw_artifacts: bool) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    for index_name in ("index.jsonl", "index.json"):
        index_path = out_root / index_name
        if index_path.exists():
            pairs.append((f"runs/{index_name}", index_path))

    run_dirs = sorted((p for p in out_root.iterdir() if _is_run_dir(p)), key=lambda p: p.name)
    for run_dir in run_dirs:
        for file_name in _SAFE_RUN_FILES:
            file_path = run_dir / file_name
            if file_path.exists():
                pairs.append((f"runs/{run_dir.name}/{file_name}", file_path))

        reports_dir = run_dir / "reports"
        if reports_dir.exists():
            for report_path in sorted(reports_dir.glob("report_*.json"), key=lambda p: p.name):
                pairs.append((f"runs/{run_dir.name}/reports/{report_path.name}", report_path))

        comparisons_dir = run_dir / "comparisons"
        if comparisons_dir.exists():
            for baseline_dir in sorted((p for p in comparisons_dir.iterdir() if p.is_dir()), key=lambda p: p.name):
                for file_name in _SAFE_COMPARE_FILES:
                    file_path = baseline_dir / file_name
                    if file_path.exists():
                        pairs.append((f"runs/{run_dir.name}/comparisons/{baseline_dir.name}/{file_name}", file_path))

        if include_raw_artifacts:
            for file_name in _RAW_RUN_FILES:
                file_path = run_dir / file_name
                if file_path.exists():
                    pairs.append((f"runs/{run_dir.name}/{file_name}", file_path))

    return pairs


def _zip_write_file(zipf: ZipFile, *, archive_path: str, source_path: Path) -> None:
    info = ZipInfo(filename=archive_path, date_time=_FIXED_ZIP_TIME)
    info.compress_type = ZIP_STORED
    info.external_attr = 0o644 << 16
    zipf.writestr(info, source_path.read_bytes())


def _zip_write_json(zipf: ZipFile, *, archive_path: str, payload: dict[str, Any]) -> None:
    info = ZipInfo(filename=archive_path, date_time=_FIXED_ZIP_TIME)
    info.compress_type = ZIP_STORED
    info.external_attr = 0o644 << 16
    body = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    zipf.writestr(info, body.encode("utf-8"))


def run_ui_package(
    out_root: str,
    *,
    out_path: str | None = None,
    include_source_paths: bool = False,
    include_raw_artifacts: bool = False,
) -> dict[str, Any]:
    """Create deterministic ZIP package for local read-only UI demos."""
    out_root_path = Path(out_root)
    if not out_root_path.exists():
        raise FileNotFoundError(f"Missing runs root: {out_root_path}")

    if not (out_root_path / "index.jsonl").exists():
        run_index(str(out_root_path))
    if not (out_root_path / "index.json").exists():
        run_index_json(str(out_root_path))

    package_path = Path(out_path) if out_path else (out_root_path / "ui_demo_package.zip")
    package_path.parent.mkdir(parents=True, exist_ok=True)

    file_pairs = _ui_server_files() + _run_artifact_files(out_root_path, include_raw_artifacts=include_raw_artifacts)
    file_pairs = sorted(file_pairs, key=lambda row: row[0])

    manifest_files: list[dict[str, Any]] = []
    with ZipFile(package_path, mode="w", compression=ZIP_STORED) as zipf:
        for archive_path, source_path in file_pairs:
            _zip_write_file(zipf, archive_path=archive_path, source_path=source_path)
            manifest_row: dict[str, Any] = {
                "archive_path": archive_path,
                "size_bytes": source_path.stat().st_size,
                "sha256": _sha256(source_path),
            }
            if include_source_paths:
                manifest_row["source_path"] = str(source_path)
            manifest_files.append(manifest_row)

        manifest = {
            "spec_version": "1.0",
            "bundle_version": "1.0",
            "mode": "ui_demo_static",
            "out_root": str(out_root_path),
            "package_path": str(package_path),
            "include_raw_artifacts": include_raw_artifacts,
            "external_safe": not include_source_paths and not include_raw_artifacts,
            "file_count": len(manifest_files),
            "files": manifest_files,
        }
        _zip_write_json(zipf, archive_path="manifest.json", payload=manifest)

    return {
        "spec_version": "1.0",
        "mode": "ui_demo_static",
        "out_root": str(out_root_path),
        "package_path": str(package_path),
        "file_count": len(manifest_files),
        "include_raw_artifacts": include_raw_artifacts,
        "external_safe": not include_source_paths and not include_raw_artifacts,
        "manifest": manifest,
    }
