# ToneSight NS8

ToneSight NS8 is a deterministic tone-structure engine that converts discrete Valence-Arousal-Dominance (VAD) signals into stable lattice anchors using an NS8 symmetry framework.

It is designed as a domain-agnostic Python library and reusable post-processing layer for downstream tone-analysis pipelines.

## Overview

ToneSight NS8 addresses a common systems gap: a deterministic, testable mapping layer for discrete VAD-based affect signals.
The system prioritizes conformance, reproducibility, and regression detection over predictive modeling.
It acts as a deterministic conformance layer between probabilistic upstream models and production monitoring/evaluation systems.

Conceptual flow:

`VAD bins -> Tone taxonomy -> NS8 mapping -> Deterministic anchor`

Positioning summary:
- ToneSight NS8 is a deterministic conformance layer for VAD-based affect telemetry.
- It bridges probabilistic upstream affect outputs and production evaluation/monitoring systems.
- It provides vector-verified behavioral stability for the NS8 mapping contract (not psychological ground truth).

This repository currently focuses on:
- strict NS8 math contract
- reference implementation
- vector-verified behavior
- taxonomy validation

Quick links:
- quickstart: `README.md` (30-second demo + CLI usage below)
- benchmark command: `python -m tonesight_ns8.cli benchmark --suite core`
- evidence narrative: `docs/WHY_NS8.md`
- conformance contract: `docs/NS8_CONTRACT_ASSURANCE.md`

## Why This Exists

Most systems can measure latency and correctness, but have weak controls for deterministic tone conformance and regression tracking.
ToneSight NS8 focuses on that specific gap: deterministic encoding, reproducible evaluation artifacts, and stable run-to-run comparison.

Input boundary:
- ToneSight expects already-discretized VAD bins (`1..8`) or taxonomy labels.
- It does not clean raw sensor/audio/text signals; those concerns stay upstream.
- It does not infer emotions directly from raw content.

## Architecture (v1)

```text
Discrete VAD (or label)
        |
        v
taxonomy/tone_taxonomy.v1.json  ->  validated V/A/D in 1..8
        |
        v
NS8 deterministic mapping (docs/SPEC_NS8.md, ns8_ref.py)
        |
        +--> receipt APIs / CLI encode-decode
        |
        +--> eval artifacts (out.jsonl, eval_summary.json, report.html, receipt.json)
                |
                +--> compare/eval-compare deterministic regression deltas
                        |
                        +--> optional observability (FastAPI/Prometheus/Grafana)
```

## 30-Second Quick Demo

```bash
python -m tonesight_ns8.cli eval
```

Expected:
- prints JSON with `run_id` and `out_dir`
- writes `runs/<run_id>/out.jsonl`
- writes `runs/<run_id>/eval_summary.json`
- writes `runs/<run_id>/report.html`
- writes `runs/<run_id>/receipt.json`

## 5-Minute Path

```bash
python -m pip install -e .
python -m tonesight_ns8.cli eval
python -m tonesight_ns8.cli compare runs/<baseline_run> runs/<candidate_run> --top-n 10 --write
python -m tonesight_ns8.cli benchmark --suite core
```

Deterministic demo script:

```bash
python examples/ns8_drift_demo.py --out-root runs/demo
```

## Hello Tone Example

```python
from tonesight_ns8 import tonesight_from_label

receipt = tonesight_from_label(
    label="empathetic",
    family="TRF",
    r=6,
    c=4,
    k=3,
    taxonomy_path="taxonomy/tone_taxonomy.v1.json",
)
print(receipt["output"]["A"])
```

## Batch Adapters (Phase 1)

Deterministic pipeline helpers for batch inputs:

```python
from tonesight_ns8 import tonesight_from_llm_labels, tonesight_from_vad_batch

vad_receipts = tonesight_from_vad_batch(
    [{"V": 7, "A": 3, "D": 3}, {"V": 2, "A": 7, "D": 4}],
    family="TRF",
    r=6,
    c=4,
    k=3,
)

label_receipts = tonesight_from_llm_labels(
    ["empathetic", "reassuring"],
    family="TRF",
    r=6,
    c=4,
    k=3,
    taxonomy_path="taxonomy/tone_taxonomy.v1.json",
)
```

