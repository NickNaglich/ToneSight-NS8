# Live Event Schema (Shadow Mode)

This document defines the canonical `LiveEvent` envelope for v1.5 shadow-mode ingestion.

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

All are expected to be pseudonymous identifiers for operational grouping only.

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

