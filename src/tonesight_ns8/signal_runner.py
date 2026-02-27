"""Deterministic multi-domain signal mapping runner for v0.2.6."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .domainpacks import load_mapping_profile, stable_payload_hash, validate_mapping_profile
from .signal_mapping import map_observation_to_ns8

OBSERVATION_SCHEMA_V1 = "ns8.signal.observation.v1"
ANCHOR_EVENT_SCHEMA_V1 = "ns8.signal.anchor_event.v1"
QUARANTINE_EVENT_SCHEMA_V1 = "ns8.signal.quarantine_event.v1"
RECEIPT_SCHEMA_VERSION = "1.0"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed_jsonl:{path.name}:line={i}:col={exc.colno}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"invalid_jsonl_row_object:{path.name}:line={i}")
        rows.append(payload)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    text = "\n".join(json.dumps(row, ensure_ascii=True, sort_keys=True) for row in rows)
    path.write_text((text + "\n") if text else "", encoding="utf-8")


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _ring_distance(a: int, b: int) -> int:
    delta = abs(int(a) - int(b))
    return int(min(delta, 8 - delta))


def _transition_type(distance: int) -> str:
    if distance <= 1:
        return "adjacent"
    if distance >= 3:
        return "jump"
    return "near"


def _quarantine_row(
    *,
    reason_code: str,
    reason_detail: str,
    observation: dict[str, Any],
    mapping_profile: str,
    mapping_profile_hash: str,
    domain_pack: str,
    domain_pack_hash: str,
    run_id: str,
) -> dict[str, Any]:
    return {
        "schema": QUARANTINE_EVENT_SCHEMA_V1,
        "reason_code": reason_code,
        "reason_detail": reason_detail,
        "observation_hash": stable_payload_hash(observation),
        "t": str(observation.get("t", "")),
        "entity_id": str(observation.get("entity_id", "")),
        "mapping_profile": mapping_profile,
        "mapping_profile_hash": mapping_profile_hash,
        "domain_pack": domain_pack,
        "domain_pack_hash": domain_pack_hash,
        "run_id": run_id,
    }


def _anchor_density(events: list[dict[str, Any]]) -> list[list[int]]:
    grid = [[0 for _ in range(8)] for _ in range(8)]
    for row in events:
        i = int(row["anchor"]["i"]) - 1
        j = int(row["anchor"]["j"]) - 1
        grid[i][j] += 1
    return grid


def _transition_matrix(events: list[dict[str, Any]]) -> list[list[int]]:
    matrix = [[0 for _ in range(8)] for _ in range(8)]
    for i in range(1, len(events)):
        a_prev = int(events[i - 1]["anchor"]["A"]) - 1
        a_cur = int(events[i]["anchor"]["A"]) - 1
        matrix[a_prev][a_cur] += 1
    return matrix


def _transition_entropy(matrix: list[list[int]]) -> float:
    total = sum(sum(row) for row in matrix)
    if total <= 0:
        return 0.0
    probs: list[float] = []
    for row in matrix:
        for count in row:
            if count > 0:
                probs.append(count / total)
    entropy = -sum(p * math.log2(p) for p in probs)
    return float(round(entropy, 6))


def _persistence_mean(events: list[dict[str, Any]]) -> float:
    if not events:
        return 0.0
    runs: list[int] = []
    current = 1
    for i in range(1, len(events)):
        if int(events[i]["anchor"]["A"]) == int(events[i - 1]["anchor"]["A"]):
            current += 1
        else:
            runs.append(current)
            current = 1
    runs.append(current)
    return float(round(sum(runs) / len(runs), 6))


def run_signal_pipeline(
    observations_path: str,
    *,
    mapping_profile_path: str,
    out_root: str = "runs",
    domain_pack: str = "custom_v1",
) -> dict[str, Any]:
    """Map signal observations into deterministic NS8 anchor artifacts."""
    observations_file = Path(observations_path)
    profile = load_mapping_profile(mapping_profile_path)
    return run_signal_pipeline_with_profile(
        observations_path=str(observations_file),
        mapping_profile=profile,
        out_root=out_root,
        domain_pack=domain_pack,
    )


def run_signal_pipeline_with_profile(
    observations_path: str,
    *,
    mapping_profile: dict[str, Any],
    out_root: str = "runs",
    domain_pack: str = "custom_v1",
) -> dict[str, Any]:
    """Map signal observations with preloaded deterministic mapping profile."""
    observations_file = Path(observations_path)
    profile = dict(mapping_profile)
    validate_mapping_profile(profile)
    profile_hash = stable_payload_hash(profile)
    domain_pack_hash = hashlib.sha256(domain_pack.encode("utf-8")).hexdigest()[:12]
    dataset_hash = _file_hash(observations_file)
    run_id = f"run_signal_{dataset_hash}_{profile_hash}"
    out_dir = Path(out_root) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    observations = _read_jsonl(observations_file)
    anchor_events: list[dict[str, Any]] = []
    quarantine_rows: list[dict[str, Any]] = []
    distances: list[int] = []
    adjacent_count = 0
    spike_count = 0

    for obs in observations:
        if str(obs.get("schema")) != OBSERVATION_SCHEMA_V1:
            quarantine_rows.append(
                _quarantine_row(
                    reason_code="PROFILE_MISMATCH",
                    reason_detail=f"observation schema mismatch: expected {OBSERVATION_SCHEMA_V1}",
                    observation=obs,
                    mapping_profile=str(profile["name"]),
                    mapping_profile_hash=profile_hash,
                    domain_pack=domain_pack,
                    domain_pack_hash=domain_pack_hash,
                    run_id=run_id,
                )
            )
            continue

        channels = obs.get("channels")
        if not isinstance(channels, dict):
            quarantine_rows.append(
                _quarantine_row(
                    reason_code="MISSING_CHANNEL",
                    reason_detail="channels missing or not object",
                    observation=obs,
                    mapping_profile=str(profile["name"]),
                    mapping_profile_hash=profile_hash,
                    domain_pack=domain_pack,
                    domain_pack_hash=domain_pack_hash,
                    run_id=run_id,
                )
            )
            continue

        missing_required = [
            name
            for name, spec in profile["channels"].items()
            if bool(spec["required"]) and channels.get(name) is None
        ]
        if missing_required:
            quarantine_rows.append(
                _quarantine_row(
                    reason_code="MISSING_CHANNEL",
                    reason_detail=f"missing required channels: {', '.join(sorted(missing_required))}",
                    observation=obs,
                    mapping_profile=str(profile["name"]),
                    mapping_profile_hash=profile_hash,
                    domain_pack=domain_pack,
                    domain_pack_hash=domain_pack_hash,
                    run_id=run_id,
                )
            )
            continue

        out_of_range = False
        for key, value in channels.items():
            if value is None:
                continue
            if not isinstance(value, int) or value < 1 or value > 8:
                out_of_range = True
                break
        if out_of_range:
            quarantine_rows.append(
                _quarantine_row(
                    reason_code="OUT_OF_RANGE",
                    reason_detail="channel value out of range (expected integer in 1..8)",
                    observation=obs,
                    mapping_profile=str(profile["name"]),
                    mapping_profile_hash=profile_hash,
                    domain_pack=domain_pack,
                    domain_pack_hash=domain_pack_hash,
                    run_id=run_id,
                )
            )
            continue

        mapped = map_observation_to_ns8(obs, profile)
        step_distance = 0
        transition_type = "initial"
        if anchor_events:
            prev_a = int(anchor_events[-1]["anchor"]["A"])
            cur_a = int(mapped["A"])
            step_distance = _ring_distance(prev_a, cur_a)
            transition_type = _transition_type(step_distance)
            distances.append(step_distance)
            if step_distance <= 1:
                adjacent_count += 1
            if step_distance >= 3:
                spike_count += 1

        anchor_events.append(
            {
                "schema": ANCHOR_EVENT_SCHEMA_V1,
                "t": str(obs.get("t", "")),
                "entity_id": str(obs.get("entity_id", "")),
                "anchor": {
                    "family": mapped["family"],
                    "i": mapped["r"],
                    "j": mapped["c"],
                    "idx": mapped["idx"],
                    "A": mapped["A"],
                },
                "inputs": {
                    "channels": channels,
                    "mapping_profile": mapped["mapping_profile"],
                    "mapping_profile_hash": mapped["mapping_profile_hash"],
                },
                "derived": {
                    "step_distance": step_distance,
                    "transition_type": transition_type,
                },
            }
        )

    transition_count = max(0, len(anchor_events) - 1)
    transition_matrix = _transition_matrix(anchor_events)
    volatility = float(round((sum(distances) / len(distances)) if distances else 0.0, 6))
    adjacency_ratio = float(round((adjacent_count / transition_count) if transition_count else 0.0, 6))
    spike_rate = float(round((spike_count / transition_count) if transition_count else 0.0, 6))
    persistence = _persistence_mean(anchor_events)
    entropy = _transition_entropy(transition_matrix)
    stability_index = float(round(max(0.0, min(1.0, 1.0 - (volatility / 7.0))), 6))

    metrics_summary = {
        "metrics_schema_version": "1.0",
        "run_id": run_id,
        "count_anchor_events": len(anchor_events),
        "count_quarantine": len(quarantine_rows),
        "volatility_mean_step_distance": volatility,
        "persistence_mean_dwell": persistence,
        "transition_entropy": entropy,
        "adjacency_ratio": adjacency_ratio,
        "spike_rate": spike_rate,
        "stability_index": stability_index,
    }

    density_map = {
        "density_schema_version": "1.0",
        "run_id": run_id,
        "grid_8x8": _anchor_density(anchor_events),
    }
    transition_payload = {
        "transition_schema_version": "1.0",
        "run_id": run_id,
        "matrix_8x8": transition_matrix,
        "transition_count": transition_count,
    }

    anchor_path = out_dir / "anchor_events.jsonl"
    metrics_path = out_dir / "metrics_summary.json"
    transitions_path = out_dir / "transition_matrix.json"
    density_path = out_dir / "density_map.json"
    quarantine_path = out_dir / "quarantine.jsonl"

    _write_jsonl(anchor_path, anchor_events)
    _write_json(metrics_path, metrics_summary)
    _write_json(transitions_path, transition_payload)
    _write_json(density_path, density_map)
    _write_jsonl(quarantine_path, quarantine_rows)

    quarantine_counts_by_reason: dict[str, int] = {}
    for row in quarantine_rows:
        code = str(row["reason_code"])
        quarantine_counts_by_reason[code] = quarantine_counts_by_reason.get(code, 0) + 1

    receipt = {
        "spec_version": "1.0",
        "receipt_schema_version": RECEIPT_SCHEMA_VERSION,
        "run_id": run_id,
        "dataset_path": str(observations_file),
        "dataset_hash": dataset_hash,
        "mapping_profile": str(profile["name"]),
        "mapping_profile_hash": profile_hash,
        "domain_pack": domain_pack,
        "domain_pack_hash": domain_pack_hash,
        "quarantine_count_total": len(quarantine_rows),
        "quarantine_counts_by_reason": quarantine_counts_by_reason,
        "quarantine_artifact_path": str(quarantine_path),
        "quarantine_artifact_hash": _file_hash(quarantine_path),
        "artifacts": {
            "anchor_events_jsonl": str(anchor_path),
            "metrics_summary_json": str(metrics_path),
            "transition_matrix_json": str(transitions_path),
            "density_map_json": str(density_path),
            "quarantine_jsonl": str(quarantine_path),
            "receipt_json": str(out_dir / "receipt.json"),
        },
    }
    receipt_path = out_dir / "receipt.json"
    _write_json(receipt_path, receipt)

    return {
        "run_id": run_id,
        "out_dir": str(out_dir),
        "receipt": receipt,
        "metrics_summary": metrics_summary,
        "artifact_paths": receipt["artifacts"],
    }