End-to-end runnable example:

```bash
python examples/batch_adapters_demo.py
```

## Installation

Clone the repository and install in editable mode:

```bash
pip install -e .
```

Requirements:
- Python 3.11+
- `pytest` (for running tests)

After install, verify the CLI using module invocation (recommended and cross-platform):

```bash
python -m tonesight_ns8.cli --help
```

Optional convenience entrypoint (works when your Python Scripts directory is on `PATH`):

```bash
tonesight-ns8 --help
```

## Troubleshooting

If editable install fails due to temp directory permissions on Windows, use a writable local temp path:

PowerShell:

```powershell
mkdir .tmp | Out-Null
$env:TEMP = "$pwd\\.tmp"
$env:TMP  = "$pwd\\.tmp"
$env:PIP_CACHE_DIR = "$pwd\\.tmp\\pip-cache"
pip install -e .
```

CMD:

```cmd
mkdir .tmp
set TEMP=%cd%\\.tmp
set TMP=%cd%\\.tmp
set PIP_CACHE_DIR=%cd%\\.tmp\\pip-cache
pip install -e .
```

If `tonesight-ns8` is not recognized on Windows, either:
- use `python -m tonesight_ns8.cli ...` (recommended), or
- add `C:\Users\<you>\AppData\Roaming\Python\Python3xx\Scripts` to `PATH`.

Sanity reset (if environment looks stale):

```bash
python -m pip uninstall -y tonesight-ns8
python -m pip install -e .
python -m tonesight_ns8.cli --help
```

## What ToneSight NS8 Is Not

ToneSight NS8 is:
- not an emotion recognition model
- not a machine learning classifier
- not a probabilistic embedding system

It is a deterministic structural mapping layer that operates on discrete VAD inputs.

## Design Principles

### Deterministic
- identical inputs produce identical outputs
- no stochastic behavior in the NS8 core

### Strict validation
- out-of-domain inputs raise explicit exceptions
- no silent wrapping for external inputs

### Separation of concerns
- VAD estimation is external to this library
- ToneSight operates on discrete VAD inputs
- NS8 math is isolated and test-driven
- ToneSight NS8 operates on already-discretized VAD inputs; estimation of VAD from audio is intentionally out of scope.

### Auditability
- behavior is pinned by test vectors
- reproducibility is enforced in tests
- spec versioning is explicit

## Mathematical Specification Summary

- Lattice indexing is 1-based.
- `N = 8` is fixed for v1.
- Canonical seeds: `TLF`, `TRB`.
- Derived families route through symmetry transforms only.
- Output range is `A in {1..8}`.

Authoritative reference:
- `docs/SPEC_NS8.md`
- `docs/NS8_CONTRACT_ASSURANCE.md`

## Tone Taxonomy

Taxonomy provides deterministic label-to-VAD mapping for friendly tone labels.
It does not perform emotion inference in core logic.

Source of truth:
- `taxonomy/tone_taxonomy.v1.json`

Constraints:
- each tone defines exactly `V, A, D`
- each value is integer in `1..8`
- mappings are human-authored and versioned

Notes:
- taxonomy is deterministic
- taxonomy is replaceable with another versioned file

## Data Model

- Segment: a time-bounded unit of analysis.
- Speaker: source identifier for segments.
- Session: container for segments.

ToneSight NS8 operates on segments that may be attributed to a speaker and grouped into a session. These concepts are domain-neutral and apply to calls, interviews, podcasts, sessions, and other multi-speaker audio.

## Analytics

Core analytics produce deterministic JSON-serializable summaries:
- speaker centroid (mean V/A/D bins)
- speaker volatility (mean absolute change in arousal across consecutive speaker segments)
- arousal momentum (`mean_momentum`, `positive_momentum_ratio`)
- tone stability index (bounded `0..1` from normalized volatility)
- session tone profile (aggregate centroid + distributions)
- session drift (`drift_v`, `drift_a`, `drift_d`, optional `drift_anchor`) over deterministic boundary windows
- arousal spike detection (configurable threshold; default `7`)
- spike density (backward-compatible alias of spike rate)
- distributions/histograms for `V`, `A`, `D`, and NS8 anchor `A`

No plotting is included in core. Visualization is downstream.

