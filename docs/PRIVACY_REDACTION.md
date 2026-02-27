# Privacy Redaction (Deterministic)

ToneSight live replay includes a deterministic redaction stage for textual fields before replay artifacts are written.

Scope:
- live event `text`
- live event `segments[].text`

Current token rules:
- `EMAIL` -> `[EMAIL]`
- `PHONE` -> `[PHONE]`
- `SSN` -> `[SSN]`

Determinism guarantees:
- rule order is fixed and documented
- replacement tokens are fixed literals
- same input text always yields the same redacted output and count summary

Operational behavior:
- redaction is enabled by default for `live-replay` and `live-verify`
- disable only for internal debugging with `--disable-redaction`
- for coding-agent telemetry (`--adapter coding_agent`), prefer metadata-only retention:
  - keep model/generation identity in `meta`
  - avoid storing raw prompt/response payloads unless explicitly required

Artifacts/receipts:
- `eval_summary.json` includes `redaction_summary`
- `receipt.json` includes `redaction_summary`

Limitations:
- this is a bounded heuristic layer, not a full PII-classification engine
- users should treat this as a deterministic safeguard, not a legal compliance guarantee

## UI Exposure Boundary (v0.2.6)

Default UI exposure policy:
- UI surfaces derived artifacts only (summaries, reports, receipts, compare/gate outputs).
- UI does not read raw capture files by default.
- UI may display restricted artifact class labels as non-clickable safety items.

Disallowed-by-default artifact classes for UI:
- `runs/captures/<capture_id>/events.raw.jsonl`
- `runs/<run_live_id>/quarantine.jsonl`

Reference allowlist:
- `docs/UI_ALLOWED_CONTRACTS.md`
- `ui/src/contracts.ts`
