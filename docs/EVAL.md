# Evaluation & Reporting

This document describes the implemented deterministic eval workflow.

Conformance vs evidence:
- eval/compare/gate artifacts in this document are conformance telemetry.
- benchmark artifacts (`benchmark --suite core|killer_stability|coding_agent_drift`) are empirical evidence outputs.
- use `docs/WHY_NS8.md` for claim-to-artifact mapping.
- v0.2.1 killer protocol reference: `docs/BENCHMARK_KILLER_STABILITY.md`.

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

CLI static report:

```bash
python -m tonesight_ns8.cli report --run-b runs/<candidate>
python -m tonesight_ns8.cli report --run-a runs/<baseline> --run-b runs/<candidate> --top-n 10
```

Report diagnostics artifact note:
- report command also writes a deterministic transition heatmap JSON artifact for single-run and compare views.

CLI dataset lint:

```bash
python -m tonesight_ns8.cli data-lint --dataset data/goldset.jsonl
python -m tonesight_ns8.cli data-lint --dataset data/goldset.jsonl --out runs/lint/goldset_lint.json
```

CLI release-check orchestration:

```bash
python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json
python -m tonesight_ns8.cli release-check --out runs/release/release_check.json
```

CLI benchmark suite:

```bash
python -m tonesight_ns8.cli benchmark --suite core
python -m tonesight_ns8.cli benchmark --suite core --out-root runs --goldset data/goldset.jsonl
python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl
python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/pseudo_real_trace.jsonl --killer-profiles default,phase_flip_cycle --killer-seeds 0,1 --killer-sweep-strengths 0.1,0.2
python -m tonesight_ns8.cli benchmark --suite coding_agent_drift --out-root runs --coding-baseline-events tests/fixtures/live_event.coding_agent.python.jsonl --coding-candidate-events tests/fixtures/live_event.coding_agent.typescript.jsonl,tests/fixtures/live_event.coding_agent.mismatch.jsonl
```

CLI incremental stream mode:

```bash
python -m tonesight_ns8.cli stream-update --segments-json segments_batch.json --session-id session_ops --state-out runs/stream/session_ops.json
python -m tonesight_ns8.cli stream-update --segments-json segments_batch_next.json --state-in runs/stream/session_ops.json --state-out runs/stream/session_ops.json
```

Optional killer benchmark controls:

```bash
python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl --killer-profiles default,oscillation_path,boundary_jitter --killer-seeds 0,1,2,3,4 --killer-primary-strength 0.2 --killer-sweep-strengths 0.05,0.1,0.15,0.2,0.3 --killer-sample-multiplier 2
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

## Pipeline Batch Adapters (v0.2.2 Phase 1)

For upstream batch integration, use deterministic package adapters:

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

Determinism contract:
- output ordering follows input ordering exactly
- each item is a receipt-compatible JSON object
- repeated calls over unchanged inputs return identical results

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

Killer benchmark artifacts (`benchmark --suite killer_stability`):
- `runs/benchmarks/killer_stability/evidence.json`
- `runs/benchmarks/killer_stability/robustness_summary.json`
- `runs/benchmarks/killer_stability/robustness_report.html`

Coding-agent drift benchmark artifacts (`benchmark --suite coding_agent_drift`):
- `runs/benchmarks/coding_agent_drift/evidence.json`
- `runs/benchmarks/coding_agent_drift/report.json`
- includes deterministic `gate_ready` summary deltas for profile/gate consumption.

Performance smoke policy:
- deterministic eval smoke is covered by `tests/test_eval_performance_smoke.py`
- conservative runtime threshold: eval on `data/goldset.jsonl` should complete in `< 30s`
- benchmark workflow remains non-blocking initially (`.github/workflows/benchmarks.yml`)

Killer benchmark interpretation:
- false drift distance: `d_c1_c2`
- true drift distance: `d_c1_c3`
- robustness drift distance: `d_c2_c4`
- headline metric: `separation_ratio_c12_over_c13` (lower is better)
- compare ToneSight against baselines under the same condition matrix and config
- robustness summary includes:
  - `wins_by_method`
  - `ratio_stats_by_method.<method>.mean/std/min/max/p10/p50/p90`
  - `absolute_criteria_pass_rate.<method>.*`
  - `tonesight_loss_tag_counts`
- treat findings as synthetic protocol evidence (not universal real-world performance proof)

Larger-`N` robustness subset (optional):
- generate deterministic `N=1000` fixture: `runs/benchmarks/killer_stability/goldset_n1000.jsonl`
- run: `python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs_n1000 --goldset runs/benchmarks/killer_stability/goldset_n1000.jsonl`
- compare with default `N=250` artifacts under `runs/benchmarks/killer_stability/`
- interpretation boundary: the `N=1000` fixture is derived/replicated from the base set and is a scaling/stability check, not independent-distribution validation.

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

Static report artifacts:
- `runs/<runB>/reports/report_<runB>.json` (single-run)
- `runs/<runB>/reports/report_<runA>_to_<runB>.json` (compare)
- `runs/<runB>/reports/transition_heatmap_<runB>.json` (single-run transitions)
- `runs/<runB>/reports/transition_heatmap_<runA>_to_<runB>.json` (compare transitions + delta matrix)

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
python -m tonesight_ns8.cli gate --run-a runs/<baseline> --run-b runs/<candidate> --profile coding_agent_drift --allow-dataset-mismatch
```

