# API Reference

This document defines the Python interface for ToneSight NS8.

## Status

- Current: package wrappers are available in `src/tonesight_ns8`.
- Current: `ns8_ref.py` remains the oracle.
- `ns8_ref.py` is the oracle until packaged implementation is proven equal by vectors + invariants.
- The system prioritizes conformance, reproducibility, and regression detection over predictive modeling.

## Public API Stability (v1)

Stable public imports are the names exported by `tonesight_ns8.__all__`:
- `compute_A`
- `resolve_to_seed`
- `validate_inputs`
- `tonesight_from_label`
- `tonesight_from_llm_labels`
- `tonesight_from_vad`
- `tonesight_from_vad_batch`
- `tonesight_receipt_from_segment`
- `attach_tonesight_to_segment`
- `Route`
- `ToneReceipt`
- `SegmentRecord`
- `SpeakerSummary`
- `SessionSummary`
- `summarize_speaker`
- `summarize_session`
- `run_eval`
- `log_eval_to_mlflow`
- `run_compare`
- `run_eval_compare`
- `run_gate`
- `run_canary`
- `run_triage`
- `run_bundle`
- `run_incident`
- `run_trend`
- `new_stream_state`
- `snapshot_stream_state`
- `run_stream_update`
- `run_report`
- `run_data_lint`
- `run_release_check`
- `run_benchmark_suite`
- `run_index`
- `run_index_json`
- `run_ui_package`
 - `run_live_capture`
 - `run_live_replay`
 - `run_live_verify`
 - `redact_text`
 - `redact_live_event`
 - `run_retention_purge`
- `register_mapping`
- `get_mapping`
- `list_mappings`
- `get_default_mapping`
- `get_default_mapping_id`

Internal/non-stable modules (no backward-compatibility guarantee in v1):
- `tonesight_ns8.defaults_schema`
- `tonesight_ns8.defaults`
- `tonesight_ns8.eval_runner` (module path)
- `tonesight_ns8.eval_compare_runner` (module path)
- `tonesight_ns8.compare_runner` (module path)

Policy:
- Prefer importing stable functions from package root (`import tonesight_ns8 as ts`).
- Treat module-level helper functions as implementation details unless explicitly listed as stable.

Canonical telemetry identity policy:
- `docs/CANONICAL_ID_POLICY.md`
- live compare/gate compatibility details: `docs/LIVE_COMPATIBILITY.md`

## Exceptions

### `InvalidInput`

Raised when strict input validation fails, including:
- invalid family
- out-of-range `r`, `c`, `k`
- invalid `N`

## Current Functions

Primary package functions:
- `compute_A(...)`
- `resolve_to_seed(...)`
- `tonesight_from_label(...)`
- `tonesight_from_llm_labels(...)`
- `tonesight_from_vad(...)`
- `tonesight_from_vad_batch(...)`

### `ns8_A(family: str, r: int, c: int, k: int, n: int = 8) -> int`

Computes deterministic NS8 anchor `A`.

Parameters:

| Name | Type | Description |
|---|---|---|
| `family` | `str` | One of `TLF, TRF, BLF, BRF, TRB, TLB, BLB, BRB` |
| `r` | `int` | Row index in `1..8` |
| `c` | `int` | Column index in `1..8` |
| `k` | `int` | Key index in `1..8` |
| `n` | `int` | Lattice size, must be `8` in v1 |

Returns:
- `int` in `1..8`

Raises:
- `InvalidInput`

Example:

```python
from ns8_ref import ns8_A

print(ns8_A("TRF", 6, 4, 3))
```

### `ns8_route(family: str, r: int, c: int, k: int, n: int = 8) -> Route`

Resolves a derived family call into canonical seed routing.

Returns:
- `Route(seed_family, r_prime, c_prime)`

Raises:
- `InvalidInput`

Example:

```python
from ns8_ref import ns8_route

route = ns8_route("BRB", 1, 7, 3)
print(route.seed_family, route.r_prime, route.c_prime)
```

### `wrapN(x: int, n: int = 8) -> int`

Mathematical wrap helper for internal NS8 math.

### `H(c: int, n: int = 8) -> int`

Horizontal mirror transform.

