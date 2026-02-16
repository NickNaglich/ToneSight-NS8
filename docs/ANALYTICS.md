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

### Arousal spike detection

Default threshold:
- `arousal_spike_threshold = 7`

Outputs:
- `spike_count`
- `spike_rate = spike_count / count_segments`
- `spike_segments` (ordered list of segment IDs meeting threshold)

## Determinism guarantees

- Segment ordering is normalized before metric computation.
- Results are stable regardless of input order.
- Invalid bins are rejected.

## Output examples

Speaker summary (shape):

```json
{
  "speaker_id": "spk_a",
  "count_segments": 3,
  "vad_centroid": [6.3333, 3.0, 3.6667],
  "volatility": 1.5,
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
  "spike_count": 2,
  "spike_rate": 0.3333,
  "spike_segments": ["seg_02", "seg_06"]
}
```
