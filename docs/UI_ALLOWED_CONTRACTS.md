# UI Allowed Contracts (Read-Only)

This document defines the only artifact contracts the UI is allowed to read in `v0.2.6`.

Boundary:
- UI is a read-only renderer over existing deterministic artifacts.
- UI must not compute new scores, bins, drift metrics, or gate decisions.
- If a value is not present in an existing artifact, UI cannot invent or derive it.
- UI may trigger an explicit operator control-plane action (`POST /api/pipeline/run`) only when the artifact API is started with `--enable-pipeline`.
- Control-plane actions must orchestrate existing deterministic library/CLI flows; they do not authorize UI-side recomputation.

## Allowed Artifact Paths

- `runs/index.json`
- `runs/<run_id>/receipt.json`
- `runs/<run_id>/eval_summary.json`
- `runs/<run_id>/report.html`
- `runs/<run_id>/reports/report_<run_id>.json`
- `runs/<run_b>/comparisons/<run_a>/compare_report.html`
- `runs/<run_b>/reports/report_<run_a>_to_<run_b>.json`
- `runs/<run_b>/comparisons/<run_a>/compare_summary.json`
- `runs/<run_b>/comparisons/<run_a>/gate_result.json` (when present)

### Artifact Exposure Classes (UI)

`Derived artifacts (UI-safe)`:
- `runs/index.json`
- `runs/<run_id>/receipt.json`
- `runs/<run_id>/eval_summary.json`
- `runs/<run_id>/reports/report_<run_id>.json`
- `runs/<run_b>/comparisons/<run_a>/compare_summary.json`
- `runs/<run_b>/comparisons/<run_a>/compare_report.html`
- `runs/<run_b>/comparisons/<run_a>/gate_result.json`
- `runs/<run_id>/report.html` (render/download convenience only)

`Raw artifacts (restricted)`:
- `runs/captures/<capture_id>/events.raw.jsonl`
- `runs/<run_live_id>/quarantine.jsonl`

UI behavior:
- UI may label restricted artifact classes, but must not provide default clickable links.

## Allowed Field Paths

### Index row (`runs/index.json[*]`)

- `run_id`
- `dataset_hash`
- `spec_version`
- `mapping_id`
- `mapping_version`
- `profile_label`
- `source_label`
- `source_labels`
- `signal_layer.mapping_profile`
- `signal_layer.mapping_profile_hash`
- `signal_layer.domain_pack`
- `signal_layer.domain_pack_hash`
- `signal_layer.quarantine_count_total`
- `signal_layer.quarantine_counts_by_reason`
- `artifacts.out_jsonl`
- `artifacts.eval_summary_json`
- `artifacts.anchor_events_jsonl`
- `artifacts.metrics_summary_json`
- `artifacts.report_html`
- `artifacts.receipt_json`
- `artifacts.quarantine_jsonl`

### Receipt (`runs/<run_id>/receipt.json`)

- `run_id`
- `spec_version`
- `dataset_hash`
- `taxonomy_hash`
- `defaults_hash`
- `mapping_id`
- `mapping_version`
- `defaults_spec_version`
- `provider`
- `model_tag`
- `model_digest`
- `model_version`
- `generation_settings`
- `redaction_summary`
- `mapping_profile`
- `mapping_profile_hash`
- `domain_pack`
- `domain_pack_hash`
- `quarantine_count_total`
- `quarantine_counts_by_reason`
- `created_at_utc`
- `code_revision`

### Eval summary (`runs/<run_id>/eval_summary.json`)

- `count_rows`
- `pass_rate`
- `fail_rate`
- `avg_l1`
- `p95_l1`
- `max_l1`
- `pass_count`
- `fail_count`
- `threshold_l1`

### Compare/report/gate artifacts

UI may read and render:
- compatibility status fields
- precomputed delta metrics
- threshold values
- violation reason fields

UI may not recompute these values from row-level artifacts.

## Explicitly Disallowed by Default

- raw capture payloads (`events.raw.jsonl`)
- quarantine/raw logs (`quarantine.jsonl` and similar raw event exports)
- any direct rendering of unredacted raw prompt/response content
- backend "UI convenience" endpoints that compute novel aggregate metrics outside existing deterministic artifact paths

## Enforcement

- UI allowlist constants: `ui/src/contracts.ts`
- Contract policy tests: `tests/test_ui_allowed_contracts.py`