Derived metrics contract reference:
- `docs/DERIVED_METRICS.md`

## Security

Repository security process:
- vulnerability disclosure policy: `SECURITY.md`
- contribution/security guidance: `CONTRIBUTING.md`
- automated CI security checks: `.github/workflows/security.yml`

Local high-signal checks:

```bash
# Secrets
gitleaks detect --source . --redact --no-git
gitleaks detect --source . --redact

# Dependencies / SAST
pip-audit
python tools/check_nosec_policy.py
python -m bandit -r src
```

CI note:
- `.github/workflows/ci.yml` includes a required `security-bandit` job running `python -m bandit -r src`.

## API Reference

Detailed API is documented in:
- `docs/API_REFERENCE.md`

The current reference implementation exposes `ns8_A` and `ns8_route`.
Future packaged releases will provide stable wrapper APIs while preserving deterministic behavior.

## Mapping Registry

ToneSight includes a deterministic mapping registry with NS8 registered as the default adapter (`mapping_id="ns8"`).
This enables future mapping implementations without changing core eval/receipt contracts.

Current mapping-aware surfaces:
- Python wrappers accept optional `mapping_id` (`tonesight_from_vad`, `tonesight_from_label`, segment helpers)
- CLI supports `--mapping` for `encode` and `decode`

Developer references:
- example adapter: `tonesight_ns8.mapping_examples.TLFConstantMappingAdapter`
- reusable adapter conformance helper: `tests/mapping_conformance.py`

### Current runnable interface

- `ns8_A(family, r, c, k, n=8) -> int`
- `ns8_route(family, r, c, k, n=8) -> Route`
- `wrapN(x, n=8) -> int`
- `H(c, n=8) -> int`
- `V(r, n=8) -> int`

### Minimal runnable example

```python
from ns8_ref import ns8_A, ns8_route

a = ns8_A("TRF", 6, 4, 3)
route = ns8_route("TRF", 6, 4, 3)

print(a)
print(route)
```

## Test Vector Policy

- `vectors/ns8_test_vectors.json` is normative for behavior verification.
- Normative vector conformance guarantees behavioral stability across implementations.
- Implementations must pass the vector suite.
- Any behavior change requires:
  - spec version bump
  - updated vectors
  - updated tests

Contract assurance and requirement-to-evidence matrix:
- `docs/NS8_CONTRACT_ASSURANCE.md`

## Segment Contract

Normative segment input contract:
- `docs/SEGMENT_INTERFACE.md`

Analytics metric definitions and output examples:
- `docs/ANALYTICS.md`

Normative defaults config contract:
- `docs/DEFAULTS_SCHEMA.md`

Release readiness checklist:
- `docs/RELEASE_CHECKLIST.md`
- `docs/SECURITY_POLICY.md`
- `docs/CANONICAL_ID_POLICY.md`
- `docs/LIVE_EVENT_SCHEMA.md`
- `docs/IDENTITY_AND_HASHING.md`
- `docs/PRIVACY_REDACTION.md`
- `docs/RETENTION_POLICY.md`
- `docs/WHY_NS8.md`
- `docs/RECIPES/drift_monitoring.md`

## CLI Usage

CLI is available as a thin wrapper over library functions.

Default values for `eval` and `eval-compare` are loaded from `config/defaults.json`:
- `goldset_path`
- `out_root`
- `taxonomy_path`
- `threshold_l1`
- optional defaults (`calibration_path`, `capture_gpu`, `mlflow_tracking_uri`)

You can override the defaults file path at runtime with:
- `TONESIGHT_DEFAULTS_PATH=/path/to/defaults.json`

Examples:

```bash
TONESIGHT_DEFAULTS_PATH=config/defaults.json python -m tonesight_ns8.cli eval
TONESIGHT_DEFAULTS_PATH=config/defaults.json python -m tonesight_ns8.cli eval-compare
```

```powershell
$env:TONESIGHT_DEFAULTS_PATH = "config/defaults.json"
python -m tonesight_ns8.cli eval
python -m tonesight_ns8.cli eval-compare
```

```cmd
set TONESIGHT_DEFAULTS_PATH=config\defaults.json
python -m tonesight_ns8.cli eval
python -m tonesight_ns8.cli eval-compare
```

