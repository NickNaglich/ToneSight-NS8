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
  - `tonesight_from_label(...)`: include both `label` and resolved `vad`
  - `tonesight_from_vad(...)`: include `vad`; omit `label` if not provided
- `spec_version` must match `docs/SPEC_NS8.md`.
- `A` must be in `1..8`.
- Unknown optional fields are allowed only if they do not alter deterministic behavior.
- Operational eval/live receipts may include additive provenance fields (for example `code_revision`) when available; absence remains backward-compatible.
