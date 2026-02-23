# ToneSight NS8 - Phased Workflow (Active)

Last reviewed: `2026-02-23`

## Purpose

This file is the active execution tracker.
Policy and governance authority remain in `.agent/AGENT_RULES.md` and `SPEC_NS8.md`.
Historical completed phase detail is archived in `.agent/TO-DO/PHASED_WORKFLOW_ARCHIVE.md`.

## Current Active Phase

- Release track: `v0.2.2 - Adoption and Pipeline Integrations`
- Overall status: `complete`

## Next Queued Work

- `v0.2.0` complete (`#40-#46`): Operations & Contract Hardening delivered.
- `v0.2.1` Phase 1 (`#47`) complete: define killer stability benchmark protocol and evidence contract.
- `v0.2.1` Phase 2 (`#48`) complete: implement deterministic runner + baseline comparators.
- `v0.2.1` Phase 3 (`#49`) complete: integrate benchmark evidence into docs/release flow.
- `v0.2.2` Phase 1 complete (`#50`): zero-friction adapters + pipeline examples.
- `v0.2.2` Phase 2 complete (`#51`): MLflow logging helper + transition heatmap diagnostics.
- `v0.2.2` Phase 3 complete (`#52`): monitoring recipe + incremental stream state + robustness HTML summary.
- `v0.2.2` Phase 4 complete (`#53`): second synthetic generator family + minimal real-trace demo + evidence map.
- GitHub tracking sync: issues `#50-#53` closed.

## Completed Milestones Summary

All prior phases listed below are `complete` and moved to archive:

- Foundation and contract hardening: `Phase 0` through `Phase 8`
- Operations and observability expansion: `Phase 9` through `Phase 21`
- Derived metrics and OSS adoption tracks: `Phase 22` through `Phase 31`
- Production credibility hardening: `Phase 32` through `Phase 35` complete

See `.agent/TO-DO/PHASED_WORKFLOW_ARCHIVE.md` for full objectives, scope, proof links, and acceptance criteria.

## v0.2.0 Phase Plan (Issue-Ready)

Intent:
- improve operational trust, security posture, and artifact contract stability
- preserve deterministic NS8 core behavior and avoid formula/spec changes

Issue mapping:
- #43 Phase 1 - Security CI Gate (`bandit` required)
- #42 Phase 2 - `#nosec` governance policy
- #41 Phase 3 - Compatibility contract unification
- #40 Phase 4 - Artifact schema version fields
- #46 Phase 5 - Deterministic static reporting
- #44 Phase 6 - Dataset quality linting
- #45 Phase 7 - Release-check orchestration command

### Phase 1 - Security CI Gate (`bandit` required)
Status: `complete`

Suggested issue title:
- `v0.2.0: Phase 1 - Add required Bandit security gate in CI`

Scope:
- `.github/workflows/ci.yml`
- `README.md`
- `docs/RELEASE_CHECKLIST.md`

Acceptance criteria:
- CI runs `python -m bandit -r src` on pull requests and main branch pushes
- security scan failure causes job failure (required gate)
- repo docs include local reproduction command for the gate
- no new `#nosec` comments added without explicit reason text

### Phase 2 - `#nosec` Governance Policy
Status: `complete`

Suggested issue title:
- `v0.2.0: Phase 2 - Enforce nosec justification policy`

Scope:
- `docs/SECURITY_POLICY.md` (new)
- `docs/RELEASE_CHECKLIST.md`
- optional lint helper under `tools/` for `#nosec` reason enforcement

Acceptance criteria:
- policy defines allowed `#nosec` usage and required inline rationale format
- policy requires ticket/traceability reference for new suppressions
- CI or test helper fails when `#nosec` appears without required rationale pattern

### Phase 3 - Compatibility Contract Unification
Status: `complete`

Suggested issue title:
- `v0.2.0: Phase 3 - Unify compare/gate/eval-compare compatibility contract`

Scope:
- `src/tonesight_ns8/compare_runner.py`
- `src/tonesight_ns8/gate_runner.py`
- `src/tonesight_ns8/eval_compare_runner.py`
- `tests/test_compare_error_contract.py`
- `tests/test_gate_runner.py`
- `tests/test_live_compare_compatibility.py`

Acceptance criteria:
- shared compatibility checks are implemented in one reusable code path
- compare/gate/eval-compare use the same identity fields and mismatch semantics
- deterministic error payloads/codes are stable and asserted in tests
- no regressions in existing compare/gate determinism suites

### Phase 4 - Artifact Schema Version Fields
Status: `complete`

Suggested issue title:
- `v0.2.0: Phase 4 - Add explicit artifact schema version fields`

Scope:
- `src/tonesight_ns8/eval_runner.py`
- `src/tonesight_ns8/live_runner.py`
- `docs/RECEIPT_SCHEMA.md`
- `docs/API_REFERENCE.md`
- `tests/test_artifact_schema_compatibility.py`