### `V(r: int, n: int = 8) -> int`

Vertical mirror transform.

### `compute_A(family: str, r: int, c: int, k: int, N: int = 8) -> int`

Package wrapper over oracle anchor computation with strict validation.

### `resolve_to_seed(family: str, r: int, c: int, k: int, N: int = 8) -> tuple[str, int, int, int]`

Package wrapper for canonical seed route resolution.

## Mapping Interface (Pre-1.0 Scaffold)

ToneSight now exposes a deterministic mapping registry so NS8 is a default adapter, not a hardcoded-only path.

Built-in default:
- `mapping_id="ns8"`

Public helpers:
- `register_mapping(mapping_id, adapter, set_default=False)`
- `get_mapping(mapping_id)`
- `list_mappings()`
- `get_default_mapping()`
- `get_default_mapping_id()`

Adapter contract:
- `name`, `spec_version`, `n`, `families`
- `validate_inputs(family, r, c, k, N=8)`
- `resolve_to_seed(family, r, c, k, N=8) -> (seed_family, r_prime, c_prime, k)`
- `compute_A(family, r, c, k, N=8) -> int`

Example adapter:
- `tonesight_ns8.mapping_examples.TLFConstantMappingAdapter`
- minimal plugin reference for registry integration and conformance testing

Current wrappers support optional `mapping_id`:
- `tonesight_from_label(..., mapping_id="ns8")`
- `tonesight_from_vad(..., mapping_id="ns8")`
- `tonesight_from_llm_labels(..., mapping_id="ns8")`
- `tonesight_from_vad_batch(..., mapping_id="ns8")`
- `tonesight_receipt_from_segment(..., mapping_id="ns8")`
- `attach_tonesight_to_segment(..., mapping_id="ns8")`

CLI support:
- `encode ... --mapping ns8`
- `decode ... --mapping ns8`
- `stream-update --segments-json <segments.json> [--state-in <state.json>] [--state-out <state.json>] [--session-id <id>]`
- `live-capture --events <path>`
- `live-replay --capture <capture_dir_or_events_jsonl> [--adapter <live_adapter_id>] [--require-pinned-model-identity]`
- `live-verify --capture <capture_dir_or_events_jsonl> [--adapter <live_adapter_id>] [--require-pinned-model-identity]`
- `canary --capture <capture_dir_or_events_jsonl>`
- `incident --run-a <run_dir> --run-b <run_dir>`
- `report --run-b <run_dir> [--run-a <run_dir>]`
- `data-lint --dataset <jsonl_path>`
- `release-check --goldset <jsonl_path> --taxonomy <taxonomy_path>`

Conformance harness:
- `tests/mapping_conformance.py` provides reusable assertions for adapter determinism, route shape, anchor range, and invalid-input rejection.

## Analytics Functions

Derived metrics contract:
- normative formulas/semantics are defined in `docs/DERIVED_METRICS.md`

### `summarize_speaker(segments: list[SegmentRecord]) -> dict[str, SpeakerSummary]`

Computes deterministic speaker-level summaries from segment records.

Inputs:
- `segments`: list of `SegmentRecord`

Output:
- dictionary keyed by `speaker_id`, each value a `SpeakerSummary`
- includes:
  - `volatility`
  - `arousal_momentum` (`mean_momentum`, `positive_momentum_ratio`, `count_transitions`)
  - `tone_stability_index` (bounded `0..1`)

Determinism guarantees:
- stable sort by segment time/identity before aggregation
- stable result regardless of input ordering

### `summarize_session(session_id: str, segments: list[SegmentRecord], arousal_spike_threshold: int = 7, drift_window_k: int = 2) -> SessionSummary`

Computes deterministic session-level summary.

Inputs:
- `session_id`: stable session identifier
- `segments`: list of `SegmentRecord`
- `arousal_spike_threshold`: integer in `1..8`
- `drift_window_k`: integer `>= 1` selecting first/last boundary window size

