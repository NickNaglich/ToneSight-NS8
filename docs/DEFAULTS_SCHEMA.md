# Defaults Schema (v1)

This document defines the normative schema for `config/defaults.json`.

## Required top-level fields

- `spec_version`: string
- `eval_defaults`: object
- `artifact_defaults`: object

## `eval_defaults` fields

- `out_root`: string
- `taxonomy_path`: string
- `threshold_l1`: integer
- `calibration_path`: string or `null`
- `capture_gpu`: boolean
- `mlflow_tracking_uri`: string or `null`

## `artifact_defaults` fields

- `vectors_path`: string
- `taxonomy_path`: string
- `goldset_path`: string

## Example

```json
{
  "spec_version": "1.0",
  "eval_defaults": {
    "out_root": "runs",
    "taxonomy_path": "taxonomy/tone_taxonomy.v1.json",
    "threshold_l1": 3,
    "calibration_path": null,
    "capture_gpu": false,
    "mlflow_tracking_uri": null
  },
  "artifact_defaults": {
    "vectors_path": "vectors/ns8_test_vectors.json",
    "taxonomy_path": "taxonomy/tone_taxonomy.v1.json",
    "goldset_path": "data/goldset.jsonl"
  }
}
```
