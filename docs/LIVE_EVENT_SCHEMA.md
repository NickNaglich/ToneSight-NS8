# Live Event Schema (Shadow Mode)

This document defines the canonical `LiveEvent` envelope for 0.1.5 shadow-mode ingestion.

Authoritative artifact:
- `schemas/live_event.schema.json`

Validator tool:
- `python tools/validate_live_event.py <path-to-jsonl>`

## Required fields

- `event_id`: stable event identifier (non-empty string; must be deterministic per upstream event)
- `source`: emitting system identifier (non-empty string)
- `timestamp_received`: ISO-8601 timestamp recorded at ingest boundary
- `meta`: object containing pseudonymous operational metadata
- `privacy_flags`: object containing privacy handling flags

## Optional fields

- `timestamp_emitted`: upstream emit timestamp (ISO-8601)
- `text`: raw content payload (non-empty string)
- `segments`: array alternative to `text`; each segment requires:
  - `id`
  - `text`
  - optional `start_sec`, `end_sec`
- `upstream_vad`: optional upstream VAD estimate (`V/A/D` in `1..8`)
- `upstream_label`: optional upstream label string

Constraint:
- at least one of `text` or `segments` must be present.

## Pseudonymous metadata (`meta`)

Recommended keys:
- `session_id`
- `agent_id`
- `user_id`
- `tenant_id`

Coding-agent optional keys (for pinned identity telemetry):
- `provider` (for example `ollama`)
- `model_tag` (human-facing model tag)
- `model_digest` (preferred immutable identity)
- `model_version` (fallback immutable identity when digest unavailable)
- `generation_settings` (object; deterministic config identity such as `temperature`, `top_p`, `seed`)
- `expected_language` (for deterministic language-mismatch telemetry)
- `tool_calls` (integer or list for deterministic tool-call counting)

Identifier keys are expected to be pseudonymous for operational grouping only.
Coding-agent keys are deterministic telemetry metadata, not prompt/response content.

## Privacy flags (`privacy_flags`)

Required keys:
- `contains_pii` (`bool`)
- `allow_store_raw` (`bool`)

These flags allow deterministic shadow-mode handling policies (`fail`, `drop`, `quarantine`) in later phases.

## Validation error shape

`tools/validate_live_event.py` returns deterministic JSON errors:

```json
{
  "valid": false,
  "error": {
    "code": "missing_required",
    "message": "row 1: missing required field 'event_id'"
  }
}
```

Success output:

```json
{"valid": true, "path": "tests/fixtures/live_event.valid.jsonl"}
```