Commands:

```bash
python -m tonesight_ns8.cli encode --family TRF --r 6 --c 4 --k 3 --V 7 --A 3 --D 3
python -m tonesight_ns8.cli encode --family TRF --r 6 --c 4 --k 3 --label empathetic --taxonomy taxonomy/tone_taxonomy.v1.json
python -m tonesight_ns8.cli decode --family TRF --r 6 --c 4 --k 3
python -m tonesight_ns8.cli summarize --segments-json segments.json --session-id session_001
python -m tonesight_ns8.cli eval
python -m tonesight_ns8.cli eval --goldset data/goldset.jsonl --out-root runs --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3
python -m tonesight_ns8.cli eval --goldset data/goldset.jsonl --out-root runs --taxonomy taxonomy/tone_taxonomy.v1.json --calibration config/taxonomy_calibration.v1.json --threshold-l1 3
python -m tonesight_ns8.cli eval-compare
python -m tonesight_ns8.cli eval-compare --goldset data/goldset.jsonl --out-root runs --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --top-n 10
python -m tonesight_ns8.cli compare runs/<runA> runs/<runB> --top-n 10 --write
python -m tonesight_ns8.cli compare runs/<runA> runs/<runB> --distance topology --top-n 10 --write
python -m tonesight_ns8.cli gate --run-a runs/<baseline> --run-b runs/<candidate>
python -m tonesight_ns8.cli gate --run-a runs/<baseline> --run-b runs/<candidate> --profile support_chat
python -m tonesight_ns8.cli gate --run-a runs/<baseline> --run-b runs/<candidate> --allow-dataset-mismatch
python -m tonesight_ns8.cli triage --run-b runs/<candidate> --top-n 50 --format jsonl
python -m tonesight_ns8.cli triage --run-a runs/<baseline> --run-b runs/<candidate> --top-n 50 --format csv
python -m tonesight_ns8.cli bundle --run-b runs/<candidate>
python -m tonesight_ns8.cli bundle --run-a runs/<baseline> --run-b runs/<candidate>
python -m tonesight_ns8.cli bundle --run-b runs/<candidate> --include-source-paths
python -m tonesight_ns8.cli trend --out-root runs
python -m tonesight_ns8.cli trend --out-root runs --group-by source
python -m tonesight_ns8.cli index-runs --out-root runs
python -m tonesight_ns8.cli report --run-b runs/<candidate>
python -m tonesight_ns8.cli report --run-a runs/<baseline> --run-b runs/<candidate> --top-n 10
python -m tonesight_ns8.cli stream-update --segments-json segments_batch.json --session-id session_ops --state-out runs/stream/session_ops.json
python -m tonesight_ns8.cli stream-update --segments-json segments_batch_next.json --state-in runs/stream/session_ops.json --state-out runs/stream/session_ops.json
python -m tonesight_ns8.cli data-lint --dataset data/goldset.jsonl
python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json
python -m tonesight_ns8.cli benchmark --suite core
python -m tonesight_ns8.cli benchmark --suite core --out-root runs --goldset data/goldset.jsonl
python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl
python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl --killer-profiles default,oscillation_path,boundary_jitter --killer-seeds 0,1,2,3,4 --killer-primary-strength 0.2 --killer-sweep-strengths 0.05,0.1,0.15,0.2,0.3 --killer-sample-multiplier 2
python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/pseudo_real_trace.jsonl --killer-profiles default,phase_flip_cycle --killer-seeds 0,1 --killer-sweep-strengths 0.1,0.2
python -m tonesight_ns8.cli live-capture --events tests/fixtures/live_capture.small.jsonl --out-root runs
python -m tonesight_ns8.cli live-replay --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --shadow-strict quarantine
python -m tonesight_ns8.cli live-verify --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --shadow-strict quarantine
python -m tonesight_ns8.cli canary --capture runs/captures/<capture_id> --baseline-out-root runs/canary/baseline --candidate-out-root runs/canary/candidate --profile support_chat
python -m tonesight_ns8.cli incident --run-a runs/<baseline> --run-b runs/<candidate> --top-n 50
python -m tonesight_ns8.cli purge --out-root runs --older-than-days 30
python -m tonesight_ns8.cli purge --out-root runs --older-than-days 30 --apply
```

