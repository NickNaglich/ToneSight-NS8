# Identity And Hashing (Live Shadow Mode)

This document defines deterministic identity rules for live-event processing.

## Stable Event Hash

Function:
- `tonesight_ns8.live_identity.stable_event_hash(event)`

Rule:
- hash input is canonical JSON of the event with keys sorted and compact separators
- `timestamp_received` is excluded from stable hash input as a volatile ingest-time field

Implication:
- two otherwise identical events with different `timestamp_received` values produce the same stable hash

## Canonicalization

Function:
- `tonesight_ns8.live_identity.canonical_live_event(event)`

Current volatile exclusion set:
- `timestamp_received`

Future changes to volatile field policy must be versioned and documented to preserve replay and forensics consistency.

## Shadow Strictness Modes

Function:
- `tonesight_ns8.live_shadow_policy.apply_shadow_policy(...)`

Modes:
- `fail`: raise immediately on first invalid event
- `drop`: keep valid events, skip invalid events, record counts
- `quarantine`: keep valid events and write invalid events as deterministic JSONL receipts

Quarantine artifact:
- default path: `runs/live_quarantine/quarantine.jsonl`
- each row should include event payload plus deterministic error object (`code`, `message`)

