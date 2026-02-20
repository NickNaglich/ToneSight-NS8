# Evaluation & Reporting

This document describes the implemented deterministic eval workflow.

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
  - compares only against prior runs matching both `dataset_hash` and `spec_version`
  - exposes `incompatible_previous_runs` and `compare_skipped_reason` in payload

Optional compare artifact (`--write`):
- `runs/<runB>/comparisons/<runA>/compare_summary.json`
- `runs/<runB>/comparisons/<runA>/compare_report.html`

Report presentation preset:
- open `runs/<run_id>/report.html?mode=present` for deterministic camera/control defaults suited for screenshots/demos

## Gate Command (CI/CD)

Use deterministic gate checks against run-to-run compare deltas:

```bash
python -m tonesight_ns8.cli gate --run-a runs/<baseline> --run-b runs/<candidate>
```

Threshold flags:
- `--min-pass-rate-delta` (default `-0.02`)
- `--max-avg-l1-delta` (default `0.2`)
- `--max-p95-l1-delta` (default `0.2`)

Exit codes:
- `0`: gate passed
- `2`: regression threshold violated
- `3`: incompatible runs (`dataset_hash`/`spec_version` mismatch)

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

## Operational Notes

- Determinism: for fixed inputs/config, scoring outputs and artifact schema are deterministic.
- Run metadata (`run_id`, timestamps, artifact paths) is expected to vary per run.
- GPU snapshots are best-effort and should not fail eval on non-GPU systems.

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
