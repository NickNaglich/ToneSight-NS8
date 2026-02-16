# Evaluation & Reporting

This repo includes a compact evaluation workflow for operational tone-compliance checks:
- Run a goldset
- Produce repeatable metrics and artifacts
- Track runs in MLflow
- Visualize system + model health in Grafana

## 1) Goldset format

File: `data/goldset.jsonl`

Recommended starter size: 100-200 examples.

Each line (minimum):

```json
{"id":"g_001","target":{"V":6,"A":3,"D":4},"text":"Thanks for reaching out..."}
```

Optional gold labels (if you have curated labels):

```json
{"id":"g_001","target":{"V":6,"A":3,"D":4},"text":"...","gold":{"V":6,"A":3,"D":4}}
```

Notes:
- If `gold` is omitted, eval measures consistency and distribution stats vs target.
- If `gold` exists, eval computes predictive accuracy and confusion matrices.
- You can include prompt context and multiple candidates per prompt by storing multiple rows with shared prompt IDs.
- Recommended dataset strategy: start with 20-30 human-authored anchors, then expand with synthetic variants while preserving anchor stability.

## 2) Eval outputs

Running eval produces:
- `runs/{run_id}/receipt.json`
- `runs/{run_id}/eval_summary.json`
- `runs/{run_id}/confusion_V.csv`
- `runs/{run_id}/confusion_A.csv`
- `runs/{run_id}/confusion_D.csv`
- `runs/{run_id}/report.html` (optional but recommended)
- `runs/{run_id}/gpu_before.json`
- `runs/{run_id}/gpu_after.json`

All of these should be logged as MLflow artifacts.

`report.html` should include:
- pass rate
- mean/p95 L1
- per-dimension error bars (V/A/D)
- top failures with short text snippets

## 3) Metrics to compute (operationally useful)

Operational:
- eval duration
- rows processed

Model behavior:
- pass_rate (using configured threshold)
- avg/median/p95 L1
- per-dimension MAE: V/A/D
- quality tier distribution

If gold labels are present:
- per-dim accuracy
- confusion matrices
- macro-averaged accuracy

Drift-ish (simple but credible):
- distribution shift for predicted V/A/D vs baseline
- average text length shift
- sentiment proxy distribution shift

Optional backend comparison (if enabled):
- side-by-side `rule.v1` vs `ollama_judge.v1`
- pass_rate
- avg L1
- latency per item
- GPU snapshot delta (if Ollama uses GPU)

## 4) Running eval

CLI:

```bash
python -m app.cli eval --gold data/goldset.jsonl
```

API:

```json
POST /v1/eval
{
  "gold_path": "data/goldset.jsonl",
  "config": { "threshold_l1": 3 }
}
```

## 5) How to review an eval run

1. Run eval to produce a `run_id`.
2. Open MLflow:
   - show run params/metrics/artifacts
3. Open Grafana:
   - show pass rate trend and L1 distribution
   - show API latency
   - show GPU utilization panels (if enabled)
4. Open `receipt.json`:
   - show dataset hash + config hash + gpu snapshots for that run

## Implementation note for GPU support in Docker

When GPU-related compose services are added, keep them behind a profile so CPU-only users are not blocked:
- `dcgm-exporter` under `profiles: ["gpu"]`
- `api` can optionally request GPU only when `gpu` profile is enabled

Per-run snapshots should be best-effort and never crash a run.
