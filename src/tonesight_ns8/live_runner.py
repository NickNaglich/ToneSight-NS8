"""Deterministic live capture/replay/verify harness for shadow mode."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from .coding_agent_adapter import (
    CODING_AGENT_ADAPTER_ID,
    CODING_AGENT_ADAPTER_VERSION,
    adapt_coding_agent_event,
)
from .defaults import EVAL_DEFAULTS, _resolve_defaults_path
from .eval_runner import _render_eval_report_html
from .live_identity import canonical_live_event, stable_event_hash
from .live_event_validation import validate_live_event_file
from .provenance import get_code_revision
from .live_shadow_policy import apply_shadow_policy
from .redaction import redact_live_event
from .taxonomy import UnknownToneLabel, get_vad, load_taxonomy

RECEIPT_SCHEMA_VERSION = "1.0"
SUMMARY_SCHEMA_VERSION = "1.0"
_LIVE_CAPTURE_SCHEMA_VERSION = "1.0"
LiveAdapterResolver = Callable[[dict[str, Any], dict[str, Any]], tuple[tuple[int, int, int], dict[str, Any] | None]]


def _resolve_upstream_signal_event(
    event: dict[str, Any],
    taxonomy: dict[str, Any],
) -> tuple[tuple[int, int, int], dict[str, Any] | None]:
    vad = event.get("upstream_vad")
    if isinstance(vad, dict):
        return (int(vad["V"]), int(vad["A"]), int(vad["D"])), None
    label = event.get("upstream_label")
    if isinstance(label, str) and label.strip():
        return get_vad(label, taxonomy), None
    raise ValueError("missing upstream_vad/upstream_label")


def _resolve_coding_agent_event(
    event: dict[str, Any],
    taxonomy: dict[str, Any],
) -> tuple[tuple[int, int, int], dict[str, Any] | None]:
    del taxonomy  # unused; kept for shared resolver signature.
    payload = adapt_coding_agent_event(event)
    vad = payload["vad"]
    return (int(vad["V"]), int(vad["A"]), int(vad["D"])), payload


_LIVE_ADAPTER_REGISTRY: dict[str, LiveAdapterResolver] = {
    "upstream_signal": _resolve_upstream_signal_event,
    CODING_AGENT_ADAPTER_ID: _resolve_coding_agent_event,
}


def list_live_adapters() -> tuple[str, ...]:
    return tuple(sorted(_LIVE_ADAPTER_REGISTRY.keys()))


def register_live_adapter(adapter_id: str, resolver: LiveAdapterResolver) -> None:
    key = str(adapter_id).strip()
    if not key:
        raise ValueError("adapter_id must be non-empty")
    if key in _LIVE_ADAPTER_REGISTRY:
        raise ValueError(f"duplicate live adapter id: {key}")
    _LIVE_ADAPTER_REGISTRY[key] = resolver


def _get_live_adapter(adapter: str) -> LiveAdapterResolver:
    resolver = _LIVE_ADAPTER_REGISTRY.get(adapter)
    if resolver is None:
        available = ", ".join(list_live_adapters())
        raise ValueError(f"unknown live adapter: {adapter} (available: {available})")
    return resolver


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows)
    path.write_text((payload + "\n") if payload else "", encoding="utf-8")


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _defaults_spec_version(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    return str(payload.get("spec_version", ""))


def _capture_hash(events: list[dict[str, Any]]) -> str:
    canonical_rows = [canonical_live_event(row) for row in events]
    encoded = json.dumps(canonical_rows, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _replay_hash(
    *,
    capture_hash: str,
    taxonomy_hash: str,
    defaults_hash: str,
    threshold_l1: int,
    shadow_strict: str,
    adapter: str,
) -> str:
    encoded = (
        f"{capture_hash}|{taxonomy_hash}|{defaults_hash}|{int(threshold_l1)}|{shadow_strict}|{adapter}".encode("utf-8")
    )
    return hashlib.sha256(encoded).hexdigest()


def _load_capture_events(capture: str) -> tuple[Path, str, list[dict[str, Any]], str]:
    capture_path = Path(capture)
    if capture_path.is_dir():
        events_path = capture_path / "events.raw.jsonl"
        if not events_path.exists():
            raise ValueError(f"capture directory missing events.raw.jsonl: {capture_path}")
        capture_id = capture_path.name
    else:
        events_path = capture_path
        capture_id = f"capture_{events_path.stem}"
    validate_live_event_file(events_path)
    events = _read_jsonl(events_path)
    if not events:
        raise ValueError("capture has no events")
    return events_path, capture_id, events, _capture_hash(events)


def _event_meta(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("meta")
    if isinstance(raw, dict):
        return raw
    return {}


def _generation_settings_identity(settings: Any) -> str:
    if not isinstance(settings, dict):
        return ""
    return json.dumps(settings, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _extract_coding_agent_identity(events: list[dict[str, Any]]) -> dict[str, Any]:
    providers: set[str] = set()
    model_tags: set[str] = set()
    model_digests: set[str] = set()
    model_versions: set[str] = set()
    generation_ids: dict[str, dict[str, Any]] = {}

    for event in events:
        meta = _event_meta(event)
        provider = str(meta.get("provider") or event.get("provider") or "ollama").strip()
        if provider:
            providers.add(provider)
        model_tag = str(meta.get("model_tag") or event.get("model") or "").strip()
        if model_tag:
            model_tags.add(model_tag)
        model_digest = str(meta.get("model_digest") or "").strip()
        if model_digest:
            model_digests.add(model_digest)
        model_version = str(meta.get("model_version") or "").strip()
        if model_version:
            model_versions.add(model_version)
        generation = meta.get("generation_settings")
        if isinstance(generation, dict):
            generation_ids[_generation_settings_identity(generation)] = generation

    provider = next(iter(providers)) if len(providers) == 1 else ""
    model_tag = next(iter(model_tags)) if len(model_tags) == 1 else ""
    model_digest = next(iter(model_digests)) if len(model_digests) == 1 else ""
    model_version = next(iter(model_versions)) if len(model_versions) == 1 else ""
    generation_settings = next(iter(generation_ids.values())) if len(generation_ids) == 1 else {}
    return {
        "provider": provider,
        "model_tag": model_tag,
        "model_digest": model_digest,
        "model_version": model_version,
        "generation_settings": generation_settings,
    }


def run_live_capture(
    events_path: str,
    *,
    out_root: str = EVAL_DEFAULTS["out_root"],
) -> dict[str, Any]:
    """Validate and persist a deterministic capture artifact."""
    source_path = Path(events_path)
    validate_live_event_file(source_path)
    events = _read_jsonl(source_path)
    if not events:
        raise ValueError("live-capture input file has no events")
    capture_hash = _capture_hash(events)
    capture_id = f"capture_{capture_hash[:12]}"
    capture_dir = Path(out_root) / "captures" / capture_id
    capture_dir.mkdir(parents=True, exist_ok=True)
    raw_path = capture_dir / "events.raw.jsonl"
    _write_jsonl(raw_path, events)
    manifest = {
        "capture_id": capture_id,
        "capture_hash": capture_hash[:12],
        "event_count": len(events),
        "source_path": str(source_path),
        "artifacts": {
            "events_raw_jsonl": str(raw_path),
            "capture_manifest_json": str(capture_dir / "capture_manifest.json"),
        },
    }
    (capture_dir / "capture_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "capture_id": capture_id,
        "capture_hash": capture_hash[:12],
        "capture_dir": str(capture_dir),
        "event_count": len(events),
        "manifest_path": str(capture_dir / "capture_manifest.json"),
    }


def _pred_vad_for_event(
    event: dict[str, Any],
    taxonomy: dict[str, Any],
    *,
    adapter: str,
) -> tuple[tuple[int, int, int], dict[str, Any] | None]:
    resolver = _get_live_adapter(adapter)
    return resolver(event, taxonomy)


def _require_pinned_identity(identity: dict[str, Any]) -> None:
    missing: list[str] = []
    if not str(identity.get("provider") or "").strip():
        missing.append("provider")
    if not str(identity.get("model_tag") or "").strip():
        missing.append("model_tag")
    model_digest = str(identity.get("model_digest") or "").strip()
    model_version = str(identity.get("model_version") or "").strip()
    if not model_digest and not model_version:
        missing.append("model_digest|model_version")
    if not isinstance(identity.get("generation_settings"), dict) or not identity.get("generation_settings"):
        missing.append("generation_settings")
    if missing:
        raise ValueError(f"pinned model identity missing required fields: {', '.join(missing)}")


def run_live_replay(
    capture: str,
    *,
    out_root: str = EVAL_DEFAULTS["out_root"],
    taxonomy_path: str = EVAL_DEFAULTS["taxonomy_path"],
    threshold_l1: int = EVAL_DEFAULTS["threshold_l1"],
    shadow_strict: str = "quarantine",
    redact: bool = True,
    adapter: str = "upstream_signal",
    require_pinned_model_identity: bool = False,
) -> dict[str, Any]:
    """Replay a live capture into deterministic run artifacts."""
    _get_live_adapter(adapter)
    if require_pinned_model_identity and adapter != CODING_AGENT_ADAPTER_ID:
        raise ValueError("require_pinned_model_identity is only supported with adapter='coding_agent'")

    events_path, capture_id, events, capture_hash = _load_capture_events(capture)
    taxonomy = load_taxonomy(taxonomy_path)
    taxonomy_hash = _file_hash(Path(taxonomy_path))
    defaults_path = _resolve_defaults_path()
    defaults_hash = _file_hash(defaults_path)
    defaults_spec_version = _defaults_spec_version(defaults_path)
    run_hash = _replay_hash(
        capture_hash=capture_hash,
        taxonomy_hash=taxonomy_hash,
        defaults_hash=defaults_hash,
        threshold_l1=threshold_l1,
        shadow_strict=shadow_strict,
        adapter=adapter,
    )
    run_id = f"run_live_{run_hash[:12]}"
    out_dir = Path(out_root) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    scored: list[dict[str, Any]] = []
    invalid_events: list[dict[str, Any]] = []
    valid_events: list[dict[str, Any]] = []
    redaction_summary = {"EMAIL": 0, "PHONE": 0, "SSN": 0}

    for event in events:
        working_event = dict(event)
        if redact:
            working_event, counts = redact_live_event(working_event)
            for key, value in counts.items():
                redaction_summary[key] += int(value)

        try:
            pred_vad, adapter_payload = _pred_vad_for_event(working_event, taxonomy, adapter=adapter)
        except (ValueError, KeyError, TypeError, UnknownToneLabel) as exc:
            invalid_events.append(
                {
                    "event_id": working_event.get("event_id"),
                    "event_hash": stable_event_hash(working_event),
                    "error": {"code": "missing_upstream_signal", "message": str(exc)},
                    "event": working_event,
                }
            )
            continue

        valid_events.append(working_event)
        text = working_event.get("text")
        if text is None and working_event.get("segments"):
            text = " ".join(str(seg.get("text", "")).strip() for seg in working_event["segments"]).strip()
        scored.append(
            {
                "id": working_event.get("event_id"),
                "label": working_event.get("upstream_label"),
                "source": working_event.get("source"),
                "agent": (working_event.get("meta") or {}).get("agent_id"),
                "timestamp": working_event.get("timestamp_emitted") or working_event.get("timestamp_received"),
                "text": text,
                "tags": ["live_replay", "shadow_mode"],
                "target_vad": {"V": pred_vad[0], "A": pred_vad[1], "D": pred_vad[2]},
                "pred_vad": {"V": pred_vad[0], "A": pred_vad[1], "D": pred_vad[2]},
                "gold_vad": None,
                "delta_v": 0,
                "delta_a": 0,
                "delta_d": 0,
                "compliance_l1": 0,
                "threshold_margin": int(threshold_l1),
                "accuracy_l1": None,
                "pass": True,  # nosec B105
                "event_hash": stable_event_hash(working_event),
                "capture_id": capture_id,
            }
        )
        if adapter_payload is not None:
            scored[-1]["adapter_id"] = adapter_payload["adapter_id"]
            scored[-1]["adapter_version"] = adapter_payload["adapter_version"]
            scored[-1]["coding_agent_features"] = adapter_payload["features"]
            scored[-1]["coding_agent_bins"] = adapter_payload["bins"]

    policy = apply_shadow_policy(
        mode=shadow_strict,
        valid_events=valid_events,
        invalid_events=invalid_events,
        quarantine_path=str(out_dir / "quarantine.jsonl"),
    )

    total = len(scored)
    summary = {
        "summary_schema_version": SUMMARY_SCHEMA_VERSION,
        "run_id": run_id,
        "capture_id": capture_id,
        "capture_hash": capture_hash[:12],
        "count_rows": total,
        "threshold_l1": int(threshold_l1),
        "pass_count": total,
        "fail_count": 0,
        "pass_rate": 1.0 if total else 0.0,
        "fail_rate": 0.0 if total else 0.0,
        "avg_l1": 0.0,
        "median_l1": 0.0,
        "p95_l1": 0.0,
        "max_l1": 0.0,
        "count_with_gold_vad": 0,
        "count_without_gold_vad": total,
        "avg_accuracy_l1": None,
        "eval_duration_seconds": 0.0,
        "accepted_count": policy["accepted_count"],
        "invalid_count": policy["invalid_count"],
        "quarantined_count": policy["quarantined_count"],
        "shadow_mode": policy["mode"],
        "redaction_summary": redaction_summary,
    }

    receipt = {
        "receipt_schema_version": RECEIPT_SCHEMA_VERSION,
        "spec_version": "1.0",
        "run_id": run_id,
        "capture_path": str(events_path),
        "capture_id": capture_id,
        "capture_hash": capture_hash[:12],
        "taxonomy_hash": taxonomy_hash,
        "defaults_hash": defaults_hash,
        "defaults_spec_version": defaults_spec_version,
        "mapping_id": "ns8",
        "mapping_version": "1.0",
        "capture_schema_version": _LIVE_CAPTURE_SCHEMA_VERSION,
        "row_count": total,
        "config": {
            "threshold_l1": int(threshold_l1),
            "taxonomy_path": taxonomy_path,
            "shadow_strict": policy["mode"],
            "source_mode": "live_replay",
            "redact": redact,
            "adapter": adapter,
            "mapping_id": "ns8",
            "mapping_version": "1.0",
            "defaults_spec_version": defaults_spec_version,
            "calibration_path": "",
        },
        "artifacts": {
            "out_jsonl": str(out_dir / "out.jsonl"),
            "eval_summary_json": str(out_dir / "eval_summary.json"),
            "report_html": str(out_dir / "report.html"),
            "receipt_json": str(out_dir / "receipt.json"),
        },
    }
    code_revision = get_code_revision()
    if code_revision is not None:
        receipt["code_revision"] = code_revision
    if policy["quarantine_path"]:
        receipt["artifacts"]["quarantine_jsonl"] = policy["quarantine_path"]
    receipt["redaction_summary"] = redaction_summary
    if adapter == CODING_AGENT_ADAPTER_ID:
        identity = _extract_coding_agent_identity(valid_events)
        if require_pinned_model_identity:
            _require_pinned_identity(identity)
        receipt["adapter_id"] = CODING_AGENT_ADAPTER_ID
        receipt["adapter_version"] = CODING_AGENT_ADAPTER_VERSION
        receipt["provider"] = identity["provider"]
        receipt["model_tag"] = identity["model_tag"]
        receipt["model_digest"] = identity["model_digest"]
        receipt["model_version"] = identity["model_version"]
        receipt["generation_settings"] = identity["generation_settings"]
        receipt["config"]["provider"] = identity["provider"]
        receipt["config"]["model_tag"] = identity["model_tag"]
        receipt["config"]["model_digest"] = identity["model_digest"]
        receipt["config"]["model_version"] = identity["model_version"]
        receipt["config"]["generation_settings"] = identity["generation_settings"]
        receipt["config"]["require_pinned_model_identity"] = bool(require_pinned_model_identity)

    _write_jsonl(out_dir / "out.jsonl", scored)
    (out_dir / "eval_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out_dir / "report.html").write_text(
        _render_eval_report_html(summary=summary, scored=scored, threshold_l1=int(threshold_l1)),
        encoding="utf-8",
    )
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    return {
        "run_id": run_id,
        "out_dir": str(out_dir),
        "summary": summary,
        "receipt": receipt,
        "shadow_policy": policy,
    }


def run_live_verify(
    capture: str,
    *,
    out_root: str = EVAL_DEFAULTS["out_root"],
    taxonomy_path: str = EVAL_DEFAULTS["taxonomy_path"],
    threshold_l1: int = EVAL_DEFAULTS["threshold_l1"],
    shadow_strict: str = "quarantine",
    redact: bool = True,
    adapter: str = "upstream_signal",
    require_pinned_model_identity: bool = False,
) -> dict[str, Any]:
    """Replay twice and verify deterministic artifact hashes are identical."""
    first = run_live_replay(
        capture,
        out_root=out_root,
        taxonomy_path=taxonomy_path,
        threshold_l1=threshold_l1,
        shadow_strict=shadow_strict,
        redact=redact,
        adapter=adapter,
        require_pinned_model_identity=require_pinned_model_identity,
    )
    run_dir = Path(first["out_dir"])
    first_hashes = {
        "out_jsonl": _file_hash(run_dir / "out.jsonl"),
        "eval_summary_json": _file_hash(run_dir / "eval_summary.json"),
        "report_html": _file_hash(run_dir / "report.html"),
    }
    quarantine_path = run_dir / "quarantine.jsonl"
    if quarantine_path.exists():
        first_hashes["quarantine_jsonl"] = _file_hash(quarantine_path)

    second = run_live_replay(
        capture,
        out_root=out_root,
        taxonomy_path=taxonomy_path,
        threshold_l1=threshold_l1,
        shadow_strict=shadow_strict,
        redact=redact,
        adapter=adapter,
        require_pinned_model_identity=require_pinned_model_identity,
    )
    second_hashes = {
        "out_jsonl": _file_hash(run_dir / "out.jsonl"),
        "eval_summary_json": _file_hash(run_dir / "eval_summary.json"),
        "report_html": _file_hash(run_dir / "report.html"),
    }
    if quarantine_path.exists():
        second_hashes["quarantine_jsonl"] = _file_hash(quarantine_path)

    mismatched = sorted(
        key for key in first_hashes if first_hashes.get(key) != second_hashes.get(key)
    )
    stable = not mismatched
    return {
        "stable": stable,
        "run_id": first["run_id"],
        "out_dir": first["out_dir"],
        "hashes_first": first_hashes,
        "hashes_second": second_hashes,
        "mismatched_artifacts": mismatched,
        "shadow_policy": second.get("shadow_policy", {}),
        "exit_code": 0 if stable else 2,
    }
