# Segment Interface (Normative v1)

ToneSight NS8 does not implement speech segmentation or continuous VAD estimation.
This document defines the minimal segment fields expected by analytics and wrapper receipt generation.

## Required fields

```json
{
  "segment_id": "seg_001",
  "speaker_id": "spk_a",
  "start_sec": 0.0,
  "end_sec": 1.24,
  "vad": { "V": 6, "A": 3, "D": 4 }
}
```

## Optional fields

```json
{
  "text": "optional transcript text",
  "confidence": 0.92,
  "tone_label": "empathetic",
  "ns8": {
    "family": "TRF",
    "r": 6,
    "c": 4,
    "k": 3,
    "seed_family": "TLF",
    "r_prime": 6,
    "c_prime": 5,
    "A": 2
  }
}
```

## Constraints

- `segment_id`: stable string.
- `speaker_id`: stable string.
- `start_sec`, `end_sec`: numeric with `end_sec >= start_sec`.
- `vad.V`, `vad.A`, `vad.D`: integers in `1..8`.

## Determinism requirements

- Analytics must sort segments deterministically by time before computing metrics.
- Results must be stable regardless of input ordering.
- Invalid bins must be rejected (`1..8` only).

## Boundary rule

This interface does not define SER model behavior.
It defines only the post-estimation contract consumed by ToneSight NS8.
