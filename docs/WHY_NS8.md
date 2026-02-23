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
- false-drift vs true-drift separation under a fixed 2x2 protocol (`C1..C4`)
- robustness under synthetic seed/profile perturbation sweeps

This repository does not claim psychological ground truth accuracy.
Killer benchmark outputs are synthetic benchmark evidence and should be interpreted as controlled protocol results.

Killer benchmark protocol (v0.2.1):
- `docs/BENCHMARK_KILLER_STABILITY.md`

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

6. Killer stability separation (v0.2.1 protocol)
- Source: `runs/benchmarks/killer_stability/evidence.json`
- Primary fields:
  - `distances.<method>.d_c1_c2`
  - `distances.<method>.d_c1_c3`
  - `distances.<method>.d_c2_c4`
  - `separation_ratios.<method>`

7. Killer stability robustness (v0.2.1 protocol)
- Source: `runs/benchmarks/killer_stability/robustness_summary.json`
- Primary fields:
  - `robustness_sweep.summary.wins_by_method`
  - `robustness_sweep.summary.ratio_stats_by_method.<method>.mean/std/min/max/p10/p50/p90`
  - `robustness_sweep.summary.absolute_criteria_pass_rate.<method>.*`
  - `robustness_sweep.summary.tonesight_loss_tag_counts`

## Reading Guidance

- Treat these benchmarks as operational evidence, not proofs of universal superiority.
- Compare methods under the same fixture and command invocation.
- For release notes, cite concrete artifact paths and specific metric fields.