Acceptance criteria:
- receipts include additive `receipt_schema_version` field
- summaries include additive `summary_schema_version` field
- backward compatibility remains additive-only (legacy readers keep working)
- compatibility tests assert field presence/type and legacy parse behavior

### Phase 5 - Deterministic Static Reporting
Status: `complete`

Suggested issue title:
- `v0.2.0: Phase 5 - Add deterministic static report command`

Scope:
- `src/tonesight_ns8/cli.py`
- `src/tonesight_ns8/report_runner.py` (new)
- `tests/test_report_runner.py` (new)
- `docs/EVAL.md`
- `docs/API_REFERENCE.md`

Acceptance criteria:
- new command (for example `tonesight report`) consumes existing run artifacts only
- output includes compare highlights, gate summary, reproducibility metadata
- repeated runs over unchanged inputs produce byte-stable output
- tests validate stable ordering and stable artifact hash behavior

### Phase 6 - Dataset Quality Linting
Status: `complete`

Suggested issue title:
- `v0.2.0: Phase 6 - Add deterministic dataset lint command`

Scope:
- `src/tonesight_ns8/cli.py`
- `src/tonesight_ns8/data_lint_runner.py` (new)
- `tests/test_data_lint_runner.py` (new)
- `docs/EVAL.md`

Acceptance criteria:
- new lint command validates JSONL structural contract deterministically
- detects duplicate/missing IDs, invalid VAD bins, malformed rows, invalid tags
- returns machine-readable summary with deterministic ordering
- non-zero exit when violations exist; zero exit when clean

### Phase 7 - Release Gate Orchestration Command
Status: `complete`

Suggested issue title:
- `v0.2.0: Phase 7 - Add release-check orchestration command`

Scope:
- `src/tonesight_ns8/cli.py`
- `src/tonesight_ns8/release_check_runner.py` (new)
- `tests/test_release_check_runner.py` (new)
- `docs/RELEASE_CHECKLIST.md`
- `README.md`

Acceptance criteria:
- one command runs required pre-release checks deterministically
- output is JSON with per-check pass/fail and overall decision
- command maps failures to non-zero exit code for CI usage
- command behavior and required checks are documented in release docs

## v0.2.1 Phase Plan (Issue-Ready)

Intent:
- deliver one minimal, high-signal benchmark showing low false drift under model swap and high sensitivity to injected drift
- prove comparability advantage versus obvious baselines (quantile bins, equal-width bins, PSI/KS/JSD)
- keep claims scoped to deterministic conformance/drift monitoring (not model inference quality)

Issue mapping:
- #47 Phase 1 - Killer stability benchmark protocol and evidence contract
- #48 Phase 2 - Deterministic runner + baseline comparators
- #49 Phase 3 - Reporting/release integration

### Phase 1 - Protocol and Evidence Contract
Status: `complete`

Suggested issue title:
- `v0.2.1: Phase 1 - Define killer stability benchmark protocol and evidence contract`

Scope:
- `docs/BENCHMARK_KILLER_STABILITY.md` (new)
- `docs/WHY_NS8.md`
- `docs/EVAL.md`

Acceptance criteria:
- protocol defines fixed 2x2 conditions `C1/C2/C3/C4`
- protocol defines required formulas:
  - false drift `D(C1,C2)`
  - true drift `D(C1,C3)`
  - separation ratio `D(C1,C2) / D(C1,C3)`
- protocol defines deterministic config requirements (seed/order/drift params)
- evidence contract defines required metadata (`dataset_hash`, `code_revision`, `spec_version`)

### Phase 2 - Runner and Baseline Comparators
Status: `complete`

Suggested issue title:
- `v0.2.1: Phase 2 - Implement killer stability benchmark runner and baseline comparators`

Scope:
- `src/tonesight_ns8/benchmark_killer_stability.py` (new)
- `src/tonesight_ns8/benchmark_runner.py`
- `src/tonesight_ns8/cli.py`
- `tests/test_benchmark_killer_stability.py` (new)

Acceptance criteria:
- runner executes `C1/C2/C3/C4` deterministically with fixed config
- outputs include ToneSight distances and at least three baselines:
  - quantile bins
  - equal-width bins
  - raw drift baseline (`PSI` and/or `KS/JSD`)
- outputs include separation ratios per method with explicit labels
- repeated runs over unchanged inputs produce byte-stable evidence artifact

### Phase 3 - Reporting and Release Integration
Status: `complete`

Suggested issue title:
- `v0.2.1: Phase 3 - Integrate killer benchmark into reporting, release docs, and CI evidence flow`

Scope:
- `docs/EVAL.md`
- `docs/API_REFERENCE.md`
- `docs/RELEASE_CHECKLIST.md`
- `README.md`

