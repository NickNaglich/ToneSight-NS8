# Evaluation & Reporting

This document describes the implemented deterministic eval workflow.

Conformance vs evidence:
- eval/compare/gate artifacts in this document are conformance telemetry.
- benchmark artifacts (`benchmark --suite core`) are empirical evidence outputs.
- use `docs/WHY_NS8.md` for claim-to-artifact mapping.

## Goldset Contract

File:
- `data/goldset.jsonl`

Each row is JSON with:
- `id` (optional but recommended)
- `target_vad`: object with `V/A/D` integers in `1..8` (required)
- `label` (optional)
- `gold_vad`: object with `V/A/D` integers in `1..8` (optional)

Example:

```json
{"id":"a_001","label":"empathetic","target_vad":{"V":7,"A":3,"D":3},"gold_vad":{"V":7,"A":3,"D":3}}
```

Current reference distribution:
- row count: `250`
- labels: `14`
- key strata tags: `boundary` (80), `hard_negative` (80), `mismatch` (110), `confusion_pair` (130), `structured_strata` (130)

Eval behavior:
- if `label` is present, prediction uses taxonomy label mapping (or calibration override when configured)
- else if `gold_vad` is present, prediction uses `gold_vad`
- else prediction falls back to `target_vad`

Conformance interpretation:
- this eval is a deterministic conformance check against target bins
- intentional negative-anchor rows are included to test failure surfacing and regression behavior
- `pass_rate` should not be interpreted as classifier accuracy
- this workflow standardizes VAD-based affect telemetry; it is not psychological inference
- run-to-run compare artifacts are intended to surface affective drift in system outputs over time

## Run Commands

CLI eval:

```bash
python -m tonesight_ns8.cli eval
python -m tonesight_ns8.cli eval --goldset data/goldset.jsonl --out-root runs --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3
```

CLI eval-compare:

```bash
python -m tonesight_ns8.cli eval-compare
python -m tonesight_ns8.cli eval-compare --goldset data/goldset.jsonl --out-root runs --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --top-n 10
```

CLI benchmark suite:

```bash
python -m tonesight_ns8.cli benchmark --suite core
python -m tonesight_ns8.cli benchmark --suite core --out-root runs --goldset data/goldset.jsonl
```

Optional observability API trigger:

```http
POST /eval/run
Content-Type: application/json
{
  "goldset_path": "data/goldset.jsonl",
  "out_root": "runs",
  "taxonomy_path": "taxonomy/tone_taxonomy.v1.json",
  "threshold_l1": 3,
  "calibration_path": null,
  "capture_gpu": false,
  "mlflow_tracking_uri": null
}
```

## Eval Artifacts

Always written:
- `runs/<run_id>/out.jsonl`
- `runs/<run_id>/eval_summary.json`
- `runs/<run_id>/report.html`
- `runs/<run_id>/receipt.json`

Optional (when `capture_gpu=true`):
- `runs/<run_id>/gpu_before.json`
- `runs/<run_id>/gpu_after.json`

Benchmark artifacts (`benchmark --suite core`):
- `runs/benchmarks/core/noise_tolerance.json`
- `runs/benchmarks/core/drift_injection.json`
- `runs/benchmarks/core/model_swap_robustness.json`
- `runs/benchmarks/core/baselines.json`
- `runs/benchmarks/core/transition_coherence.json`
- `runs/benchmarks/core/report.json`

Performance smoke policy:
- deterministic eval smoke is covered by `tests/test_eval_performance_smoke.py`
- conservative runtime threshold: eval on `data/goldset.jsonl` should complete in `< 30s`
- benchmark workflow remains non-blocking initially (`.github/workflows/benchmarks.yml`)

## `eval_summary.json` Fields

- `run_id`
- `count_rows`
- `threshold_l1`
- `pass_count`, `fail_count`
- `pass_rate`, `fail_rate`
- `avg_l1`, `median_l1`, `p95_l1`, `max_l1`
- `count_with_gold_vad`, `count_without_gold_vad`
- `avg_accuracy_l1` (`null` when no `gold_vad` rows are present)

## `out.jsonl` Per-Row Explainability Fields

Each scored row includes deterministic explainability values:
- `delta_v`: absolute `|pred_vad.V - target_vad.V|`
- `delta_a`: absolute `|pred_vad.A - target_vad.A|`
- `delta_d`: absolute `|pred_vad.D - target_vad.D|`
- `compliance_l1`: equals `delta_v + delta_a + delta_d`
- `threshold_margin`: `threshold_l1 - compliance_l1` (negative means threshold violation)