Output:
- `SessionSummary` with centroid, distributions, and spike stats
- includes:
  - `spike_rate` (backward-compatible)
  - `spike_density` (alias of `spike_rate`)
  - `arousal_momentum`
  - `tone_stability_index`
  - drift metrics: `drift_v`, `drift_a`, `drift_d`, optional `drift_anchor`
  - resolved `drift_window_k` used for the calculation
  - cross-speaker `arousal_coupling` payload:
    - `coupling_score`
    - `count_pairs`
    - `alignment` metadata with deterministic policy and pair details

Determinism guarantees:
- stable sort before aggregation
- stable result regardless of input ordering

Minimal example:

```python
from tonesight_ns8.analytics import summarize_session, summarize_speaker
from tonesight_ns8.schema import SegmentRecord

segments = [
    SegmentRecord("seg_01", "spk_a", 0.0, 1.0, 6, 3, 4, ns8_A=2),
    SegmentRecord("seg_02", "spk_b", 1.1, 2.0, 4, 7, 5, ns8_A=6),
]

print(summarize_speaker(segments))
print(summarize_session("session_001", segments))
```

## Evaluation Runner

Runtime defaults note:
- defaults for eval paths/threshold are loaded from `config/defaults.json` via `tonesight_ns8.defaults`.
- schema is defined in `docs/DEFAULTS_SCHEMA.md`.

### `run_eval(goldset_path: str, *, out_root: str = "runs", taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json", threshold_l1: int = 3, calibration_path: str | None = None, capture_gpu: bool = False, mlflow_tracking_uri: str | None = None) -> dict`

These defaults are sourced from `config/defaults.json`.

Runs deterministic evaluation over JSONL anchors and writes artifacts:
- `runs/<run_id>/out.jsonl`
- `runs/<run_id>/eval_summary.json`
- `runs/<run_id>/report.html`
- `runs/<run_id>/receipt.json`

Returns:
- run metadata including `run_id`, `out_dir`, summary, and receipt.
- optional calibration override support (`calibration_path`)
- optional GPU snapshots (`capture_gpu=True`)
- optional MLflow logging (`mlflow_tracking_uri`)
- receipt includes reproducibility hashes: `taxonomy_hash`, `defaults_hash`
- receipt includes additive artifact schema field `receipt_schema_version`
- receipt may include additive provenance field `code_revision` (short git SHA) when available
- receipt includes `mlflow` block when MLflow logging is attempted (enabled run ID or non-fatal disabled reason)

### `log_eval_to_mlflow(*, tracking_uri: str | None, result: dict, out_dir: Path, threshold_l1: int, taxonomy_path: str, calibration_path: str | None) -> dict | None`

One-call helper for MLflow metrics/artifact logging from eval outputs.

Behavior:
- returns `None` when `tracking_uri` is unset/empty (no-op)
- returns `{"enabled": False, "reason": ...}` on import/runtime failures without raising
- returns `{"enabled": True, "run_id": ...}` on successful logging

`out.jsonl` per-row explainability fields:
- `delta_v`, `delta_a`, `delta_d` (absolute per-dimension target deltas)
- `compliance_l1` (`delta_v + delta_a + delta_d`)
- `threshold_margin` (`threshold_l1 - compliance_l1`)

`eval_summary.json` key fields:
- `summary_schema_version`
- `dataset_hash`
- `count_rows`, `threshold_l1`
- `pass_count`, `fail_count`, `pass_rate`, `fail_rate`
- `avg_l1`, `median_l1`, `p95_l1`, `max_l1`
- `count_with_gold_vad`, `count_without_gold_vad`
- `avg_accuracy_l1` (or `null` when no gold labels are present)
- `eval_duration_seconds`

Artifact compatibility contract checks:
- required field/type coverage and additive-field tolerance are enforced in `tests/test_artifact_schema_compatibility.py`

### `run_eval_compare(goldset_path: str, *, out_root: str = "runs", taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json", threshold_l1: int = 3, calibration_path: str | None = None, capture_gpu: bool = False, mlflow_tracking_uri: str | None = None, top_n: int = 10) -> dict`

These defaults are sourced from `config/defaults.json`.

Runs eval and then compares the new run against the most recent prior run with matching:
- `dataset_hash`
- `spec_version`
- `mapping_id`
- `mapping_version`
- `taxonomy_identity` (`taxonomy_hash` with path fallback)
- `calibration_identity`
- `defaults_schema_version`