Eval artifacts:
- `runs/<run_id>/out.jsonl`
- `runs/<run_id>/eval_summary.json`
- `runs/<run_id>/report.html`
- `runs/<run_id>/receipt.json`

Compare artifact (optional with `--write`):
- `runs/<runB>/comparisons/<runA>/compare_summary.json`
- `runs/<runB>/comparisons/<runA>/compare_report.html`

Static report artifacts:
- `runs/<runB>/reports/report_<runB>.json` (single-run)
- `runs/<runB>/reports/report_<runA>_to_<runB>.json` (compare)
- `runs/<runB>/reports/transition_heatmap_<runB>.json` (single-run transitions)
- `runs/<runB>/reports/transition_heatmap_<runA>_to_<runB>.json` (compare transitions + delta matrix)

Gate command (`gate`) exit codes:
- `0`: gate passed
- `2`: regression threshold violated
- `3`: incompatible runs (`dataset_hash`/`spec_version` mismatch)

Release-check command (`release-check`) exit codes:
- `0`: all required pre-release checks passed
- `2`: one or more required checks failed

Gate profiles:
- configured in `config/gate_profiles.json`
- selected with `--profile <name>`
- explicit CLI thresholds still override selected profile values

Optional eval artifacts:
- `runs/<run_id>/gpu_before.json`
- `runs/<run_id>/gpu_after.json`

Live replay artifacts:
- `runs/captures/<capture_id>/events.raw.jsonl`
- `runs/captures/<capture_id>/capture_manifest.json`
- `runs/<run_live_id>/out.jsonl`
- `runs/<run_live_id>/eval_summary.json`
- `runs/<run_live_id>/report.html`
- `runs/<run_live_id>/receipt.json`
- `runs/<run_live_id>/quarantine.jsonl` (when `--shadow-strict quarantine` and invalid events exist)
- `redaction_summary` in replay `eval_summary.json` and `receipt.json`

Canary/incident artifacts:
- canary payload includes baseline/candidate replay metadata, `compare_summary`, and `gate_result`
- incident writes:
  - `runs/<runB>/comparisons/<runA>/compare_summary.json`
  - `runs/<runB>/comparisons/<runA>/compare_report.html`
  - `runs/<runB>/comparisons/<runA>/triage_<score>.<jsonl|csv>`
  - `runs/<runB>/bundles/forensics_bundle__vs__<runA>.zip`
  - `runs/<runB>/incidents/<runA>/incident_report.md`

Run index artifact:
- `runs/index.jsonl` (`index-runs`) with one deterministic row per discovered run

Benchmark artifacts (`benchmark --suite core`):
- `runs/benchmarks/core/noise_tolerance.json`
- `runs/benchmarks/core/drift_injection.json`
- `runs/benchmarks/core/model_swap_robustness.json`
- `runs/benchmarks/core/baselines.json`
- `runs/benchmarks/core/transition_coherence.json`
- `runs/benchmarks/core/report.json`

Killer benchmark artifacts (`benchmark --suite killer_stability`):
- `runs/benchmarks/killer_stability/evidence.json`
- `runs/benchmarks/killer_stability/robustness_summary.json`
- `runs/benchmarks/killer_stability/robustness_report.html`
- includes deterministic `C1/C2/C3/C4` condition distances and `separation_ratio_c12_over_c13` per method
- includes synthetic multi-seed/profile robustness stats:
  - `wins_by_method`
  - `ratio_stats_by_method` (`mean/std/min/max/p10/p50/p90`)
  - `absolute_criteria_pass_rate` (`ratio<1`, `true>false`, combined pass-rate)
  - `tonesight_loss_tag_counts` for non-winning ToneSight robustness runs
  - `by_profile` summary blocks for per-profile ranking/tail/pass-rate review

Robustness summary snapshot (`runs/benchmarks/killer_stability/robustness_summary.json`, `N=250`):

| Method | Wins (20 runs) | Mean | p50 | p90 | Max | `ratio<1` pass-rate |
|---|---:|---:|---:|---:|---:|---:|
| ToneSight | 10 | 1.037 | 0.867 | 1.644 | 1.789 | 0.70 |
| equal_width | 5 | 1.702 | 1.736 | 3.107 | 3.829 | 0.40 |
| quantile | 3 | 3.511 | 2.831 | 7.333 | 9.383 | 0.25 |
| raw_jsd_hist16 | 2 | 1.512 | 1.399 | 2.049 | 2.758 | 0.20 |