## Compare Output

`compare` and `eval-compare` produce:
- core deltas: `delta_pass_rate`, `delta_avg_l1`, `delta_p95_l1`
- trend labels: `pass_rate_trend`, `avg_l1_trend`, `p95_l1_trend`
- row coverage: `count_common_ids`, `count_only_in_a`, `count_only_in_b`
- per-label deltas (`per_label_delta`) when labels are available
- regression coverage:
  - `regression_count_total`
  - `top_n_requested`
  - `top_n_returned`
  - `truncated`
- `top_regressions`: deterministic sort by `delta_l1` descending, then `id`
  - includes per-dimension changes `delta_v`, `delta_a`, `delta_d` when available
- eval-compare compatibility gate:
  - compares only against prior runs matching compatibility identity fields:
    - `dataset_hash`
    - `spec_version`
    - `mapping_id`
    - `mapping_version`
    - `taxonomy_identity` (`taxonomy_hash` with path fallback)
    - `calibration_identity`
    - `defaults_schema_version`
  - exposes `incompatible_previous_runs` and `compare_skipped_reason` in payload

Optional compare artifact (`--write`):
- `runs/<runB>/comparisons/<runA>/compare_summary.json`
- `runs/<runB>/comparisons/<runA>/compare_report.html`

Distance mode:
- default `--distance l1` uses `compliance_l1` delta ranking
- optional `--distance topology` uses NS8 anchor ring distance between `pred_vad` and `target_vad` (fallback to `compliance_l1` when anchor inputs are missing)
- compare output includes `distance_mode` and per-regression `distance_a`, `distance_b`, `delta_distance`

Compare error contract:
- compare fails with deterministic actionable errors for:
  - missing required files: `missing_required_file:<name>`
  - malformed JSON artifacts: `malformed_json:<name>:line=<n>:col=<m>`
  - malformed JSONL rows: `malformed_jsonl:<name>:line=<n>:col=<m>`
  - incompatible receipts: `incompatible_receipts:<field>:<a>!=<b>`
- CLI wraps runner failures as deterministic error payloads:
  - `{"error":{"type":"CompareInputError","message":"..."}}` with exit code `2`

CLI example:

```bash
python -m tonesight_ns8.cli compare runs/<runA> runs/<runB> --distance topology --top-n 10 --write
```

Report presentation preset:
- open `runs/<run_id>/report.html?mode=present` for deterministic camera/control defaults suited for screenshots/demos

## Gate Command (CI/CD)

Use deterministic gate checks against run-to-run compare deltas:

```bash
python -m tonesight_ns8.cli gate --run-a runs/<baseline> --run-b runs/<candidate>
python -m tonesight_ns8.cli gate --run-a runs/<baseline> --run-b runs/<candidate> --profile support_chat
```

Threshold flags:
- `--min-pass-rate-delta` (default `-0.02`)
- `--max-avg-l1-delta` (default `0.2`)
- `--max-p95-l1-delta` (default `0.2`)
- `--profile <name>` (loads thresholds from `config/gate_profiles.json`)

Exit codes:
- `0`: gate passed
- `2`: regression threshold violated
- `3`: incompatible runs (`dataset_hash`/`spec_version` mismatch)

Compatibility gates include:
- `spec_version`
- `mapping_id`
- `mapping_version`
- `taxonomy_identity` (`taxonomy_hash` or taxonomy path fallback)
- `calibration_identity`
- `defaults_schema_version`
- optional `dataset_hash` gate (disable via `--allow-dataset-mismatch` for live non-goldset comparisons)

## Triage Command (Data QA)

Export deterministic triage rows for reviewer prioritization:

```bash
python -m tonesight_ns8.cli triage --run-b runs/<candidate> --top-n 50 --format jsonl
python -m tonesight_ns8.cli triage --run-a runs/<baseline> --run-b runs/<candidate> --top-n 50 --format csv
```

Behavior:
- single-run mode: triage from one run (`--run-b`)
- diff mode: triage from baseline/candidate pair (`--run-a` + `--run-b`)
- deterministic ranking by `--score` (default `compliance_l1`), then `id`
- exports `jsonl` or `csv`
- rationale fields include `delta_v`, `delta_a`, `delta_d`, `threshold_margin`, `label`, `tags`