Returns:
- `eval`: eval output payload
- `previous_run`: previous run path (or `null` when none exists)
- `incompatible_previous_runs`: skipped prior runs with explicit mismatch reasons
- `compare_skipped_reason`: `null` when compare executed; otherwise reason such as `no_prior_runs` or `no_compatible_prior_run`
- `compare`: compare output payload (or `null` on first run)

CLI trace metadata (`python -m tonesight_ns8.cli eval` and `eval-compare`):
- top-level `trace` object is included for operational reproducibility
- keys: `spec_version`, `dataset_hash`, `taxonomy_hash`, `defaults_hash`
- output remains JSON and backward-compatible (existing fields retained)

### `run_compare(run_a: str, run_b: str, *, top_n: int = 10, distance_mode: str = "l1", write_artifact: bool = False, require_dataset_match: bool = True, require_pinned_model_identity: bool = False) -> dict`

Compares two deterministic eval runs and computes regression deltas.

Required inputs in each run directory:
- `eval_summary.json`
- `out.jsonl`
- `receipt.json`

Computed outputs:
- delta `pass_rate`
- delta `avg_l1`
- delta `p95_l1`
- `distance_mode` (`l1` or `topology`)
- deterministic trend labels (`improved`, `regressed`, `unchanged`) for each core delta metric
- per-label delta summary (when label present)
- row coverage (`count_common_ids`, `count_only_in_a`, `count_only_in_b`)
- regression coverage (`regression_count_total`, requested/returned `top_n`, truncation flag)
- top regressions by L1 increase (stable sort by delta desc, then `id`)
- top regression entries include `delta_v`, `delta_a`, `delta_d` when available
- top regression entries include `distance_a`, `distance_b`, `delta_distance`

Distance modes:
- `l1` (default): per-row distance is `compliance_l1`
- `topology`: per-row distance is NS8 anchor ring distance between `pred_vad` and `target_vad`; falls back to `compliance_l1` when anchor inputs are missing

Compatibility behavior:
- always requires matching `spec_version`
- requires matching `dataset_hash` when `require_dataset_match=True` (default)
- allows dataset hash mismatch when `require_dataset_match=False` (used by gate flows that explicitly disable dataset matching)
- optionally enforces pinned-model identity when `require_pinned_model_identity=True`

Optional artifact write (`write_artifact=True`):
- `runs/<runB>/comparisons/<runA>/compare_summary.json`
- `runs/<runB>/comparisons/<runA>/compare_report.html`

### `run_gate(run_a: str, run_b: str, *, profile: str | None = None, gate_profiles_path: str = "config/gate_profiles.json", min_pass_rate_delta: float | None = None, max_avg_l1_delta: float | None = None, max_p95_l1_delta: float | None = None, require_pinned_model_identity: bool | None = None, top_n: int = 10, require_dataset_match: bool = True) -> dict`

Runs deterministic CI gate checks over compare deltas.

Compatibility checks:
- `spec_version`
- `mapping_id`
- `mapping_version`
- `taxonomy_identity` (`taxonomy_hash` with path fallback)
- `calibration_identity`
- `defaults_schema_version`
- optional `dataset_hash` check (`require_dataset_match`)
- optional pinned-model identity check (`require_pinned_model_identity`)

Decision semantics:
- `decision = "passed"` -> `exit_code = 0`
- `decision = "regressed"` -> `exit_code = 2`
- `decision = "incompatible"` -> `exit_code = 3`

Threshold checks:
- fail if `delta_pass_rate < min_pass_rate_delta`
- fail if `delta_avg_l1 > max_avg_l1_delta`
- fail if `delta_p95_l1 > max_p95_l1_delta`

Gate profiles:
- profile config lives at `config/gate_profiles.json`
- select with `profile="<name>"`
- explicit threshold args override selected profile values
- bundled `coding_agent_drift` profile enables `require_pinned_model_identity=true`
- bundled `coding_agent_drift` profile also includes optional behavioral deltas:
  - `max_language_mismatch_rate_delta`
  - `max_verbosity_bin_mean_delta`
  - `min_tests_presence_rate_delta`
  - `min_tool_call_rate_delta`

