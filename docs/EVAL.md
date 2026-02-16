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

Eval behavior:
- if `label` is present, prediction uses taxonomy label mapping (or calibration override when configured)
- else if `gold_vad` is present, prediction uses `gold_vad`
- else prediction falls back to `target_vad`

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

Optional compare artifact (`--write`):
- `runs/<runB>/comparisons/<runA>/compare_summary.json`

## Operational Notes

- Determinism: for fixed inputs/config, scoring outputs and artifact schema are deterministic.
- Run metadata (`run_id`, timestamps, artifact paths) is expected to vary per run.
- GPU snapshots are best-effort and should not fail eval on non-GPU systems.
