# Killer Stability Benchmark (v0.2.1 Phase 1 Contract)

This document defines the normative protocol and evidence contract for the v0.2.1 killer stability benchmark.

Goal:
- demonstrate low false drift under harmless upstream model swap
- demonstrate high true drift under controlled drift injection
- compare ToneSight against obvious baselines using the same fixture

Scope boundary:
- this benchmark evaluates conformance/drift comparability behavior
- this benchmark does not claim psychological inference accuracy
- this benchmark is synthetic and controlled; results are not a universal production guarantee

## Protocol: Fixed 2x2 Conditions

Use one fixed dataset and deterministic config to execute four conditions:

- `C1`: same content, upstream `A`, no drift injected
- `C2`: same content, upstream `B`, no drift injected
- `C3`: same content, upstream `A`, drift injected
- `C4`: same content, upstream `B`, drift injected

Interpretation:
- `C1 -> C2` measures false drift sensitivity (harmless change)
- `C1 -> C3` measures true drift sensitivity (real change)
- `C2 -> C4` validates robustness under model-swap + injected drift

## Required Formulas

Let `D(X,Y)` be a deterministic run-to-run distance using the same method.

Required benchmark values:
- false drift distance: `D(C1, C2)`
- true drift distance: `D(C1, C3)`
- robustness drift distance: `D(C2, C4)`

Required headline metric:
- separation ratio: `D(C1, C2) / D(C1, C3)`

Expected direction:
- lower is better (small false drift, large true drift)

## Required Methods

ToneSight method:
- distance from ToneSight run artifacts (compare/evidence-compatible)

Baseline methods (minimum):
- quantile-bin baseline (8 bins)
- equal-width-bin baseline (8 bins)
- raw-distribution baseline (`PSI` and/or `KS`/`JSD`)

All methods must use the same condition pairs and same source fixture.

## Drift Injection Contract

At least one parameterized drift family must be supported, with deterministic controls:
- calibration drift (bias/scale/noise)
- regime drift (subset shift in V/A/D behavior)
- optional spike drift (rare extreme events)

All drift params must be recorded in evidence output.

## Determinism Requirements

- fixed random seed(s) in config
- stable input ordering and stable sort keys
- canonical output ordering for methods/conditions
- stable artifact serialization (`sort_keys=True` for JSON outputs)

## Evidence Artifact Contract

Primary artifact path target:
- `runs/benchmarks/killer_stability/evidence.json`
- `runs/benchmarks/killer_stability/robustness_summary.json`

Required top-level fields:
- `spec_version`
- `benchmark_schema_version`
- `dataset_hash`
- `code_revision` (optional if unavailable, but field should exist with `null`)
- `conditions` (explicit `C1..C4` definitions)
- `config` (seed, drift params, bin settings, method flags)
- `distances` (per method and condition pair)
- `separation_ratios` (per method)
- `summary` (winner ordering/relative interpretation)
- `robustness_sweep` (multi-seed/profile robustness runs + aggregate statistics)

Required robustness summary fields:
- `robustness_sweep.summary.wins_by_method`
- `robustness_sweep.summary.ratio_stats_by_method.<method>.mean/std/min/max/p10/p50/p90`
- `robustness_sweep.summary.absolute_criteria_pass_rate.<method>.*`
- `robustness_sweep.summary.tonesight_loss_tag_counts`
- `robustness_sweep.runs[*].tonesight_loss_tags`

Required condition-pair fields per method:
- `d_c1_c2`
- `d_c1_c3`
- `d_c2_c4`
- `separation_ratio_c12_over_c13`

## Minimal Success Criteria (Phase 1 Documentation Target)

This phase defines protocol only. No implementation proof is required here.

Implementation phases must later demonstrate:
- deterministic reproducibility of evidence artifact
- complete method coverage (ToneSight + required baselines)
- explicit separation-ratio outputs per method
