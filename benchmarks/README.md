# Benchmark Harness

This folder provides deterministic benchmark scripts used for OSS evidence.

Core suite components:
- `noise_tolerance.py`
- `drift_injection.py`
- `model_swap_robustness.py`
- `baselines.py`

Run the full suite through CLI:

```bash
python -m tonesight_ns8.cli benchmark --suite core
```

Artifacts are written to:
- `runs/benchmarks/core/noise_tolerance.json`
- `runs/benchmarks/core/drift_injection.json`
- `runs/benchmarks/core/model_swap_robustness.json`
- `runs/benchmarks/core/baselines.json`
- `runs/benchmarks/core/report.json`