Where ToneSight loses (`tonesight_loss_tag_counts`, `N=250`):
- `occupancy_dominated_shift`: 5
- `ramp_mild_or_late`: 5
- `transition_signal_weak`: 3
- `true_drift_not_dominant`: 3

Larger-`N` subset check (`N=1000` derived fixture):
- run: `python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs_n1000 --goldset runs/benchmarks/killer_stability/goldset_n1000.jsonl`
- artifacts: `runs_n1000/benchmarks/killer_stability/evidence.json`, `runs_n1000/benchmarks/killer_stability/robustness_summary.json`
- ToneSight summary: wins `13/20`, mean `0.940`, p50 `0.868`, p90 `1.312`, max `1.365`, `ratio<1` pass-rate `0.75`
- interpretation guardrail: this `N=1000` fixture is deterministically derived from the same source set and is a scaling check, not independent-distribution validation.

`N=250` vs `N=1000` (derived) robustness comparison:

| Method | N=250 wins | N=250 mean | N=250 p90 | N=250 `ratio<1` | N=1000 wins | N=1000 mean | N=1000 p90 | N=1000 `ratio<1` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ToneSight | 10 | 1.037 | 1.644 | 0.70 | 13 | 0.940 | 1.312 | 0.75 |
| equal_width | 5 | 1.702 | 3.107 | 0.40 | 6 | 1.205 | 1.950 | 0.35 |
| quantile | 3 | 3.511 | 7.333 | 0.25 | 0 | 3.077 | 5.556 | 0.25 |
| raw_jsd_hist16 | 2 | 1.512 | 2.049 | 0.20 | 1 | 1.568 | 2.012 | 0.05 |

Fixed-metric policy:
- keep `tonesight_distance_metric` weights fixed (`topology_pair=0.7`, `transition_jsd=0.2`, `occupancy_jsd=0.1`) across profile/seed sweeps.
- use robustness profiles to test structural behavior; do not retune per profile to improve win counts.

Claim boundary note:
- killer benchmark outputs are synthetic controlled evidence for conformance/drift comparability;
- they should not be interpreted as direct emotion-inference quality claims.

Performance smoke policy:
- deterministic eval smoke test: `tests/test_eval_performance_smoke.py`
- conservative threshold: eval on `data/goldset.jsonl` completes in `< 30s`
- benchmark workflow is currently non-blocking: `.github/workflows/benchmarks.yml`

## 30-Second Local Demo

Run a deterministic eval:

```bash
python -m tonesight_ns8.cli eval
```

This uses defaults from `config/defaults.json`. You can still override with explicit flags.

Expected artifacts:
- `runs/<run_id>/out.jsonl`
- `runs/<run_id>/eval_summary.json`
- `runs/<run_id>/report.html`
- `runs/<run_id>/receipt.json`

Presentation mode for screenshot-ready report view:

```text
runs/<run_id>/report.html?mode=present
```

The `mode=present` preset applies deterministic camera/control defaults for stable demos.

Example `eval_summary.json` (shape only):

```json
{
  "run_id": "run_20260214T000000Z_abc123def456",
  "count_rows": 20,
  "threshold_l1": 3,
  "pass_count": 18,
  "fail_count": 2,
  "pass_rate": 0.9,
  "fail_rate": 0.1,
  "avg_l1": 0.0,
  "median_l1": 0.0,
  "p95_l1": 0.0,
  "max_l1": 2.0,
  "count_with_gold_vad": 20,
  "count_without_gold_vad": 0,
  "avg_accuracy_l1": 0.0
}
```

Example `receipt.json` (shape only):

