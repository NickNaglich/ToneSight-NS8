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
- `tonesight_from_vad`
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
- `run_compare`
- `run_eval_compare`

Internal/non-stable modules (no backward-compatibility guarantee in v1):
- `tonesight_ns8.defaults_schema`
- `tonesight_ns8.defaults`
- `tonesight_ns8.eval_runner` (module path)
- `tonesight_ns8.eval_compare_runner` (module path)
- `tonesight_ns8.compare_runner` (module path)

Policy:
- Prefer importing stable functions from package root (`import tonesight_ns8 as ts`).
- Treat module-level helper functions as implementation details unless explicitly listed as stable.

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
- `tonesight_from_vad(...)`

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

## Analytics Functions

### `summarize_speaker(segments: list[SegmentRecord]) -> dict[str, SpeakerSummary]`

Computes deterministic speaker-level summaries from segment records.

Inputs:
- `segments`: list of `SegmentRecord`

Output:
- dictionary keyed by `speaker_id`, each value a `SpeakerSummary`

Determinism guarantees:
- stable sort by segment time/identity before aggregation
- stable result regardless of input ordering

### `summarize_session(session_id: str, segments: list[SegmentRecord], arousal_spike_threshold: int = 7) -> SessionSummary`

Computes deterministic session-level summary.

Inputs:
- `session_id`: stable session identifier
- `segments`: list of `SegmentRecord`
- `arousal_spike_threshold`: integer in `1..8`

Output:
- `SessionSummary` with centroid, distributions, and spike stats

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
- `runs/<run_id>/receipt.json`

Returns:
- run metadata including `run_id`, `out_dir`, summary, and receipt.
- optional calibration override support (`calibration_path`)
- optional GPU snapshots (`capture_gpu=True`)
- optional MLflow logging (`mlflow_tracking_uri`)

`eval_summary.json` key fields:
- `count_rows`, `threshold_l1`
- `pass_count`, `fail_count`, `pass_rate`, `fail_rate`
- `avg_l1`, `median_l1`, `p95_l1`, `max_l1`
- `count_with_gold_vad`, `count_without_gold_vad`
- `avg_accuracy_l1` (or `null` when no gold labels are present)

### `run_eval_compare(goldset_path: str, *, out_root: str = "runs", taxonomy_path: str = "taxonomy/tone_taxonomy.v1.json", threshold_l1: int = 3, calibration_path: str | None = None, capture_gpu: bool = False, mlflow_tracking_uri: str | None = None, top_n: int = 10) -> dict`

These defaults are sourced from `config/defaults.json`.

Runs eval and then compares the new run against the most recent prior run with the same dataset hash.

Returns:
- `eval`: eval output payload
- `previous_run`: previous run path (or `null` when none exists)
- `compare`: compare output payload (or `null` on first run)

### `run_compare(run_a: str, run_b: str, *, top_n: int = 10, write_artifact: bool = False) -> dict`

Compares two deterministic eval runs and computes regression deltas.

Required inputs in each run directory:
- `eval_summary.json`
- `out.jsonl`
- `receipt.json`

Computed outputs:
- delta `pass_rate`
- delta `avg_l1`
- delta `p95_l1`
- deterministic trend labels (`improved`, `regressed`, `unchanged`) for each core delta metric
- per-label delta summary (when label present)
- row coverage (`count_common_ids`, `count_only_in_a`, `count_only_in_b`)
- regression coverage (`regression_count_total`, requested/returned `top_n`, truncation flag)
- top regressions by L1 increase (stable sort by delta desc, then `id`)

Optional artifact write (`write_artifact=True`):
- `runs/<runB>/comparisons/<runA>/compare_summary.json`

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

## Behavioral Contract

- Math and routing are governed by `docs/SPEC_NS8.md`.
- Vectors in `vectors/ns8_test_vectors.json` are normative.
- Any behavior change requires spec + vector updates.