### `run_canary(capture: str, *, baseline_out_root: str = "runs/canary/baseline", candidate_out_root: str = "runs/canary/candidate", baseline_taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json", candidate_taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json", baseline_threshold_l1: int = 3, candidate_threshold_l1: int = 3, shadow_strict: str = "quarantine", redact: bool = True, top_n: int = 10, profile: str | None = None, gate_profiles_path: str = "config/gate_profiles.json", min_pass_rate_delta: float | None = None, max_avg_l1_delta: float | None = None, max_p95_l1_delta: float | None = None, allow_dataset_mismatch: bool = False) -> dict`

Runs baseline/candidate replay over the same capture and returns a gate decision bundle.

Returns:
- baseline replay result
- candidate replay result
- `compare_summary` (from gate/compare)
- `gate_result` (full gate payload)
- `exit_code` passthrough from gate result

### `run_triage(run_b: str, *, run_a: str | None = None, top_n: int = 50, score: str = "compliance_l1", output_format: str = "jsonl", out_path: str | None = None) -> dict`

Creates deterministic triage exports from one run or a run pair.

Modes:
- single-run mode (`run_b` only)
- diff mode (`run_a` + `run_b`)

Ranking:
- deterministic sort by selected `score` (descending), then `id` (ascending)
- default `score = "compliance_l1"`

Exports:
- `output_format = "jsonl"` or `"csv"`
- includes rationale fields such as `delta_v`, `delta_a`, `delta_d`, `threshold_margin`, `label`, and `tags`

### `run_bundle(run_b: str, *, run_a: str | None = None, out_path: str | None = None, include_source_paths: bool = False) -> dict`

Creates a deterministic forensics bundle ZIP for a run and optional compare pair.

Run-only bundle includes:
- `run/receipt.json`
- `run/eval_summary.json`
- `run/report.html`
- `run/out.jsonl`
- `manifest.json` (hashes/sizes for included files)

Compare pair mode (`run_a` provided) additionally includes:
- `compare/compare_summary.json`
- `compare/compare_report.html`

Determinism notes:
- stable archive member ordering
- fixed ZIP timestamps
- manifest is canonical JSON with deterministic ordering

External-safe defaults:
- `include_source_paths=False` omits host filesystem paths from manifest entries
- set `include_source_paths=True` only for internal/debug bundles

### `run_incident(run_a: str, run_b: str, *, top_n: int = 50, triage_score: str = "delta_compliance_l1", triage_format: str = "jsonl", include_source_paths: bool = False, report_path: str | None = None) -> dict`

Generates deterministic incident response artifacts for a baseline/candidate run pair.

Included outputs:
- compare summary/report paths
- triage export path
- forensics bundle path
- markdown incident template path

### `run_report(run_b: str, *, run_a: str | None = None, out_path: str | None = None, top_n: int = 10, profile: str | None = None, gate_profiles_path: str = "config/gate_profiles.json", min_pass_rate_delta: float | None = None, max_avg_l1_delta: float | None = None, max_p95_l1_delta: float | None = None, require_dataset_match: bool = True) -> dict`

Builds a deterministic static JSON report from existing run artifacts.

Inputs:
- `run_b`: required candidate/current run directory
- `run_a`: optional baseline run directory for compare/gate highlights

Output:
- writes report JSON under `<run_b>/reports/` by default
- writes deterministic transition heatmap JSON under `<run_b>/reports/` for single-run and compare views
- includes:
  - run-B KPI snapshot (`count_rows`, `pass_rate`, `avg_l1`, `p95_l1`)
  - reproducibility metadata from receipt (`spec_version`, hashes, mapping IDs, code revision when present)
  - compare highlights (`metrics`, regression coverage, top regressions) when `run_a` is provided
  - gate summary (`decision`, thresholds, violations, incompatibilities, exit code) when `run_a` is provided
  - additive `coding_agent_drift` slice when coding-agent rows are present

Determinism guarantees:
- consumes existing artifacts only
- uses stable ordering and canonical JSON (`sort_keys=True`)
- repeated runs with unchanged inputs produce byte-stable report files

