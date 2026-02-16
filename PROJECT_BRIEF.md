# ToneSight NS8 - Implementation Brief (v1)

Scope note:
- This brief contains legacy planning context and is not authoritative for current runtime scope.
- Current authoritative behavior and scope are defined by `README.md`, `SPEC_NS8.md`, `.agent/AGENT_RULES.md`, and `.agent/TO-DO/PHASED_WORKFLOW.md`.
- Any references below to upstream affect estimation/generation are optional ecosystem context, not required core implementation.

## 1) Project purpose

ToneSight NS8 is a local-first tone compliance and observability service for LLM-generated text.

Its goal is to make tone measurable and monitorable by:
- estimating affect (VAD) from text
- discretizing into stable bins (NS8)
- scoring outputs against a target tone
- exposing metrics via standard MLOps tooling
- producing reproducible evaluation receipts

Important positioning:
- This is evaluation infrastructure.
- It does not claim psychological emotion accuracy.
- NS8 is used as a deterministic encoding layer, not an emotion model.

## 2) Core problem being solved

Modern LLM systems track latency, cost, and accuracy, but often lack reliable instrumentation for:
- tone regressions
- emotional drift
- style compliance

ToneSight NS8 provides a quantitative proxy signal suitable for:
- regression testing
- batch evaluation
- prompt comparison
- monitoring dashboards

## 3) High-level pipeline

### Mode A - Scoring existing text (primary)

Input:
- target tone (VAD bins or label)
- candidate text

Pipeline:
1. Affect estimation from text
2. Quantization -> `V/A/D in {1..8}`
3. NS8 encoding -> `<NS8E:...>` token
4. Distance computation vs target
5. Pass/fail decision
6. Metrics + receipts + monitoring

Output:
- predicted bins
- NS8 token
- distance metrics
- decision
- provenance IDs

### Mode B - Generate + score (optional)

Input:
- prompt
- target tone

Pipeline:
1. Generate candidates via Ollama (optional)
2. Run Mode A scoring on each candidate
3. Rank and report

## 4) NS8 role (precise definition)

What NS8 is in this project:
- deterministic discrete encoding layer
- operates on VAD bins (`1..8`)
- produces compact reversible tokens
- enables stable logging and monitoring
- supports reproducible artifacts

What NS8 is not:
- not an emotion detection method
- not improving classifier accuracy
- not required for tone scoring logic

The system should still work logically if NS8 tokens are replaced by raw bins.

## 5) Affect representation

Dimensions:
- Valence (`V`): `1..8`
- Arousal (`A`): `1..8`
- Dominance (`D`): `1..8`

Optional:
- quality tier `Q in {0..3}`
- confidence `in [0,1]`

Quantization:
- normalize predictor outputs to `[0,1]`
- `bin = min(8, max(1, floor(8*u) + 1))`

## 6) NS8 encoding specification

Parameters:
- `N = 8` (fixed for affect space)
- `k in {1..8}`
- `family in {TLF, TRF, BLF, BRF, TRB, TLB, BLB, BRB}`

Mapping (v1):
- `r = V`
- `c1 = A`
- `c2 = D`
- `s1 = A_FAMILY(r, c1, k, 8)`
- `s2 = A_FAMILY(r, c2, k, 8)`

Token should contain:
- `V` explicitly
- `k`
- `family`
- `S{s1}{s2}`
- `Q`
- `CRC`

Example:
- `<NS8E:V6-K3-FTLF-S27-Q2-ZM>`

Reversibility:
- decode by scanning `c in {1..8}` such that:
  - `A_FAMILY(V, c, k, 8) == s`
- this is required even when mapping is not strictly bijective

## 7) Bijectivity policy (important)

Because `N=8` is composite:
- some rows are not mathematically bijective
- decoding must use row scan
- families should be selected to maximize bijection

Recommended v1 rule:
- if `V` is even -> use top family (for example `TLF`)
- if `V` is odd -> use bottom family (for example `BLF`)

This preserves row-wise bijection more reliably for `N=8`.

## 8) Separate codespace (required)

`NS8E` token is only for affect. All provenance uses separate IDs.

Required IDs:
- `run_id`: unique per batch/eval run
  - format: `run_<ISO8601>_<shortid>`
- `dataset_id`: stable hash of input JSONL
  - `dataset_id = base32(sha256(file_bytes))[:12]`
- `config_id`: hash of canonical config JSON
  - `config_id = base32(sha256(canonical_json(config)))[:12]`
- `backend_id` (examples: `rule.v1`, `ollama_judge.v1`)

Critical rule:
- these IDs must not appear as Prometheus labels
- they belong in receipts, MLflow, and output artifacts

## 9) Monitoring architecture

Required stack:
- FastAPI service
- Prometheus metrics endpoint
- Grafana dashboards
- MLflow tracking
- per-run GPU snapshots

Optional:
- DCGM exporter
- Loki
- OpenTelemetry

## 10) Prometheus metrics (low cardinality only)

Operational:
- `http_requests_total`
- `http_request_duration_seconds`

Model behavior:
- `tone_score_requests_total{backend,decision}`
- `tone_l1_bucket{backend}`
- `tone_dim_abs_error_bucket{dim,backend}`
- `tone_quality_total{q,backend}`

Constraint:
- avoid high-cardinality labels

## 11) GPU monitoring requirements

Per-run snapshots (required), before and after batch/eval:
- collect via `nvidia-smi` if available:
  - GPU name
  - driver version
  - utilization
  - memory used/total
  - temperature
  - power draw (if available)

If no GPU:
- `"gpu": { "available": false }`

Snapshots must be saved and logged to MLflow.

Live GPU metrics (optional):
- support DCGM exporter behind Docker profile
- must not break CPU-only environments

## 12) Evaluation (goldset)

Goldset JSONL supports:

```json
{"id":"...","target":{"V":6,"A":3,"D":4},"text":"...","gold":{"V":6,"A":3,"D":4}}
```

(`gold` optional)

Eval computes:
- pass rate
- avg / p95 L1
- per-dim MAE
- confusion matrices (if gold present)
- distribution summaries

## 13) Known limitations (must be documented)

Documentation must explicitly state:
- text-only affect inference is noisy
- this metric is a proxy signal
- this is not psychological inference
- best use is regression detection and comparison

## 14) Definition of Done (v1)

Project is complete when:
- Docker Compose starts required stack
- `/health`, `/ready`, `/metrics` work
- `/v1/score`, `/v1/batch`, `/v1/eval` work
- NS8 encode/decode passes 1000 random round-trips
- MLflow logs runs and artifacts
- Grafana dashboards render
- GPU snapshots are recorded
- Prometheus metrics stay low-cardinality
- README includes limitations

## 15) Non-goals (important)

Do not:
- claim emotion accuracy
- claim NS8 improves detection quality
- add cloud dependencies
- add high-cardinality metrics
- over-engineer model backends

## Final one-line summary for implementation

ToneSight NS8 is a local-first evaluation service that estimates affect from text, discretizes it into NS8 bins, encodes it into reversible tokens, scores tone compliance against targets, and exposes reproducible metrics and monitoring suitable for production-style LLM evaluation.