Threshold flags:
- `--min-pass-rate-delta` (default `-0.02`)
- `--max-avg-l1-delta` (default `0.2`)
- `--max-p95-l1-delta` (default `0.2`)
- `--profile <name>` (loads thresholds from `config/gate_profiles.json`)
- `--require-pinned-model-identity` (enforce provider/model/generation compatibility)
- coding-agent profile adds behavioral thresholds:
  - `max_language_mismatch_rate_delta`
  - `max_verbosity_bin_mean_delta`
  - `min_tests_presence_rate_delta`
  - `min_tool_call_rate_delta`

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
- optional pinned model identity gate:
  - `provider`
  - `model_identity` (`model_digest` preferred; `model_version` fallback)
  - `generation_settings` identity

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
- when coding-agent rows are present, triage includes additive coding fields (language mismatch and bin deltas)

## Static Report Command (Phase 5)

Create deterministic static JSON report artifacts from existing run outputs:

```bash
python -m tonesight_ns8.cli report --run-b runs/<candidate>
python -m tonesight_ns8.cli report --run-a runs/<baseline> --run-b runs/<candidate> --profile support_chat --top-n 10
```

Behavior:
- consumes existing artifacts only (`receipt.json`, `eval_summary.json`, optional compare/gate from `run_a`)
- includes reproducibility metadata from receipt (`spec_version`, hashes, mapping metadata)
- includes compare highlights and gate summary when `--run-a` is provided
- includes additive `coding_agent_drift` slice when coding-agent rows are present
- writes deterministic report JSON under `runs/<run_b>/reports/` by default
- repeated runs over unchanged inputs produce byte-stable output (`sort_keys=True` JSON)

## Dataset Lint Command (Phase 6)

Run deterministic JSONL quality checks before eval:

```bash
python -m tonesight_ns8.cli data-lint --dataset data/goldset.jsonl
```

Checks:
- malformed JSON rows
- missing or duplicate IDs
- invalid `target_vad`/`gold_vad` bins (must be `V/A/D` ints in `1..8`)
- invalid tags list/items

Output contract:
- machine-readable summary with deterministic violation ordering
- includes `violations_by_code`, full ordered `violations` list, and `exit_code`
- exit semantics: `0` when clean, `2` when violations exist

## Release-Check Command (Phase 7)

Run one deterministic command to evaluate pre-release readiness:

```bash
python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json
```

Checks (fixed order):
- `dataset_lint`
- `taxonomy_load`
- `gate_profiles_config`
- `nosec_policy`