### `run_data_lint(dataset_path: str, *, out_path: str | None = None) -> dict`

Runs deterministic structural/data-quality lint checks over a JSONL dataset.

Checks include:
- malformed JSON rows
- missing/duplicate IDs
- invalid VAD bins (`target_vad` required; `gold_vad` when present)
- invalid tags shape/items

Output:
- machine-readable summary with:
  - `passed`
  - `row_count_total`, `row_count_valid`
  - `violation_count`, `violations_by_code`
  - ordered `violations` list (`line`, `code`, `message`)
  - `exit_code` (`0` clean, `2` violations)
- optional summary artifact write via `out_path`

### `run_release_check(*, goldset_path: str = "data/goldset.jsonl", taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json", gate_profiles_path: str = "config/gate_profiles.json", out_path: str | None = None) -> dict`

Runs deterministic pre-release gate orchestration and returns a machine-readable decision payload.

Required checks (deterministic order):
- `dataset_lint`
- `taxonomy_load`
- `gate_profiles_config`
- `nosec_policy`

Output:
- per-check pass/fail status with details
- top-level `decision`, `failed_checks`, and CI-ready `exit_code`
- `exit_code = 0` when all checks pass
- `exit_code = 2` when one or more checks fail

### `run_trend(out_root: str, *, group_by: str | None = None, out_path: str | None = None) -> dict`

Aggregates deterministic run-over-run trend summaries from historical run artifacts.

Inputs:
- run discovery from `out_root/*` directories containing:
  - `eval_summary.json`
  - `receipt.json`
  - `out.jsonl`

Output:
- writes `trend_summary.json` (default path: `<out_root>/trend_summary.json`)

### `run_live_capture(events_path: str, *, out_root: str = "runs") -> dict`

Validates LiveEvent JSONL and writes deterministic capture artifacts.

Writes:
- `<out_root>/captures/<capture_id>/events.raw.jsonl`
- `<out_root>/captures/<capture_id>/capture_manifest.json`

Returns:
- `capture_id`, `capture_hash`, `capture_dir`, `event_count`, `manifest_path`

### `run_live_replay(capture: str, *, out_root: str = "runs", taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json", threshold_l1: int = 3, shadow_strict: str = "quarantine", redact: bool = True, adapter: str = "upstream_signal", require_pinned_model_identity: bool = False) -> dict`

Replays a validated capture into standard deterministic run artifacts.

Writes:
- `<out_root>/<run_live_id>/out.jsonl`
- `<out_root>/<run_live_id>/eval_summary.json`
- `<out_root>/<run_live_id>/report.html`
- `<out_root>/<run_live_id>/receipt.json`
- `<out_root>/<run_live_id>/quarantine.jsonl` (when quarantine mode and invalid events exist)

Returns:
- run metadata, summary, receipt, and shadow policy result
- summary includes additive artifact schema field `summary_schema_version`
- receipt includes additive artifact schema field `receipt_schema_version`
- includes deterministic `redaction_summary` in summary/receipt when redaction is enabled
- receipt may include additive provenance field `code_revision` (short git SHA) when available
- with `adapter="coding_agent"`:
  - rows include deterministic `coding_agent_features` and `coding_agent_bins`
  - receipt includes `adapter_id`, `adapter_version`, `capture_schema_version`
  - receipt includes pinned-model identity fields when available (`provider`, `model_tag`, `model_digest`/`model_version`, `generation_settings`)
  - when `require_pinned_model_identity=True`, replay fails fast unless provider/model identity/generation settings are present

### `run_live_verify(capture: str, *, out_root: str = "runs", taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json", threshold_l1: int = 3, shadow_strict: str = "quarantine", redact: bool = True, adapter: str = "upstream_signal", require_pinned_model_identity: bool = False) -> dict`

Runs `run_live_replay` twice over the same capture and compares artifact hashes.

Returns:
- `stable` boolean
- artifact hash maps for first/second replay
- `mismatched_artifacts`
- `exit_code` (`0` on stable output, `2` on mismatch)

### `redact_text(text: str | None) -> tuple[str | None, dict[str, int]]`

Deterministically redacts configured token classes (`EMAIL`, `PHONE`, `SSN`) using fixed replacement tokens.