Acceptance criteria:
- docs include canonical benchmark command and artifact paths
- docs include interpretation guidance for false vs true drift and separation ratio
- release checklist references benchmark evidence artifact review for `v0.2.1`
- benchmark integration remains non-blocking unless explicitly promoted in a later phase

## v0.2.2 Phase Plan (Issue-Ready)

Intent:
- move from benchmark-only credibility to obvious real-pipeline usefulness
- preserve deterministic evaluation guardrails while adding adoption-oriented interfaces
- keep claims scoped and artifact-backed

Issue mapping:
- #50 Phase 1 - Zero-friction adapters and pipeline examples
- #51 Phase 2 - MLflow helper and transition heatmap diagnostics
- #52 Phase 3 - Monitoring recipe, stream mode, and robustness HTML report
- #53 Phase 4 - Diverse synthetic generator and minimal real-trace evidence map

### Phase 1 - Zero-Friction Adoption Adapters
Status: `complete`

Suggested issue title:
- `v0.2.2: Phase 1 - Add batch adapters and pipeline-ready examples`

Scope:
- `src/tonesight_ns8/api.py`
- `src/tonesight_ns8/__init__.py`
- `examples/` (new adapter examples or notebook)
- `README.md`
- `docs/EVAL.md`

Acceptance criteria:
- add batch helper for deterministic VAD inputs (for example `tonesight_from_vad_batch(...)`)
- add deterministic label-batch helper over taxonomy mapping (for example `tonesight_from_llm_labels(...)`)
- include at least one end-to-end example showing adapter usage in a practical pipeline
- adapter outputs include deterministic receipt-compatible fields and stable ordering
- tests cover batch shape/typing/ordering and deterministic repeatability

### Phase 2 - MLflow Helper and Visual Diagnostics
Status: `complete`

Suggested issue title:
- `v0.2.2: Phase 2 - Add MLflow artifact helper and transition heatmap output`

Scope:
- `src/tonesight_ns8/eval_runner.py`
- `src/tonesight_ns8/report_runner.py`
- `src/tonesight_ns8/cli.py`
- `docs/API_REFERENCE.md`
- `docs/EVAL.md`
- `tests/` (new helper/report tests)

Acceptance criteria:
- add one-call helper to log run metrics/artifacts to MLflow when tracking is configured
- helper remains no-op safe when MLflow is unavailable or URI is empty
- generate deterministic transition heatmap artifact for run/compare views
- docs include exact command/API usage and artifact paths
- tests validate deterministic output shape and stable field set

### Phase 3 - Monitoring Recipe, Stream Mode, Robustness HTML
Status: `complete`

Suggested issue title:
- `v0.2.2: Phase 3 - Add drift monitoring recipe, incremental stream state, and robustness HTML summary`

Scope:
- `src/tonesight_ns8/analytics.py` or new `src/tonesight_ns8/stream_runner.py`
- `src/tonesight_ns8/benchmark_killer_stability.py`
- `src/tonesight_ns8/cli.py`
- `docs/RECIPES/drift_monitoring.md` (new)
- `README.md`
- `tests/` (new stream/benchmark report tests)

Acceptance criteria:
- add incremental API supporting update/snapshot semantics for rolling sessions
- add generated `robustness_report.html` based on benchmark evidence JSON
- add operator recipe with baseline/candidate/threshold workflow using existing compare/gate commands
- stream and report outputs are deterministic for fixed inputs/order
- tests cover stream accumulator correctness and report artifact generation

### Phase 4 - Diverse Evidence Expansion
Status: `complete`

Suggested issue title:
- `v0.2.2: Phase 4 - Add second synthetic generator family and minimal real-trace evidence map`

Scope:
- `src/tonesight_ns8/benchmark_killer_stability.py`
- `data/` (new tiny public-safe trace fixture or synthetic trace set)
- `docs/BENCHMARK_KILLER_STABILITY.md`
- `docs/WHY_NS8.md`
- `README.md`
- `tests/test_benchmark_killer_stability.py`

Acceptance criteria:
- add at least one new deterministic generator family with distinct drift dynamics (beyond current profiles)
- add one minimal real-trace or pseudo-real trace pipeline demonstration with reproducible command
- publish evidence map summary in docs comparing ToneSight vs baselines across scenario families
- claim language remains explicitly scoped to controlled protocol evidence
- benchmark tests include new generator profile coverage and artifact schema assertions

## Status Vocabulary (Normalized)

Use only these status labels in this workflow:

- `planned`
- `in_progress`
- `complete`

## Maintenance Rules

- Keep this file short and execution-focused.
- Keep historical detail in `.agent/TO-DO/PHASED_WORKFLOW_ARCHIVE.md`.
- Every workflow status change must include an append-only entry in `.agent/LOGS/CHANGE_LOG.md`.
- Any NS8 formula/strictness change still requires spec bump + vectors + tests + docs in one atomic update.
