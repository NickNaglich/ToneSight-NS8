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
  - `robustness_sweep.summary.by_profile.<profile>.*`

## Scenario Family Evidence Map

Use per-profile robustness blocks to compare ToneSight vs baselines across scenario families.

| Scenario family | Purpose | Compare fields |
|---|---|---|
| `default` | baseline mixed drift + model swap | `robustness_sweep.summary.by_profile.default.ratio_stats_by_method.*` |
| `oscillation_path` | alternating transition-heavy path shifts | `robustness_sweep.summary.by_profile.oscillation_path.ratio_stats_by_method.*` |
| `temporal_ramp` | gradual time-ordered drift | `robustness_sweep.summary.by_profile.temporal_ramp.ratio_stats_by_method.*` |
| `subgroup_mixture` | deterministic subgroup drift concentration | `robustness_sweep.summary.by_profile.subgroup_mixture.ratio_stats_by_method.*` |
| `boundary_jitter` | bin-boundary quantization sensitivity stress | `robustness_sweep.summary.by_profile.boundary_jitter.ratio_stats_by_method.*` |
| `phase_flip_cycle` | cyclic regime direction flips by phase block | `robustness_sweep.summary.by_profile.phase_flip_cycle.ratio_stats_by_method.*` |

Pseudo-real trace demonstration fixture:
- `data/pseudo_real_trace.jsonl`
- command:
  `python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/pseudo_real_trace.jsonl --killer-profiles default,phase_flip_cycle --killer-seeds 0,1 --killer-sweep-strengths 0.1,0.2`

Current reproducible snapshot (`N=250`, `runs/benchmarks/killer_stability/robustness_summary.json`):
- ToneSight: wins `10/20`, ratio stats `mean=1.037`, `p50=0.867`, `p90=1.644`, `max=1.789`
- ToneSight pass-rates: `separation_ratio_lt_1=0.70`, `true_drift_gt_false_drift=0.70`, `both_ratio_and_true_gt_false=0.70`
- loss tags: `occupancy_dominated_shift=5`, `ramp_mild_or_late=5`, `transition_signal_weak=3`, `true_drift_not_dominant=3`

Larger-`N` subset (`N=1000`, deterministic derived fixture):
- Source: `runs_n1000/benchmarks/killer_stability/robustness_summary.json`
- ToneSight: wins `13/20`, ratio stats `mean=0.940`, `p50=0.868`, `p90=1.312`, `max=1.365`
- ToneSight pass-rates: `separation_ratio_lt_1=0.75`, `true_drift_gt_false_drift=0.75`, `both_ratio_and_true_gt_false=0.75`
- interpretation guardrail: this is a deterministic scaling check on a derived fixture, not independent-distribution or real-world diversity validation.

Known failure regimes (from `tonesight_loss_tag_counts`):
- `occupancy_dominated_shift`: drift is primarily static occupancy mass movement, where simple bins can remain competitive.
- `ramp_mild_or_late`: temporal ramp signal is too weak/late for topology/transition terms to dominate.
- `transition_signal_weak`: sequence dynamics are not strong enough to leverage transition-aware distance.
- `true_drift_not_dominant`: run-level condition where `D(C1,C3)` does not exceed `D(C1,C2)` for ToneSight.

Fixed-metric policy:
- benchmark runs keep the same ToneSight distance weights (`topology_pair=0.7`, `transition_jsd=0.2`, `occupancy_jsd=0.1`) across all profiles/seeds.
- profile variation is used for robustness testing, not per-profile metric retuning.

Release-note claim template (scoped):
- "In this deterministic synthetic robustness protocol (fixed weights, 4 profiles x 5 seeds), ToneSight led by win-rate and mean separation ratio; results are controlled-protocol evidence and not independent-distribution validation."

## Reading Guidance

- Treat these benchmarks as operational evidence, not proofs of universal superiority.
- Compare methods under the same fixture and command invocation.
- For release notes, cite concrete artifact paths and specific metric fields.