### `redact_live_event(event: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]`

Returns a redacted copy of a live event and aggregated token counts across `text` and `segments[].text`.

### `run_retention_purge(*, out_root: str, older_than_days: int, dry_run: bool = True, include_bundles: bool = False, include_captures: bool = False) -> dict`

Deterministic retention cleanup helper used by CLI `purge`.

Behavior:
- default dry-run mode
- skips capture directories unless explicitly included
- skips run directories containing `bundles/` unless explicitly included
- includes ordered run list with:
  - `pass_rate`, `avg_l1`, `p95_l1`
  - run-over-run deltas against previous compatible run
  - `delta_skipped_reason` when previous run is incompatible (`dataset_hash`/`spec_version` mismatch)

Grouping (optional):
- `group_by` aggregates per-run stats from row metadata fields (for example `source`, `agent`, `prompt_id`)
- group metrics include `count`, `avg_l1`, and `fail_rate`

### `new_stream_state(*, session_id: str, arousal_spike_threshold: int = 7, drift_window_k: int = 2) -> dict`

Creates empty deterministic rolling state object for stream updates.

### `snapshot_stream_state(state: dict) -> dict`

Builds deterministic session snapshot from current stream state contents.

### `run_stream_update(*, session_id: str | None = None, state_path: str | None = None, out_state_path: str | None = None, segments: list[SegmentRecord | dict] | None = None, segments_path: str | None = None, arousal_spike_threshold: int = 7, drift_window_k: int = 2) -> dict`

Appends deterministic segment batch to rolling state and returns updated snapshot.

Behavior:
- initialize state from `session_id` when `state_path` is not provided
- append batch from `segments` or `segments_path`
- return updated in-memory `state` and deterministic `snapshot`
- optionally persist state JSON via `out_state_path` (or overwrite `state_path`)

### `run_index(out_root: str, *, out_path: str | None = None) -> dict`

Builds deterministic run metadata index with one JSON line per discovered run.

Discovery rules:
- includes directories containing:
  - `receipt.json`
  - `eval_summary.json`
  - `out.jsonl`

Output:
- default path: `<out_root>/index.jsonl`
- rows are sorted by `run_id`
- each row includes:
  - run IDs and hash/version metadata
  - `profile_label`, `source_label`, and row-derived `source_labels`
  - artifact pointers (`out_jsonl`, `eval_summary_json`, `report_html`, `receipt_json`)

### `run_index_json(out_root: str, *, index_jsonl_path: str | None = None, out_path: str | None = None) -> dict`

Builds deterministic JSON array index for read-only UI clients from `index.jsonl`.

Behavior:
- reads `index_jsonl_path` or default `<out_root>/index.jsonl`
- writes deterministic JSON array to `<out_root>/index.json` by default
- preserves run ordering by `run_id`
- performs no metric recomputation

CLI:
- `python -m tonesight_ns8.cli index-runs-json --out-root runs`
- `python tools/generate_run_index_json.py --out-root runs`

### `run_ui_package(out_root: str, *, out_path: str | None = None, include_source_paths: bool = False, include_raw_artifacts: bool = False) -> dict`

Builds deterministic ZIP package for local read-only UI demos.

Behavior:
- packages repo `ui/` and `server/` directories
- packages run artifacts under `runs/` from `out_root`
- ensures `index.jsonl` and `index.json` exist (generates deterministically when missing)
- excludes raw artifacts by default:
  - `out.jsonl`
  - `events.raw.jsonl`
  - `quarantine.jsonl`

Returns:
- `package_path`
- `file_count`
- `external_safe`
- deterministic `manifest`

CLI:
- `python -m tonesight_ns8.cli ui-package --out-root runs`
- `python -m tonesight_ns8.cli ui-package --out-root runs --out runs/demo_ui_package.zip`
- `python -m tonesight_ns8.cli ui-package --out-root runs --include-raw-artifacts` (internal-only)

## Static Artifact API (Server)

Server entrypoint:
- `python server/app.py --runs-root runs --host 127.0.0.1 --port 8081`

Default behavior:
- serves deterministic existing artifacts only.

