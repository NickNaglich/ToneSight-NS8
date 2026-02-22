# Derived Metrics Contract (0.1.7+)

This document defines the normative deterministic contract for derived analytics metrics.

Scope note:
- ToneSight metrics are deterministic conformance telemetry over discrete VAD bins.
- They are not raw-audio inference and not emotion ground-truth claims.

## Deterministic Rules

Ordering:
- all segment series are normalized by `(start_sec, end_sec, segment_id, speaker_id)` before sequence metrics

Rounding:
- derived floating metrics use fixed rounding precision of 6 decimals where implemented as derived values
- base ratio fields retained for backward compatibility (for example `spike_rate`) preserve existing behavior

Validation:
- V/A/D bins must be integer `1..8`
- invalid segment bins fail fast

## Speaker Metrics

### `arousal_momentum.mean_momentum`

Formula:
- for ordered speaker segments, compute `delta_i = A_i - A_(i-1)` for `i>=1`
- `mean_momentum = mean(delta_i)`

Edge cases:
- fewer than 2 segments -> `0.0`

### `arousal_momentum.positive_momentum_ratio`

Formula:
- `positive_momentum_ratio = count(delta_i > 0) / count(delta_i)`

Edge cases:
- fewer than 2 segments -> `0.0`

### `arousal_momentum.count_transitions`

Formula:
- `count_transitions = max(count_segments - 1, 0)`

### `tone_stability_index`

Formula:
- `volatility = mean(|A_i - A_(i-1)|)` across ordered segments
- `tone_stability_index = clamp(1 - (volatility / 7), 0, 1)`

Rationale:
- `7` is max per-step arousal delta in NS8 (`1..8`)

Edge cases:
- fewer than 2 segments -> `1.0`

## Session Metrics

### Drift (`drift_v`, `drift_a`, `drift_d`, `drift_anchor`)

Windowing:
- `k = min(max(requested_k, 1), count_segments)` when count > 0
- `k = 0` when session empty
- start window: first `k` ordered segments
- end window: last `k` ordered segments

Formulas:
- `drift_v = mean(V_end_window) - mean(V_start_window)`
- `drift_a = mean(A_end_window) - mean(A_start_window)`
- `drift_d = mean(D_end_window) - mean(D_start_window)`
- `drift_anchor` same for `ns8_A` when both windows have anchor values; else `null`

Edge cases:
- empty session -> drifts `0.0`, `drift_anchor=null`
- short sessions may overlap deterministically

### Spike density

Formula:
- `spike_density = spike_count / count_segments` (alias of `spike_rate`)

Backward compatibility:
- `spike_rate` remains present

### Cross-speaker arousal coupling

Alignment policy:
- deterministic per-speaker arousal series from normalized ordering
- for each speaker pair, align by index truncation to `min(len(series_a), len(series_b))`
- valid pair correlation requires:
  - at least 2 aligned points
  - non-zero variance for both aligned series

Outputs:
- `arousal_coupling.coupling_score`: weighted mean Pearson correlation over valid pairs (or `null`)
- `arousal_coupling.count_pairs`: total aligned points used by valid correlations
- `arousal_coupling.alignment`:
  - `policy = "speaker_pair_index_alignment"`
  - `speaker_count`
  - `speaker_pair_count`
  - `pair_details[]` with `speaker_a`, `speaker_b`, `aligned_count`, `coupling_score`
  - `insufficient_data`