```json
{
  "spec_version": "1.0",
  "run_id": "run_20260214T000000Z_abc123def456",
  "dataset_path": "data/goldset.jsonl",
  "dataset_hash": "abc123def456",
  "taxonomy_hash": "7e2f9b31c1d4",
  "defaults_hash": "9af18c0042de",
  "row_count": 20,
  "config": {
    "threshold_l1": 3,
    "taxonomy_path": "taxonomy/tone_taxonomy.v1.json"
  },
  "artifacts": {
    "out_jsonl": "runs/<run_id>/out.jsonl",
    "eval_summary_json": "runs/<run_id>/eval_summary.json",
    "report_html": "runs/<run_id>/report.html",
    "receipt_json": "runs/<run_id>/receipt.json"
  },
  "created_at_utc": "2026-02-14T00:00:00+00:00"
}
```

Note: `run_id` and `created_at_utc` are metadata and vary per run; scoring metrics and artifact schema remain deterministic for fixed inputs/config.

Conformance note:
- `pass_rate` in this project is a conformance metric against target VAD bins.
- The goldset intentionally includes negative anchors to validate failure surfacing and regression sensitivity.
- This metric is not a claim of classifier accuracy.

## Goldset Validation

Validate dataset integrity before eval:

```bash
python tools/validate_goldset.py data/goldset.jsonl
```

Live event envelope validation:

```bash
python tools/validate_live_event.py tests/fixtures/live_event.valid.jsonl
```

Live shadow replay validation:

```bash
python -m tonesight_ns8.cli live-capture --events tests/fixtures/live_capture.small.jsonl --out-root runs
python -m tonesight_ns8.cli live-verify --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --shadow-strict quarantine
```

Retention dry-run/apply:

```bash
python -m tonesight_ns8.cli purge --out-root runs --older-than-days 30
python -m tonesight_ns8.cli purge --out-root runs --older-than-days 30 --apply
```

Automated validation workflow (tests + goldset validator):

```bash
python -m pytest -q
python tools/validate_goldset.py data/goldset.jsonl
```

Cross-environment determinism validation:
- CI includes a dedicated `determinism-matrix` job in `.github/workflows/ci.yml`
- current matrix targets:
  - `ubuntu-latest` + Python `3.11`
  - `windows-latest` + Python `3.11`
- matrix checks run:
  - `python -m pytest -q`
  - `python tools/regen_vectors.py`
  - `git diff --exit-code`

## Path B Monitoring (Opt-in)

This repository includes optional, opt-in observability components that are not required for core deterministic functionality:
- FastAPI observability app (`/health`, `/metrics`, `/eval/run`, `/eval/last`)
- Prometheus scraping API metrics
- Grafana dashboard provisioning
- deterministic conformance telemetry suitable for run-to-run drift monitoring

Start the stack:

```bash
export TONESIGHT_API_TOKEN="<strong-random-token>"
export GF_SECURITY_ADMIN_USER="<grafana-admin-user>"
export GF_SECURITY_ADMIN_PASSWORD="<strong-grafana-password>"
docker compose up --build
```

Endpoints:
- API: `http://localhost:8080/health`
- API metrics: `http://localhost:8080/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (credentials from `GF_SECURITY_ADMIN_USER` / `GF_SECURITY_ADMIN_PASSWORD`)

Protected API routes require bearer token:
- `/metrics`
- `/eval/run`
- `/eval/last`

Example:

```bash
curl -H "Authorization: Bearer $TONESIGHT_API_TOKEN" http://localhost:8080/metrics
```

Dashboard behavior notes:
- `API RPS` and `API p95 latency` live panels are intentionally volatile at low traffic.
- Use the `30m smoothed` panels for stable interpretation.
- Eval quality panels are latest-snapshot gauges from the most recent `/eval/run`.

Local non-Docker install (optional):

```bash
pip install -e ".[observability]"
uvicorn tonesight_ns8.observability_api:app --host 0.0.0.0 --port 8080
```

Trigger eval via API with optional calibration/MLflow/GPU settings:

```bash
curl -X POST http://localhost:8080/eval/run \
  -H "Authorization: Bearer $TONESIGHT_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"goldset_path":"data/goldset.jsonl","out_root":"runs","taxonomy_path":"taxonomy/tone_taxonomy.v1.json","threshold_l1":3,"calibration_path":"config/taxonomy_calibration.v1.json","capture_gpu":false,"mlflow_tracking_uri":""}'
