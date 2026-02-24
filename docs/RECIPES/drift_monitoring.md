# Drift Monitoring Recipe

This recipe defines a deterministic baseline/candidate workflow using existing compare/gate commands.

## 1) Create baseline run

```bash
python -m tonesight_ns8.cli eval --goldset data/goldset.jsonl --out-root runs --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3
```

Record baseline path:
- `runs/<baseline_run_id>`

## 2) Create candidate run

```bash
python -m tonesight_ns8.cli eval --goldset data/goldset.jsonl --out-root runs --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3
```

Record candidate path:
- `runs/<candidate_run_id>`

## 3) Compare deterministic drift deltas

```bash
python -m tonesight_ns8.cli compare runs/<baseline_run_id> runs/<candidate_run_id> --top-n 10 --write
```

Review:
- `runs/<candidate_run_id>/comparisons/<baseline_run_id>/compare_summary.json`

## 4) Apply deterministic gate thresholds

```bash
python -m tonesight_ns8.cli gate --run-a runs/<baseline_run_id> --run-b runs/<candidate_run_id>
```

Decision semantics:
- exit `0`: passed
- exit `2`: regressed
- exit `3`: incompatible receipts

## 5) Generate report + transition diagnostics

```bash
python -m tonesight_ns8.cli report --run-a runs/<baseline_run_id> --run-b runs/<candidate_run_id> --top-n 10
```

Review:
- `runs/<candidate_run_id>/reports/report_<baseline>_to_<candidate>.json`
- `runs/<candidate_run_id>/reports/transition_heatmap_<baseline>_to_<candidate>.json`

## 6) Maintain rolling stream state (optional live-like mode)

```bash
python -m tonesight_ns8.cli stream-update --segments-json segments_batch.json --session-id session_ops --state-out runs/stream/session_ops.json
python -m tonesight_ns8.cli stream-update --segments-json segments_batch_next.json --state-in runs/stream/session_ops.json --state-out runs/stream/session_ops.json
```

Behavior:
- appends deterministic segment batches into stream state
- emits deterministic snapshot fields compatible with session analytics