Output contract:
- machine-readable JSON with per-check statuses and details
- top-level `decision`, `failed_checks`, and `exit_code`
- exit semantics: `0` pass, `2` fail (CI-friendly)

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
python -m tonesight_ns8.cli index-runs-json --out-root runs
python tools/generate_run_index_json.py --out-root runs
```

Behavior:
- discovers run directories containing `receipt.json`, `eval_summary.json`, and `out.jsonl`
- deterministic ordering by `run_id`
- stable schema with:
  - run IDs and version/hash metadata
  - profile/source labels (`profile_label`, `source_label`, `source_labels`)
  - artifact pointers (`out_jsonl`, `eval_summary_json`, `report_html`, `receipt_json`)
- idempotent output for unchanged run sets

JSON index bridge for read-only UI:
- `index-runs-json` converts deterministic `runs/index.jsonl` into deterministic `runs/index.json` array.
- conversion is read-only and does not recompute run metrics.

## Static Artifact API (Phase 2)

Minimal local API is available at `server/app.py`:

```bash
python server/app.py --runs-root runs --host 127.0.0.1 --port 8081
```

Routes (read-only artifact passthrough):
- `GET /health`
- `GET /api/index` -> `runs/index.json`
- `GET /api/run/{run_id}/receipt` -> `runs/{run_id}/receipt.json`
- `GET /api/run/{run_id}/summary` -> `runs/{run_id}/eval_summary.json`
- `GET /api/run/{run_id}/report` -> `runs/{run_id}/reports/report_{run_id}.json`
- `GET /api/run/{run_id}/report-html` -> `runs/{run_id}/report.html`
- `GET /api/compare/{run_a}/{run_b}` -> `runs/{run_b}/comparisons/{run_a}/compare_summary.json`
- `GET /api/compare-report/{run_a}/{run_b}` -> `runs/{run_b}/comparisons/{run_a}/compare_report.html`
- `GET /api/gate/{run_a}/{run_b}` -> `runs/{run_b}/comparisons/{run_a}/gate_result.json` (when persisted)

Contract boundary:
- API serves existing JSON artifacts only.
- API does not run eval/compare/gate computations.

Optional static UI demo package:

```bash
python -m tonesight_ns8.cli ui-package --out-root runs
```

Behavior:
- writes deterministic ZIP at `runs/ui_demo_package.zip` by default
- includes `ui/`, `server/`, and UI-safe run artifacts for local demo playback
- excludes raw artifacts (`out.jsonl`, `events.raw.jsonl`, `quarantine.jsonl`) unless `--include-raw-artifacts`

## Live Shadow Harness (Phase 17)

Deterministic capture/replay/verify flow for live-shaped events:

```bash
python -m tonesight_ns8.cli live-capture --events tests/fixtures/live_capture.small.jsonl --out-root runs
python -m tonesight_ns8.cli live-replay --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --shadow-strict quarantine
python -m tonesight_ns8.cli live-verify --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --shadow-strict quarantine
python -m tonesight_ns8.cli live-replay --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --adapter coding_agent
python -m tonesight_ns8.cli live-verify --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --adapter coding_agent
python -m tonesight_ns8.cli live-replay --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --adapter coding_agent --require-pinned-model-identity
python -m tonesight_ns8.cli live-verify --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --adapter coding_agent --require-pinned-model-identity
```

Behavior:
- `live-capture`: validates LiveEvent envelope and writes deterministic capture artifacts
- `live-replay`: maps upstream signal (`upstream_vad` or `upstream_label`) into standard run artifacts
- `live-replay --adapter coding_agent`: derives deterministic coding-agent features/bins and maps them to NS8-compatible VAD
- `--require-pinned-model-identity` (coding-agent only): fail-fast when provider/model identity/generation settings are missing
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

## ClawDBot Mode A (Log Ingestion)

Recommended low-coupling integration:
- write ClawDBot interaction logs as LiveEvent JSONL (`docs/LIVE_EVENT_SCHEMA.md`)
- ingest with `live-capture`
- replay with `live-replay --adapter coding_agent`
- compare/gate/report using existing run artifacts

Example:

```bash
python -m tonesight_ns8.cli live-capture --events clawdbot_events.jsonl --out-root runs
python -m tonesight_ns8.cli live-replay --capture runs/captures/<capture_id> --taxonomy taxonomy/tone_taxonomy.v1.json --threshold-l1 3 --adapter coding_agent --require-pinned-model-identity
python -m tonesight_ns8.cli gate --run-a runs/<baseline_live_run> --run-b runs/<candidate_live_run> --profile coding_agent_drift --allow-dataset-mismatch
python -m tonesight_ns8.cli report --run-a runs/<baseline_live_run> --run-b runs/<candidate_live_run> --profile coding_agent_drift --allow-dataset-mismatch
```

Boundary note:
- this mode provides deterministic behavioral consistency telemetry; it is not code-correctness or cognition scoring.