Optional operator control-plane mode:
- enable with `--enable-pipeline`
- exposes `POST /api/pipeline/run` for deterministic orchestration of existing flows (`live-capture`, `live-replay`, optional `compare`/`gate`, `index-runs`, `index-runs-json`)
- does not authorize UI-side recomputation of metrics or hidden scoring paths

### `run_benchmark_suite(*, suite: str = "core", out_root: str = "runs", goldset_path: str = "data/goldset.jsonl", killer_profiles: list[str] | None = None, killer_seeds: list[int] | None = None, killer_primary_strength: float = 0.20, killer_sweep_strengths: list[float] | None = None, killer_sample_multiplier: int = 1, coding_baseline_events: str = "tests/fixtures/live_event.coding_agent.python.jsonl", coding_candidate_events: list[str] | None = None) -> dict`

Runs deterministic benchmark evidence suite and writes JSON artifacts.

Suite `core` artifacts:
- `<out_root>/benchmarks/core/noise_tolerance.json`
- `<out_root>/benchmarks/core/drift_injection.json`
- `<out_root>/benchmarks/core/model_swap_robustness.json`
- `<out_root>/benchmarks/core/baselines.json`
- `<out_root>/benchmarks/core/report.json`

Suite `killer_stability` artifacts:
- `<out_root>/benchmarks/killer_stability/evidence.json`
- `<out_root>/benchmarks/killer_stability/robustness_summary.json`
- `<out_root>/benchmarks/killer_stability/robustness_report.html`

Suite `coding_agent_drift` artifacts:
- `<out_root>/benchmarks/coding_agent_drift/evidence.json`
- `<out_root>/benchmarks/coding_agent_drift/report.json`
- includes deterministic `gate_ready` summaries for profile/gate consumption

Current supported suite:
- `core`
- `killer_stability`
- `coding_agent_drift`

CLI:
- `python -m tonesight_ns8.cli benchmark --suite core`
- `python -m tonesight_ns8.cli benchmark --suite killer_stability`
- `python -m tonesight_ns8.cli benchmark --suite killer_stability --killer-profiles default,oscillation_path,boundary_jitter,phase_flip_cycle --killer-seeds 0,1,2,3,4 --killer-primary-strength 0.2 --killer-sweep-strengths 0.05,0.1,0.15,0.2,0.3 --killer-sample-multiplier 2`
- `python -m tonesight_ns8.cli benchmark --suite coding_agent_drift --coding-baseline-events tests/fixtures/live_event.coding_agent.python.jsonl --coding-candidate-events tests/fixtures/live_event.coding_agent.typescript.jsonl,tests/fixtures/live_event.coding_agent.mismatch.jsonl`

### `tonesight_from_label(label: str, family: str, r: int, c: int, k: int, taxonomy_path: str) -> dict`

Behavior:
- load taxonomy
- resolve label to VAD
- compute NS8 anchor
- return deterministic JSON-serializable receipt

### `tonesight_from_vad(V: int, A: int, D: int, family: str, r: int, c: int, k: int) -> dict`

Behavior:
- use explicit VAD input
- compute NS8 anchor
- return deterministic JSON-serializable receipt

### `tonesight_from_vad_batch(rows: list[dict[str, int]], family: str, r: int, c: int, k: int) -> list[dict]`

Behavior:
- validates `rows` as an ordered list of `{V,A,D}` integer objects
- maps each row to a deterministic receipt using shared NS8 routing parameters
- preserves input order in output receipts

### `tonesight_from_llm_labels(labels: list[str], family: str, r: int, c: int, k: int, taxonomy_path: str) -> list[dict]`

Behavior:
- validates `labels` as an ordered list of non-empty strings
- resolves each label through taxonomy VAD mapping
- maps each resolved row to a deterministic receipt using shared NS8 routing parameters
- preserves input order in output receipts

## Behavioral Contract

- Math and routing are governed by `docs/SPEC_NS8.md`.
- Vectors in `vectors/ns8_test_vectors.json` are normative.
- Any behavior change requires spec + vector updates.
- Architect-level assurance mapping (axioms/invariants/traceability) is documented in `docs/NS8_CONTRACT_ASSURANCE.md`.
