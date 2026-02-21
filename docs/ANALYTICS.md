# Analytics (v1)

ToneSight NS8 analytics are deterministic, dependency-light summaries over segments.

## Inputs

- Segment records with `speaker_id`, time bounds, VAD bins, and optional NS8 anchor.
- Session identifier supplied to session summarization.

## Metrics

### Speaker centroid

For each speaker:
- `mean(V)`, `mean(A)`, `mean(D)` over that speaker's segments.

### Speaker volatility

For each speaker:
- Sort that speaker's segments by `(start_sec, end_sec, segment_id)`.
- Compute mean absolute change in arousal between consecutive segments:
- `volatility = mean(|A_i - A_(i-1)|)`.

### Arousal momentum

For each speaker/session:
- sort segments by deterministic order
- compute signed arousal deltas `A_(i+1) - A_i`
- expose:
  - `mean_momentum`
  - `positive_momentum_ratio`
  - `count_transitions`

### Tone stability index

Bounded deterministic index derived from normalized arousal volatility:

- `tone_stability_index = clamp(1 - (volatility / 7), 0, 1)`

Notes:
- `7` is the maximum possible per-step arousal delta in NS8 bins (`1..8`)
- values closer to `1` indicate more stable tone

### Distributions

Histograms (length 8 each):
- `V` bins
- `A` bins
- `D` bins
- NS8 anchor `A` bins (when anchor present)

### Session tone profile

Across all session segments:
- aggregate centroid (`mean(V), mean(A), mean(D)`)
- aggregate distributions

### Session drift metrics

Directional shift between start/end boundary windows:
- `drift_v`
- `drift_a`
- `drift_d`
- `drift_anchor` (optional; included when anchor values are present in both windows)

Window policy:
- use first `k` and last `k` segments from deterministic session ordering
- `k` is configured via `drift_window_k` (default `2`)
- bounded behavior:
  - empty session: `k=0`, drifts are `0.0` (`drift_anchor=null`)
  - short sessions: `k=min(requested_k, count_segments)`; overlap is deterministic

### Arousal spike detection

Default threshold:
- `arousal_spike_threshold = 7`

Outputs:
- `spike_count`
- `spike_rate = spike_count / count_segments`
- `spike_density` (alias of `spike_rate`, preserved for backward compatibility)
- `spike_segments` (ordered list of segment IDs meeting threshold)

## Determinism guarantees

- Segment ordering is normalized before metric computation.
- Results are stable regardless of input order.
- Invalid bins are rejected.
- Derived metric floats are rounded to fixed precision for stable JSON output.

## Output examples

Speaker summary (shape):

```json
{
  "speaker_id": "spk_a",
  "count_segments": 3,
  "vad_centroid": [6.3333, 3.0, 3.6667],
  "volatility": 1.5,
  "arousal_momentum": {
    "mean_momentum": 0.5,
    "positive_momentum_ratio": 0.5,
    "count_transitions": 2.0
  },
  "tone_stability_index": 0.785714,
  "distributions": {
    "V": [0, 0, 0, 0, 0, 2, 1, 0],
    "A": [0, 1, 1, 1, 0, 0, 0, 0],
    "D": [0, 0, 1, 2, 0, 0, 0, 0],
    "anchor_A": [1, 1, 1, 0, 0, 0, 0, 0]
  }
}
```

Session summary (shape):

```json
{
  "session_id": "session_001",
  "count_segments": 6,
  "vad_centroid": [5.1667, 5.0, 4.5],
  "distributions": {
    "V": [0, 0, 1, 1, 1, 2, 1, 0],
    "A": [0, 1, 1, 1, 0, 1, 1, 1],
    "D": [0, 0, 1, 2, 2, 1, 0, 0],
    "anchor_A": [1, 1, 1, 1, 0, 1, 0, 1]
  },
  "drift_window_k": 2,
  "drift_v": -0.5,
  "drift_a": 1.0,
  "drift_d": 0.5,
  "drift_anchor": 1.5,
  "spike_count": 2,
  "spike_rate": 0.3333,
  "spike_density": 0.3333,
  "arousal_momentum": {
    "mean_momentum": 1.0,
    "positive_momentum_ratio": 0.6,
    "count_transitions": 5.0
  },
  "tone_stability_index": 0.6,
  "spike_segments": ["seg_02", "seg_06"]
}
```
