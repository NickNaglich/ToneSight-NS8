# Why NS8 (Evidence-Oriented)

This document explains why ToneSight uses NS8 as a deterministic mapping layer and how to evaluate that choice with reproducible artifacts.

## Claim Boundaries

Conformance guarantees (contract-level):
- deterministic mapping for fixed valid input
- strict validation and explicit errors for invalid input
- symmetry behavior pinned by vectors and invariants

Empirical evidence claims (benchmark-level):
- stability under small perturbations
- drift visibility under controlled injections
- model-swap robustness comparison vs simple baselines

This repository does not claim psychological ground truth accuracy.

## How To Reproduce Evidence

Run:

```bash
python -m tonesight_ns8.cli benchmark --suite core --out-root runs --goldset data/goldset.jsonl
```

Generated artifacts:
- `runs/benchmarks/core/report.json`
- `runs/benchmarks/core/noise_tolerance.json`
- `runs/benchmarks/core/drift_injection.json`
- `runs/benchmarks/core/model_swap_robustness.json`
- `runs/benchmarks/core/baselines.json`
- `runs/benchmarks/core/transition_coherence.json`

## Claim -> Artifact Mapping

1. Noise tolerance (small perturbations)
- Source: `runs/benchmarks/core/noise_tolerance.json`
- Primary fields:
  - `amplitudes.*.ns8.flip_rate`
  - `amplitudes.*.equal_width.flip_rate`
  - `amplitudes.*.quantile.flip_rate`

2. Drift injection sensitivity
- Source: `runs/benchmarks/core/drift_injection.json`
- Primary fields:
  - `scenarios.*.ns8.jsd`
  - `scenarios.*.equal_width.jsd`
  - `scenarios.*.quantile.jsd`
  - `scenarios.*.<method>.psi`

3. Model-swap robustness
- Source: `runs/benchmarks/core/model_swap_robustness.json`
- Primary fields:
  - `pairs.*.ns8.mismatch_rate`
  - `pairs.*.equal_width.mismatch_rate`
  - `pairs.*.quantile.mismatch_rate`
  - `pairs.*.<method>.avg_distance`

4. Baseline occupancy/distribution context
- Source: `runs/benchmarks/core/baselines.json`
- Primary fields:
  - `<method>.unused_states_rate`
  - `<method>.entropy_bits`
  - `distance_between_baselines.jsd_equal_vs_quantile`
  - `distance_between_baselines.psi_equal_vs_quantile`

5. Transition locality/coherence over ordered sequences
- Source: `runs/benchmarks/core/transition_coherence.json`
- Primary fields:
  - `base.<method>.mean_step_distance`
  - `base.<method>.local_step_ratio`
  - `base.<method>.coherence_score`
  - `scenarios.*.<method>.delta_vs_base.mean_step_distance_delta`
  - `scenarios.*.<method>.delta_vs_base.coherence_score_delta`

## Reading Guidance

- Treat these benchmarks as operational evidence, not proofs of universal superiority.
- Compare methods under the same fixture and command invocation.
- For release notes, cite concrete artifact paths and specific metric fields.