```

## Repository Structure

```text
.
|-- README.md
|-- pyproject.toml
|-- docker-compose.yml
|-- LICENSE
|-- ns8_ref.py
|-- src/
|   `-- tonesight_ns8/
|       |-- api.py
|       |-- cli.py
|       |-- eval_runner.py
|       |-- compare_runner.py
|       |-- gate_runner.py
|       |-- stream_runner.py
|       |-- report_runner.py
|       |-- benchmark_killer_stability.py
|       `-- ...
|-- data/
|   |-- goldset.jsonl
|   `-- pseudo_real_trace.jsonl
|-- vectors/
|   `-- ns8_test_vectors.json
|-- taxonomy/
|   `-- tone_taxonomy.v1.json
|-- config/
|   |-- defaults.json
|   |-- gate_profiles.json
|   |-- taxonomy_calibration.v1.json
|   `-- vad_quantization.v1.json
|-- docs/
|   |-- ANALYTICS.md
|   |-- API_REFERENCE.md
|   |-- BENCHMARK_KILLER_STABILITY.md
|   |-- CANONICAL_ID_POLICY.md
|   |-- DEFAULTS_SCHEMA.md
|   |-- DERIVED_METRICS.md
|   |-- EVAL.md
|   |-- IDENTITY_AND_HASHING.md
|   |-- INCIDENT_PLAYBOOK.md
|   |-- LIVE_COMPATIBILITY.md
|   |-- LIVE_EVENT_SCHEMA.md
|   |-- MONITORING.md
|   |-- NS8_CONTRACT_ASSURANCE.md
|   |-- PRIVACY_REDACTION.md
|   |-- RECIPES/
|   |   `-- drift_monitoring.md
|   |-- RELEASE_CHECKLIST.md
|   |-- RELEASE_NOTES_0.2.2.md
|   |-- RECEIPT_SCHEMA.md
|   |-- RETENTION_POLICY.md
|   |-- SECURITY_POLICY.md
|   |-- SPEC_NS8.md
|   |-- SEGMENT_INTERFACE.md
|   `-- WHY_NS8.md
|-- benchmarks/
|   |-- baselines.py
|   |-- drift_injection.py
|   |-- model_swap_robustness.py
|   |-- noise_tolerance.py
|   `-- README.md
|-- examples/
|   |-- batch_adapters_demo.py
|   |-- demo_compute.py
|   `-- ns8_drift_demo.py
|-- tools/
|   |-- check_nosec_policy.py
|   `-- regen_vectors.py
|-- tests/
|   |-- test_stream_runner.py
|   |-- test_report_runner.py
|   |-- test_benchmark_killer_stability.py
|   `-- ...
|-- test_cli.py
`-- test_ns8_vectors.py
```

Note: The current layout uses a reference implementation (`ns8_ref.py`).
`ns8_ref.py` remains the oracle until packaged implementation parity is proven by vectors + invariants.

## Versioning and Stability

- Library/package versioning follows semantic versioning and is currently pre-1.0 (`0.x` series).
- Current package version target: `0.2.2`.
- NS8 spec version is tracked separately in `docs/SPEC_NS8.md`.
- The NS8 specification is stable within a major version.

Compatibility expectations:
- patch/minor updates must not change NS8 math behavior without explicit spec handling
- behavior changes require spec and vector updates

Phase 2 status:
- Formula decision is resolved (Option A retained).
- Runtime behavior is frozen to `spec_version: 1.0` using `docs/SPEC_NS8.md` + `vectors/ns8_test_vectors.json`.

## Limitations

- ToneSight NS8 does not perform emotion recognition.
- Continuous VAD estimation is external.
- Correctness depends on input quality.
- Dominance may be inferred upstream if unavailable.

## Quick Start

Run the test suite:

```bash
python -m pytest -q
```

Minimal example:

```python
from ns8_ref import ns8_A
print(ns8_A("TLF", 1, 1, 1))
```
## Licensing Boundary

ToneSight NS8 is open and currently licensed under MIT.
NS8 in this repository is the in-scope reference mapping for the toolkit and is currently covered by MIT in this pre-1.0 release line.
ToneSight NS8 is released under the MIT License.
For commercial licensing, enterprise support, or OEM inquiries, please contact: Nicholas@CollaborativeCurators.com

Authoritative files:
- `LICENSE`
- `LICENSE_POLICY.md`