## Trend Command (Run History)

Aggregate deterministic run-over-run metrics from artifact history:

```bash
python -m tonesight_ns8.cli trend --out-root runs
python -m tonesight_ns8.cli trend --out-root runs --group-by source
```

Behavior:
- discovers compatible run artifacts in `out-root` and emits `trend_summary.json`
- run list is deterministically ordered by `run_id`
- computes deltas vs previous compatible run for `pass_rate`, `avg_l1`, `p95_l1`
- optional grouping by row metadata field (`source`, `agent`, `prompt_id`, etc.) with per-group `count`, `avg_l1`, `fail_rate`

## Run Index Command (Phase 21)

Build deterministic run metadata index with one JSONL row per discovered run:

```bash
python -m tonesight_ns8.cli index-runs --out-root runs
python -m tonesight_ns8.cli index-runs --out-root runs --out runs/index.jsonl
```

Behavior:
- discovers run directories containing `receipt.json`, `eval_summary.json`, and `out.jsonl`
- deterministic ordering by `run_id`
- stable schema with:
  - run IDs and version/hash metadata
  - profile/source labels (`profile_label`, `source_label`, `source_labels`)
  - artifact pointers (`out_jsonl`, `eval_summary_json`, `report_html`, `receipt_json`)
- idempotent output for unchanged run sets

## Live Shadow Harness (Phase 17)

Deterministic capture/replay/verify flow for live-shaped events:

```bash
python -m tonesight_ns8.cli live-capture --events tests/fixtures/live_capture.small.jsonl --out-root runs
python -m tonesight_ns8.cli live-replay --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --shadow-strict quarantine
python -m tonesight_ns8.cli live-verify --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --shadow-strict quarantine
```

Behavior:
- `live-capture`: validates LiveEvent envelope and writes deterministic capture artifacts
- `live-replay`: maps upstream signal (`upstream_vad` or `upstream_label`) into standard run artifacts
- `live-verify`: replays the same capture twice and checks hash identity for deterministic artifacts
- `live-replay`/`live-verify` apply deterministic text redaction by default (disable with `--disable-redaction` only for internal debugging)

Live artifacts:
- `runs/captures/<capture_id>/events.raw.jsonl`
- `runs/captures/<capture_id>/capture_manifest.json`
- `runs/<run_live_id>/out.jsonl`
- `runs/<run_live_id>/eval_summary.json`
- `runs/<run_live_id>/report.html`
- `runs/<run_live_id>/receipt.json`
- `runs/<run_live_id>/quarantine.jsonl` (only when quarantine mode receives invalid events)
- replay summaries include `redaction_summary` token counts

## Retention Purge

Deterministic retention cleanup:

```bash
python -m tonesight_ns8.cli purge --out-root runs --older-than-days 30
python -m tonesight_ns8.cli purge --out-root runs --older-than-days 30 --apply
```

Safety defaults:
- dry-run unless `--apply`
- capture directories skipped unless `--include-captures`
- run directories containing `bundles/` skipped unless `--include-bundles`

## Operational Notes

- Determinism: for fixed inputs/config, scoring outputs and artifact schema are deterministic.
- Run metadata (`run_id`, timestamps, artifact paths) is expected to vary per run.
- GPU snapshots are best-effort and should not fail eval on non-GPU systems.
- For live replay, run IDs are deterministic for fixed capture + config, and `live-verify` asserts artifact hash stability.
- Eval replay reproducibility comparison policy:
  - stable targets: `out.jsonl` byte/hash equality and `eval_summary.json` equality excluding variable fields
  - allowed variable fields:
    - `eval_summary.json`: `run_id`, `eval_duration_seconds`
    - `receipt.json`: `run_id`, `created_at_utc`, `runtime.started_at_utc`, `runtime.completed_at_utc`, `runtime.eval_duration_seconds`, artifact paths under `artifacts.*`

Validation command:
- `python tools/validate_goldset.py data/goldset.jsonl`

## Shadow Strictness Modes (Live Pipeline)

When validating live event envelopes in shadow mode, invalid rows follow one of:
- `fail`: stop processing and raise on first invalid event
- `drop`: skip invalid events and continue with valid set
- `quarantine`: continue with valid events and write invalid events to quarantine JSONL with deterministic reason receipts

Identity note:
- stable event hashing excludes `timestamp_received` from hash input to keep replay identity deterministic
- see `docs/IDENTITY_AND_HASHING.md`
