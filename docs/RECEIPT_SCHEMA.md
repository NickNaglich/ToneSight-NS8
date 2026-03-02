# Receipt Schema (v1)

This document freezes the normative receipt shape for ToneSight NS8 wrapper APIs.

Status:
- v1 contract draft (normative for wrapper API implementation).

## Required fields

- `spec_version`: string
- `input`: object
- `route`: object
- `output`: object

## Receipt example

```json
{
  "spec_version": "1.0",
  "input": {
    "family": "TRF",
    "r": 6,
    "c": 4,
    "k": 3,
    "label": "empathetic",
    "vad": { "V": 7, "A": 3, "D": 3 }
  },
  "route": {
    "seed_family": "TLF",
    "r_prime": 6,
    "c_prime": 5
  },
  "output": {
    "A": 2
  }
}
```

## Notes

- `label` and `vad` are optional based on entrypoint:
  - `tonesight_receipt_from_label_context(...)`: include both `label` and resolved `vad`
  - `tonesight_receipt_from_vad_context(...)`: include `vad`; omit `label` if not provided
- Anchor semantics:
  - `output.A` is derived from NS8 routing inputs (`family`, `r`, `c`, `k`).
  - `input.vad` and `input.label` are contextual receipt fields and do not directly alter NS8 anchor math.
  - With fixed `family/r/c/k`, anchor can remain constant even when VAD varies.
- Backward-compatible aliases `tonesight_from_label(...)` and `tonesight_from_vad(...)` remain available but are deprecated.
- `spec_version` must match `docs/SPEC_NS8.md`.
- `A` must be in `1..8`.
- Unknown optional fields are allowed only if they do not alter deterministic behavior.
- Operational eval/live receipts include additive `receipt_schema_version` for artifact contract versioning.
- Operational eval/live summaries include additive `summary_schema_version` for summary contract versioning.
- Operational eval/live receipts may include additive provenance fields (for example `code_revision`) when available; absence remains backward-compatible.

## Signal-Layer Additive Fields (v0.2.6)

Signal-layer receipts may include additive deterministic fields:
- `mapping_profile`
- `mapping_profile_hash`
- `domain_pack`
- `domain_pack_hash`
- `quarantine_count_total`
- `quarantine_counts_by_reason`
- `quarantine_artifact_path`
- `quarantine_artifact_hash`

These fields are additive and must not break existing receipt consumers.
