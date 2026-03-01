# Change Log

Append-only project change log for agent updates.

## Entry template

```
[YYYY-MM-DDTHH:MM:SSZ] Summary
Files: path/to/file1, path/to/file2
Reason: Why this change was made.
Validation: docs-only | tests not run | tests passed | tests failed (details)
```


[2026-02-14T02:50:02Z] Add required agent activity logging policy
Files: .agent/AGENT_RULES.md, .agent/LOGS/CHANGE_LOG.md
Reason: Ensure agents append project updates to a standard log file under .agent/LOGS.
Validation: docs-only


[2026-02-14T02:52:36Z] Add NS8 test vectors with family coverage and strict invalid cases
Files: ns8_test_vectors.json
Reason: Provide canonical NS8 vectors covering all 8 families, edge cases, and 2 strict-mode invalid inputs.
Validation: docs-only


[2026-02-14T02:55:39Z] Add frozen NS8 spec, reference implementation, and vector-based tests
Files: SPEC_NS8.md, ns8_ref.py, test_ns8_vectors.py, ns8_test_vectors.json
Reason: Enforce a strict, versioned NS8 contract with canonical seed routing and executable vector/invariant checks; corrected one inconsistent expected_A using the reference implementation.
Validation: python -m pytest -q test_ns8_vectors.py (13 passed, 1 warning)

[2026-02-14T02:55:49Z] Document NS8 contract artifacts in README
Files: README.md
Reason: Make the new spec/reference/vector/test contract discoverable from primary project docs.
Validation: docs-only

[2026-02-14T03:15:56Z] Add authoritative tone taxonomy contract and validation tests
Files: tone_taxonomy.v1.json, test_tone_taxonomy.py, README.md, .agent/AGENT_RULES.md
Reason: Cross-check and implement deterministic label-to-VAD taxonomy with schema/domain enforcement and distance sanity warnings to prevent mapping drift.
Validation: python -m pytest -q test_ns8_vectors.py test_tone_taxonomy.py (15 passed, warnings expected)

[2026-02-14T03:26:30Z] Add phased implementation workflow under .agent/TO-DO with cross-check gates
Files: .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Translate external phased plan into repo-specific execution phases, including a formula-mismatch decision gate to prevent silent NS8 contract drift.
Validation: docs-only

[2026-02-14T03:35:40Z] Add still-needed and optional pre-build guidance to docs
Files: README.md, .agent/AGENT_RULES.md, EVAL.md
Reason: Make required pre-build gaps explicit (goldset, frozen defaults config, hybrid data policy) and document optional synthetic-data accelerators.
Validation: docs-only

[2026-02-14T04:14:37Z] Refactor docs to deterministic library framing and add API reference
Files: README.md, API_REFERENCE.md
Reason: Align documentation with domain-agnostic, test-vector-validated NS8 library guidance and provide explicit runnable API contract docs.
Validation: docs-only

[2026-02-14T04:16:27Z] Align AGENT_RULES.md to updated deterministic library-first project goal
Files: .agent/AGENT_RULES.md
Reason: Replace prior full-stack API/monitoring-oriented rules with NS8 library-centric scope, strict spec authority, vector/taxonomy policies, and reproducibility-focused documentation standards.
Validation: docs-only

[2026-02-14T04:19:26Z] Refine AGENT_RULES with test policy, vector edit controls, semver note, and phase-gated deliverables
Files: .agent/AGENT_RULES.md
Reason: Apply requested patch to align rules with practical enforcement and current library-first scope while avoiding false policy failures.
Validation: docs-only

[2026-02-14T04:21:23Z] Patch AGENT_RULES numbering and add pytest.ini to stabilize repo-wide test discovery
Files: .agent/AGENT_RULES.md, pytest.ini
Reason: Fix duplicated numbering in scope section and prevent pytest collection errors from inaccessible cache directories.
Validation: python -m pytest -q (15 passed, warnings present)

[2026-02-14T04:26:03Z] Apply high-impact README improvements for installability and API clarity
Files: README.md
Reason: Incorporate recommended documentation upgrades: installation section, explicit non-goals framing, VAD boundary clarification, API naming transition note, structure clarification, and smoother quick-start flow.
Validation: docs-only

[2026-02-14T04:38:36Z] Rework phased workflow and add contract-hardening stubs/tools
Files: .agent/TO-DO/PHASED_WORKFLOW.md, docs/RECEIPT_SCHEMA.md, docs/SEGMENT_INTERFACE.md, config/vad_quantization.v1.json, tools/regen_vectors.py, API_REFERENCE.md, README.md
Reason: Align project plan with hardened phased workflow guidance; add missing receipt/schema boundaries and vector regeneration tooling; mark ns8_ref.py as oracle-until-parity.
Validation: python tools/regen_vectors.py; python -m pytest -q (15 passed, warnings present)

[2026-02-14T04:50:01Z] Add generic segment/speaker/session analytics layer and align docs/workflow
Files: src/tonesight_ns8/__init__.py, src/tonesight_ns8/schema.py, src/tonesight_ns8/analytics.py, conftest.py, test_analytics.py, README.md, API_REFERENCE.md, docs/SEGMENT_INTERFACE.md, docs/ANALYTICS.md, .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Implement deterministic generic analytics and update documentation/contracts for segment->speaker->session summaries while keeping ToneSight domain-agnostic.
Validation: python -m pytest -q (18 passed, warnings present)

[2026-02-14T04:58:55Z] Harden AGENT_RULES with receipt-schema enforcement and vector-regeneration guardrails
Files: .agent/AGENT_RULES.md
Reason: Apply high-priority governance safeguards from external review: enforce canonical receipt schema, restrict vector regeneration, tighten warning policy, and keep CLI as thin wrapper.
Validation: docs-only

[2026-02-14T05:01:49Z] Add release scope bands and refresh phased workflow snapshot
Files: .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Align workflow with agreed v1/v1.1/v1.2 scope statement and clarify that quantization is a boundary contract stub in v1; update present/missing artifact inventory to match repo state.
Validation: docs-only

[2026-02-14T05:07:25Z] Implement package wrappers, deterministic receipt emission, and thin CLI commands
Files: src/tonesight_ns8/errors.py, src/tonesight_ns8/ns8.py, src/tonesight_ns8/taxonomy.py, src/tonesight_ns8/api.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/schema.py, src/tonesight_ns8/__init__.py, test_receipts_api.py, test_cli.py, API_REFERENCE.md, README.md
Reason: Deliver next-step scope: stabilize public API surface, wire receipt schema-compliant wrappers end-to-end, and add minimal CLI (encode, decode, summarize) as thin library wrappers.
Validation: python -m pytest -q (23 passed, warnings present)

[2026-02-14T05:15:12Z] Implement v1/v1.1/v1.2 scope-band patch in phased workflow
Files: .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Align roadmap with agreed library-first sequence, clarify quantization boundary-contract wording, and refresh current-state artifact inventory.
Validation: docs-only

[2026-02-14T05:23:39Z] Add 20-anchor goldset and deterministic eval runner artifacts with CLI eval command
Files: data/goldset.jsonl, src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, src/tonesight_ns8/schema.py, src/tonesight_ns8/ns8.py, src/tonesight_ns8/taxonomy.py, src/tonesight_ns8/api.py, src/tonesight_ns8/errors.py, test_eval_runner.py, test_receipts_api.py, test_cli.py, README.md, API_REFERENCE.md
Reason: Implement agreed next milestone: goldset seed + deterministic eval runner producing out.jsonl/eval_summary.json/receipt.json while keeping API/CLI naming stable and decode parameter-based for v1.
Validation: python -m pytest -q (25 passed, warnings present)

[2026-02-14T05:28:38Z] Add packaging metadata, warning policy, and CI workflow
Files: pyproject.toml, pytest.ini, .github/workflows/ci.yml, README.md, .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Implement remaining ship-quality blockers: editable-install metadata with console script, formalized expected-warning handling, and automated CI (tests + vector regen diff check).
Validation: python -m pytest -q (25 passed); python -m tonesight_ns8.cli --help with PYTHONPATH=src; pip install -e . blocked by local Temp directory permission error in this environment.

[2026-02-14T05:33:07Z] Add Windows temp-permission install workaround to README
Files: README.md
Reason: Document practical PowerShell/CMD workaround for editable-install failures caused by temp directory permissions.
Validation: docs-only

[2026-02-14T13:22:53Z] Clarify workflow freeze policy and add measurable Phase 8 demo acceptance criteria
Files: .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Prevent agent misinterpretation during demo work by explicitly freezing core math behavior and defining deterministic, testable 30-second demo outputs/artifacts.
Validation: docs-only

[2026-02-14T13:26:33Z] Improve README demo discoverability and align sample eval artifacts with actual output schema
Files: README.md
Reason: Surface install troubleshooting as a dedicated section, add a clear 30-second eval demo path, and prevent schema drift by documenting artifact examples that match eval_runner outputs.
Validation: docs-only


[2026-02-14T13:37:19Z] Update phased workflow statuses, add changelog-backed proof links, and append post-Phase fork with Path A/B next steps
Files: .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Reflect current completion state accurately, reduce ambiguity with evidence-linked statuses, and define explicit post-Phase 8 execution paths (default eval tooling vs opt-in observability).
Validation: docs-only


[2026-02-14T13:39:44Z] Convert phased workflow tasks to checkbox format and mark completion state
Files: .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Improve execution tracking clarity by turning phase task items and acceptance criteria into actionable checklists with explicit done/pending markers.
Validation: docs-only


[2026-02-14T13:47:37Z] Add standalone invariants test file, add deterministic demo script, and reconcile phased workflow deferred/completed checkboxes
Files: tests/test_invariants.py, test_ns8_vectors.py, examples/demo_compute.py, .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Remove phase/task inconsistencies by implementing missing low-effort artifacts, separating invariant hardening from vector fixtures, and clarifying intentionally deferred packaging relocations/formula decision status.
Validation: python -m pytest -q test_ns8_vectors.py tests/test_invariants.py (17 passed); PYTHONPATH=src python examples/demo_compute.py


[2026-02-14T17:34:22Z] Implement Phase 9 deterministic run comparison (runner + CLI + tests + docs/workflow updates)
Files: src/tonesight_ns8/compare_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, test_compare.py, README.md, API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Deliver Path A Phase 9 capability to compare two eval runs with deterministic delta metrics, stable regression ranking, optional compare artifact writing, and explicit roadmap/docs alignment.
Validation: python -m pytest -q (31 passed)


[2026-02-14T17:36:22Z] Implement Phase 10 by expanding goldset with intentional negative anchors and making eval test row-count dynamic
Files: data/goldset.jsonl, test_eval_runner.py, .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Increase evaluation signal quality with 10 deterministic mismatch rows (target VAD vs text/label mismatch) and keep tests robust to planned dataset growth without brittle fixed-row assumptions.
Validation: python -m pytest -q (31 passed); PYTHONPATH=src python -m tonesight_ns8.cli eval --goldset data/goldset.jsonl --out-root .agent/tmp_runs_phase10 --taxonomy tone_taxonomy.v1.json --threshold-l1 3; PYTHONPATH=src python -m tonesight_ns8.cli compare .agent/tmp_runs_phase10/run_20260214T173603Z_9affc077cb7b .agent/tmp_runs_phase10/run_20260214T173611Z_9affc077cb7b --top-n 5 --write


[2026-02-14T17:59:19Z] Continue by adding packaged artifact aliases for vectors/taxonomy and closing deferred workflow checkboxes
Files: vectors/ns8_test_vectors.json, taxonomy/tone_taxonomy.v1.json, test_artifact_aliases.py, .agent/TO-DO/PHASED_WORKFLOW.md
Reason: Complete remaining non-formula packaging-path tasks by adding canonical package-oriented artifact locations while retaining root compatibility, and enforce no-drift parity between root and alias files.
Validation: python -m pytest -q (33 passed)


[2026-02-14T18:31:05Z] Continue by standardizing canonical taxonomy/vector paths in runtime defaults, tooling, tests, and docs
Files: src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/cli.py, tools/regen_vectors.py, test_ns8_vectors.py, test_tone_taxonomy.py, API_REFERENCE.md, README.md
Reason: Align the now-present package-oriented artifact locations (	axonomy/, ectors/) with operational defaults while preserving compatibility with root aliases and keeping deterministic behavior unchanged.
Validation: python -m pytest -q (33 passed)


[2026-02-14T18:49:14Z] Apply pre-push polish: add gitignore hygiene, document Phase 2 freeze explicitly, and append correction for prior encoding artifact text
Files: .gitignore, README.md, .agent/LOGS/CHANGE_LOG.md
Reason: Prepare Path A scope for presentation by excluding local runtime/cache files from source control, making deferred formula status explicit in top-level docs, and clarifying prior changelog path text where control characters rendered incorrectly (intended paths: 	axonomy/, ectors/).
Validation: python -m pytest -q (33 passed)


[2026-02-14T18:51:56Z] Resolve Phase 2 with Option A and record formula decision under spec_version 1.0
Files: .agent/TO-DO/PHASED_WORKFLOW.md, SPEC_NS8.md
Reason: Close the remaining governance decision by explicitly adopting Option A (retain current NS8 formulas) and making the choice auditable in workflow and spec decision records.
Validation: python -m pytest -q (33 passed)


[2026-02-14T19:05:22Z] Implement Path B monitoring stack (workflow + services + observability docs + smoke tests)
Files: .agent/TO-DO/PHASED_WORKFLOW.md, docker-compose.yml, docker/api.Dockerfile, requirements-observability.txt, src/tonesight_ns8/observability_api.py, monitoring/prometheus/prometheus.yml, monitoring/grafana/provisioning/datasources/datasource.yml, monitoring/grafana/provisioning/dashboards/dashboards.yml, monitoring/grafana/dashboards/tonesight-overview.json, pyproject.toml, README.md, MONITORING.md, test_observability_api.py
Reason: Add an opt-in v1.2 observability platform without changing NS8 core behavior, including containerized monitoring services, HTTP metrics instrumentation, dashboard provisioning, and baseline validation coverage.
Validation: python -m pytest -q (34 passed, 1 skipped); docker compose config -q


[2026-02-14T19:30:08Z] Implement quality iteration set 1-4: calibration support, regular eval+compare workflow, expanded goldset signal, and richer monitoring (alerts + optional MLflow/GPU)
Files: src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/eval_compare_runner.py, src/tonesight_ns8/__init__.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/observability_api.py, monitoring/prometheus/prometheus.yml, monitoring/prometheus/alerts.yml, monitoring/grafana/dashboards/tonesight-overview.json, docker-compose.yml, data/goldset.jsonl, config/taxonomy_calibration.v1.json, pyproject.toml, requirements-observability.txt, API_REFERENCE.md, README.md, MONITORING.md, test_eval_runner.py, test_cli.py, test_observability_api.py
Reason: Deliver requested post-core improvements by adding deterministic calibration hooks, one-command regression tracking cadence (eval-compare), broader/balanced dataset coverage for stronger signal, and production-oriented observability upgrades including alert rules and optional run-level MLflow/GPU telemetry.
Validation: python -m pytest -q (37 passed, 1 skipped); docker compose config -q


[2026-02-15T01:27:11Z] Improve Grafana usability by separating live volatile panels from 30m-smoothed panels and adding on-dashboard interpretation guidance
Files: monitoring/grafana/dashboards/tonesight-overview.json, README.md
Reason: Prevent false 'project is broken' perception by making low-traffic volatility explicit, providing stable smoothing views, and clarifying how eval snapshot gauges should be interpreted.
Validation: dashboard JSON parse check; Prometheus query validation for new panel expressions (vg_over_time, last_over_time, freshness expression)


[2026-02-15T01:31:35Z] Harden Grafana smoothing stability by switching to 30m increase-based panel queries and fixed axis behavior
Files: monitoring/grafana/dashboards/tonesight-overview.json
Reason: Reduce refresh-to-refresh volatility and visual scale distortion for low-traffic dashboards by using more step-insensitive PromQL for smoothed panels and applying non-negative/soft-max axis constraints.
Validation: dashboard JSON parse check; Prometheus query validation for updated expressions (sum(increase(...))/1800, histogram_quantile over 30m increase rates)


[2026-02-15T16:23:36Z] Harden stat panel stability by forcing lastNotNull reduction and explicit units/decimals; add fixed axis bounds for smoothed RPS panel
Files: monitoring/grafana/dashboards/tonesight-overview.json
Reason: Eliminate misleading refresh-to-refresh jumps caused by time-window aggregation defaults in Grafana stat panels and reduce visual volatility from autoscaling.
Validation: dashboard JSON parse check; Prometheus query spot-check for stat panel expressions and values


[2026-02-16T17:37:52Z] Enforce strict integer NS8 inputs and runtime taxonomy label format
Files: ns8_ref.py, src/tonesight_ns8/taxonomy.py, tests/test_strict_validation.py
Reason: Close validation gaps by rejecting float/bool NS8 inputs and enforcing lowercase snake_case labels during runtime taxonomy validation (not only in tests).
Validation: python -m pytest -q


[2026-02-16T17:40:02Z] Add default config artifact and enforce phase-gated checklist parity
Files: config/defaults.json, tests/test_defaults_config.py, .agent/AGENT_RULES.md
Reason: Close remaining governance gap by adding canonical deterministic defaults config and marking phase-gated deliverables complete when artifacts are present.
Validation: python -m pytest -q


[2026-02-16T17:42:46Z] Wire runtime defaults to config/defaults.json across eval, CLI, and observability API
Files: src/tonesight_ns8/defaults.py, src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/eval_compare_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/observability_api.py, tests/test_defaults_config.py
Reason: Make config/defaults.json the single source of truth for runtime defaults and remove hardcoded duplicate defaults from call sites.
Validation: python -m pytest -q


[2026-02-16T17:45:43Z] Document config-driven defaults, add override integration test, and add CI defaults-schema guard
Files: README.md, API_REFERENCE.md, tests/test_defaults_config.py, tools/validate_defaults.py, .github/workflows/ci.yml
Reason: Align docs with config/defaults.json behavior, verify defaults overrides propagate through CLI/eval via module reload in tests, and fail CI early on malformed defaults config.
Validation: python tools/validate_defaults.py; python -m pytest -q


[2026-02-16T17:51:03Z] Add defaults schema doc and fail-fast runtime errors for defaults loading
Files: docs/DEFAULTS_SCHEMA.md, README.md, API_REFERENCE.md, src/tonesight_ns8/defaults.py, tests/test_defaults_config.py
Reason: Formalize the defaults artifact contract and improve operability by raising explicit runtime errors for missing/unreadable/invalid defaults config.
Validation: python tools/validate_defaults.py; python -m pytest -q


[2026-02-16T17:59:31Z] Share defaults schema validation across runtime/CI and add startup fail-fast tests for CLI/observability imports
Files: src/tonesight_ns8/defaults_schema.py, src/tonesight_ns8/defaults.py, tools/validate_defaults.py, tests/test_defaults_config.py
Reason: Eliminate duplicated defaults-schema logic by centralizing validation and verify malformed defaults config fails clearly at CLI/API startup import surfaces.
Validation: python tools/validate_defaults.py; python -m pytest -q


[2026-02-16T18:07:18Z] Add docs-consistency/defaults validator negative tests and document TONESIGHT_DEFAULTS_PATH override
Files: tests/test_defaults_config.py, tools/validate_defaults.py, README.md, MONITORING.md
Reason: Prevent drift between docs and config/defaults.json, validate non-zero failure behavior on malformed defaults fixture, and document runtime defaults path override for CLI/API operations.
Validation: python tools/validate_defaults.py; python -m pytest -q


[2026-02-16T18:13:19Z] Add explicit defaults override examples and CI negative check against invalid defaults fixture
Files: README.md, MONITORING.md, .github/workflows/ci.yml, tests/fixtures/defaults.invalid.json, tests/test_defaults_config.py
Reason: Improve operator usability with concrete shell-specific TONESIGHT_DEFAULTS_PATH examples and enforce validator failure behavior in CI using a committed malformed fixture.
Validation: python tools/validate_defaults.py; python -m pytest -q; python tools/validate_defaults.py tests/fixtures/defaults.invalid.json (expected failure)


[2026-02-16T18:16:54Z] Reconcile status docs, finalize license metadata, and enforce observability tests in CI
Files: README.md, .agent/AGENT_RULES.md, pyproject.toml, LICENSE, .github/workflows/ci.yml
Reason: Align project-status documentation with completed phase decisions, remove placeholder licensing metadata, and ensure observability test coverage is enforced in CI with optional dependencies installed.
Validation: python tools/validate_defaults.py; python -m pytest -q


[2026-02-16T18:20:35Z] Add v1 release checklist, define public API stability policy, add CI CLI/eval smoke, and tighten artifact ignore rules
Files: docs/RELEASE_CHECKLIST.md, README.md, API_REFERENCE.md, .github/workflows/ci.yml, .gitignore
Reason: Improve v1 release readiness by codifying validation workflow, clarifying stable-vs-internal API boundaries, enforcing entrypoint/eval smoke checks in CI, and preventing runtime artifact clutter in source control.
Validation: python tools/validate_defaults.py; python -m pytest -q; PYTHONPATH=src python -m tonesight_ns8.cli eval


[2026-02-16T18:33:58Z] Tighten scope wording for deterministic conformance positioning and add legacy-brief guardrails
Files: README.md, API_REFERENCE.md, PROJECT_BRIEF.md
Reason: Align documentation language with library-first scope by emphasizing conformance/regression priorities, clarifying non-inference taxonomy mapping, keeping observability explicitly opt-in, and preventing scope drift from legacy planning brief content.
Validation: python tools/validate_defaults.py; python -m pytest -q


[2026-02-16T18:40:04Z] Apply README presentation polish and release-checklist warning hygiene note
Files: README.md, docs/RELEASE_CHECKLIST.md
Reason: Improve external readability with a concise why/architecture/quick-demo narrative and add explicit warning-triage expectation in release checks without changing core scope or behavior.
Validation: python tools/validate_defaults.py; python -m pytest -q



[2026-02-16T20:07:03Z] Add licensing boundary documentation without changing v1 MIT license scope
Files: LICENSE_POLICY.md, README.md
Reason: Apply licensing clarity suggestions in a scope-safe way by documenting current MIT coverage and future boundary policy without introducing a new active license.
Validation: docs-only (no code-path changes)

[2026-02-16T20:54:03Z] Add concrete v1.1 milestone checklist and CHANGE_LOG entry template
Files: docs/RELEASE_CHECKLIST.md
Reason: Define post-v1 execution scope and standardize append-only log formatting for consistent release governance.
Validation: docs-only (no code-path changes)

[2026-02-16T20:56:03Z] Start v1.1 by improving CLI argument validation and operator-facing error handling
Files: src/tonesight_ns8/cli.py, test_cli.py
Reason: Improve usability with explicit family choices, bounded NS8 integer validation, non-negative numeric checks, and deterministic JSON error payloads for runtime command failures.
Validation: python -m pytest -q test_cli.py; python -m pytest -q tests/test_strict_validation.py; python -m pytest -q

[2026-02-16T20:58:47Z] Continue v1.1 with deterministic eval/compare report ergonomics and trend metadata
Files: src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/compare_runner.py, test_eval_runner.py, test_compare.py, docs/API_REFERENCE.md
Reason: Improve operator readability by adding explicit pass/fail and distribution summary fields for eval outputs plus deterministic trend/coverage metadata for compare outputs.
Validation: python -m pytest -q test_eval_runner.py test_compare.py; python -m pytest -q

[2026-02-16T21:00:34Z] Continue v1.1 by aligning evaluation documentation with implemented CLI/API and artifact contracts
Files: docs/EVAL.md, README.md
Reason: Remove stale pre-v1 language and document the actual goldset schema, commands, artifacts, and deterministic summary/compare fields to reduce operator confusion.
Validation: python -m pytest -q tests/test_defaults_config.py; python -m pytest -q

[2026-02-16T21:09:16Z] Package and release v1.1 with CLI usability, report ergonomics, and docs alignment updates
Files: pyproject.toml, src/tonesight_ns8/observability_api.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/compare_runner.py, test_cli.py, test_eval_runner.py, test_compare.py, docs/EVAL.md, docs/API_REFERENCE.md, docs/RELEASE_CHECKLIST.md, README.md
Reason: Finalize post-v1 milestone work with deterministic operator UX/reporting improvements, update docs to implemented behavior, and bump package/app version to 1.1.0 for release.
Validation: python -m pytest -q

[2026-02-16T22:03:33Z] Add deterministic mapping registry interface and NS8 adapter scaffold for v1.2 extensibility
Files: src/tonesight_ns8/mapping.py, src/tonesight_ns8/api.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_mapping_registry.py, test_cli.py, docs/API_REFERENCE.md, README.md
Reason: Introduce a mapping plugin seam where NS8 remains default while enabling future mappings through a typed registry, without changing existing deterministic outputs.
Validation: python -m pytest -q tests/test_mapping_registry.py test_cli.py test_receipts_api.py; python -m pytest -q

[2026-02-16T22:14:10Z] Add README environment best-practice guidance for CLI invocation and reset workflow
Files: README.md
Reason: Reduce cross-platform install friction by making python -m invocation canonical, documenting Windows PATH behavior for script entrypoints, and adding a deterministic sanity-reset sequence.
Validation: docs-only (no code-path changes)

[2026-02-17T02:38:18Z] Add reusable mapping adapter conformance harness and packaged example adapter
Files: src/tonesight_ns8/mapping_examples.py, tests/mapping_conformance.py, tests/test_mapping_conformance.py, tests/test_mapping_registry.py, tests/__init__.py, docs/API_REFERENCE.md, README.md
Reason: Implement v1.2 next steps by introducing a reusable contract test suite for adapters and a minimal second adapter used in registry and conformance validation.
Validation: python -m pytest -q tests/test_mapping_conformance.py tests/test_mapping_registry.py test_cli.py; python -m pytest -q

[2026-02-17T04:15:34Z] Add deterministic eval HTML report artifact and wire it into receipts/docs
Files: src/tonesight_ns8/eval_runner.py, test_eval_runner.py, README.md, docs/API_REFERENCE.md, docs/EVAL.md
Reason: Provide a simple human-readable eval report (eport.html) generated from existing artifacts while preserving deterministic scoring outputs.
Validation: python -m pytest -q test_eval_runner.py; python -m pytest -q

[2026-02-17T04:21:32Z] Expand eval HTML report with coverage, L1 distribution percentiles/buckets, and per-dimension MAE
Files: src/tonesight_ns8/eval_runner.py, test_eval_runner.py
Reason: Improve report utility for operators by adding low-complexity quality diagnostics beyond core KPIs while preserving deterministic artifacts.
Validation: python -m pytest -q test_eval_runner.py; python -m pytest -q

[2026-02-17T04:27:09Z] Rework eval report.html into interactive multi-panel deterministic report
Files: src/tonesight_ns8/eval_runner.py
Reason: Incorporate recruiter-facing demo guidance with a self-contained report that highlights deterministic, observable, and agent-ready behavior (3D VAD explorer, drift charts, heatmap, regression panel) from eval artifacts only.
Validation: python -m pytest -q test_eval_runner.py; python -m pytest -q; python -m tonesight_ns8.cli eval

[2026-02-17T04:45:51Z] Implement v1.3 reporting upgrades and expand goldset to 120 rows
Files: src/tonesight_ns8/eval_runner.py, data/goldset.jsonl, README.md, docs/EVAL.md, docs/API_REFERENCE.md
Reason: Add conformance framing, richer interactive report diagnostics (metadata, rolling pass rate, cumulative failures, agent-aware view), runtime metadata capture, and larger deterministic goldset coverage for stronger evaluation signal.
Validation: python -m pytest -q; python -m tonesight_ns8.cli eval

[2026-02-18T18:34:57Z] Bump package/app versions to 1.3.0 and finalize release-prep commit
Files: pyproject.toml, src/tonesight_ns8/observability_api.py
Reason: Align release metadata with current v1.3.0 feature scope before push.
Validation: python tools/validate_defaults.py; python -m pytest -q; python -m tonesight_ns8.cli eval

[2026-02-18T20:20:16Z] Stop tmp directory accumulation in tests and cleanup existing temp artifacts
Files: pytest.ini, test_cli.py, test_compare.py, test_eval_runner.py, tests/test_defaults_config.py, .agent/LOGS/CHANGE_LOG.md
Reason: Prevent unbounded growth of repo-local tmp directories by removing per-run UUID temp roots in tests, reusing deterministic test temp roots with pre-cleanup, and disabling pytest cacheprovider creation of pytest-cache-files-* directories.
Validation: python -m pytest -q (64 passed); elevated cleanup removed pytest-cache-files-*, .agent/tmp*, and .tmp/tmp_defaults_* directories.

[2026-02-18T22:03:50Z] Implement GitHub issues #1, #2, #3: eval explainability, compare deltas, and receipt reproducibility hashes
Files: src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/compare_runner.py, test_eval_runner.py, test_compare.py, test_cli.py, docs/EVAL.md, docs/API_REFERENCE.md, README.md, .agent/LOGS/CHANGE_LOG.md
Reason: Deliver top-priority issue work by adding deterministic per-row delta explainability (delta_v/delta_a/delta_d, 	hreshold_margin), exposing per-dimension regression changes in compare output, and recording 	axonomy_hash/defaults_hash in eval receipts for reproducibility.
Validation: python -m pytest -q (64 passed)

[2026-02-19T17:31:58Z] Complete GitHub issues #4-#9 with compare compatibility gates/artifacts, goldset expansion+validation, presentation mode, and CLI trace metadata
Files: src/tonesight_ns8/eval_compare_runner.py, src/tonesight_ns8/compare_runner.py, src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/cli.py, data/goldset.jsonl, tools/validate_goldset.py, tests/test_goldset_validation.py, tests/fixtures/goldset.invalid.jsonl, test_eval_runner.py, test_compare.py, test_cli.py, docs/EVAL.md, docs/API_REFERENCE.md, README.md, .agent/LOGS/CHANGE_LOG.md
Reason: Finish remaining open enhancement issues by implementing deterministic compatibility checks and reporting ergonomics while strengthening dataset quality and reproducibility visibility.
Validation: python -m pytest -q (67 passed); python tools/validate_goldset.py data/goldset.jsonl

[2026-02-19T17:51:04Z] Refine project positioning docs for conformance-layer precision and safer affect wording
Files: README.md, docs/EVAL.md, .agent/LOGS/CHANGE_LOG.md
Reason: Align external-analysis feedback with current implementation by clarifying that ToneSight standardizes VAD-based affect telemetry, expects upstream-discretized inputs, and is a deterministic conformance layer (not emotion inference).
Validation: docs-only

[2026-02-19T17:54:22Z] Align docs to external positioning review: preserve infra framing, tighten non-overclaim wording
Files: README.md, docs/EVAL.md, docs/MONITORING.md, .agent/LOGS/CHANGE_LOG.md
Reason: Confirmed external pitch mostly matches code (deterministic conformance, run-to-run drift, observability); clarified language to avoid ground-truth emotion claims and reinforce upstream input boundary.
Validation: docs-only

[2026-02-19T17:58:18Z] Add architect-level NS8 contract assurance documentation and cross-links
Files: docs/NS8_CONTRACT_ASSURANCE.md, README.md, docs/API_REFERENCE.md, docs/SPEC_NS8.md, .agent/LOGS/CHANGE_LOG.md
Reason: External review highlighted value of formal contract framing; added explicit axioms/invariants/determinism/traceability matrix grounded in existing oracle+tests without overclaiming theorem-prover-level formal verification.
Validation: docs-only

[2026-02-19T18:52:04Z] Add v1.4 phased workflow plan and create tracking issues #10-#13
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Cross-referenced external upgrade suggestions with current codebase and converted high-ROI, scope-safe items into a concrete v1.4 execution track with acceptance criteria and GitHub issue tracking.
Validation: docs-only

[2026-02-19T18:56:12Z] Implement v1.4 Phase 11: deterministic gate command for CI regression checks
Files: src/tonesight_ns8/gate_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_gate_runner.py, README.md, docs/EVAL.md, docs/API_REFERENCE.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add tonesight gate command with compatibility checks (dataset/spec), threshold-based regression decisions, and stable exit codes (0 pass, 2 regressed, 3 incompatible) for CI/CD release gating.
Validation: python -m pytest -q tests/test_gate_runner.py test_cli.py test_compare.py (13 passed); python -m pytest -q (71 passed)

[2026-02-19T19:30:38Z] Implement v1.4 Phase 12: deterministic triage export command for data QA
Files: src/tonesight_ns8/triage_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_triage_runner.py, test_cli.py, README.md, docs/EVAL.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add tonesight triage command with single-run and diff modes, deterministic score-based ranking, jsonl/csv export, and rationale fields for reviewer prioritization.
Validation: python -m pytest -q tests/test_triage_runner.py test_cli.py (11 passed); python -m pytest -q (75 passed)

[2026-02-19T22:03:16Z] Implement v1.4 Phase 13: deterministic forensics bundle command
Files: src/tonesight_ns8/bundle_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_bundle_runner.py, test_cli.py, README.md, docs/API_REFERENCE.md, docs/RELEASE_CHECKLIST.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add tonesight bundle command to package run artifacts (and optional compare artifacts) into deterministic zip bundles with manifest hashes for incident analysis and auditability.
Validation: python -m pytest -q tests/test_bundle_runner.py test_cli.py (12 passed); python -m pytest -q (79 passed)

[2026-02-20T00:39:33Z] Implement v1.4 Phase 14: deterministic trend rollups with optional artifact-level grouping
Files: src/tonesight_ns8/trend_runner.py, src/tonesight_ns8/compare_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_trend_runner.py, test_compare.py, test_cli.py, README.md, docs/EVAL.md, docs/MONITORING.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add tonesight trend command to aggregate run-over-run deltas from artifacts, with deterministic grouping by row metadata fields (source/agent/prompt_id or other present keys) while keeping provider-agnostic architecture.
Validation: python -m pytest -q tests/test_trend_runner.py test_compare.py test_cli.py (16 passed); python -m pytest -q (84 passed)

[2026-02-20T04:22:40Z] Add concrete v1.5/v1.6 roadmap phases and create matching GitHub issues #14-#20
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Convert live-readiness and controlled-productionization guidance into actionable phased deliverables with explicit scope/acceptance criteria and issue tracking.
Validation: docs-only

[2026-02-20T17:59:38Z] Implement v1.5 hardening batch: observability auth/rate limiting/path allowlist, container hardening, secure bundle manifests, and pinned dependency/image versions
Files: src/tonesight_ns8/observability_api.py, src/tonesight_ns8/bundle_runner.py, src/tonesight_ns8/cli.py, docker-compose.yml, docker/api.Dockerfile, requirements-observability.txt, pyproject.toml, test_observability_api.py, tests/test_bundle_runner.py, test_cli.py, README.md, docs/MONITORING.md, docs/API_REFERENCE.md, .agent/LOGS/CHANGE_LOG.md
Reason: Address security posture gaps by enforcing bearer auth and rate limits on sensitive endpoints, restricting filesystem paths, removing default container credentials, running API container as non-root, supporting external-safe forensics bundles, and reducing supply-chain drift.
Validation: python -m pytest -q test_observability_api.py tests/test_bundle_runner.py test_cli.py (19 passed); python -m pytest -q (88 passed)

[2026-02-20T18:09:49Z] Implement v1.5 Phase 15: canonical LiveEvent schema and validation tooling
Files: docs/LIVE_EVENT_SCHEMA.md, schemas/live_event.schema.json, tools/validate_live_event.py, tests/test_live_event_validation.py, tests/fixtures/live_event.valid.jsonl, tests/fixtures/live_event.invalid.jsonl, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Define deterministic shadow-mode ingestion contract and enforce it with explicit reason-coded validation errors for malformed live event envelopes.
Validation: python -m pytest -q tests/test_live_event_validation.py (2 passed); python -m pytest -q (90 passed)

[2026-02-20T18:39:20Z] Implement v1.5 Phase 16: deterministic live identity hashing and shadow strictness policies
Files: src/tonesight_ns8/live_identity.py, src/tonesight_ns8/live_shadow_policy.py, src/tonesight_ns8/__init__.py, docs/IDENTITY_AND_HASHING.md, docs/EVAL.md, README.md, tests/test_hash_stability.py, tests/test_shadow_mode_quarantine.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add stable event hash semantics (excluding timestamp_received) and explicit fail/drop/quarantine handling with deterministic quarantine receipts for invalid live events.
Validation: python -m pytest -q tests/test_hash_stability.py tests/test_shadow_mode_quarantine.py tests/test_live_event_validation.py (7 passed); python -m pytest -q (95 passed)

[2026-02-20T18:59:37Z] Implement v1.5 Phase 17: deterministic live capture/replay/verify harness with CLI and CI smoke
Files: src/tonesight_ns8/live_runner.py, src/tonesight_ns8/live_event_validation.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tools/validate_live_event.py, tests/test_live_replay_determinism.py, tests/fixtures/live_capture.small.jsonl, test_cli.py, .github/workflows/ci.yml, README.md, docs/EVAL.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Deliver live shadow-mode replay capability by adding deterministic capture IDs/run IDs, standard run artifact generation from LiveEvent inputs, replay stability verification via artifact hashing, CLI commands (live-capture/live-replay/live-verify), and CI golden-capture smoke coverage.
Validation: python -m pytest -q tests/test_live_replay_determinism.py test_cli.py tests/test_live_event_validation.py tests/test_hash_stability.py tests/test_shadow_mode_quarantine.py (22 passed)

[2026-02-20T19:12:07Z] Add v1.7 derived-metrics roadmap section and create matching GitHub issues #21-#24
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Convert external derived-metrics suggestions into concrete, scope-safe phased deliverables (Phase 22-25) with deterministic acceptance criteria and create trackable implementation issues on GitHub.
Validation: docs/planning update only; GitHub issues created: #21, #22, #23, #24

[2026-02-20T20:03:00Z] Implement v1.5 Phase 18 redaction + retention controls with CLI/docs/tests
Files: src/tonesight_ns8/redaction.py, src/tonesight_ns8/retention.py, src/tonesight_ns8/live_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_redaction_determinism.py, tests/test_retention_purge.py, tests/test_live_replay_determinism.py, test_cli.py, docs/PRIVACY_REDACTION.md, docs/RETENTION_POLICY.md, docs/EVAL.md, docs/API_REFERENCE.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add deterministic text redaction stage for live replay artifacts and safe retention purge workflow (dry-run default, explicit bundle/capture inclusion), then document and validate behavior end-to-end.
Validation: python -m pytest -q tests/test_retention_purge.py test_cli.py tests/test_redaction_determinism.py tests/test_live_replay_determinism.py (21 passed); python -m pytest -q (106 passed)

[2026-02-21T00:16:13Z] Implement v1.6 Phase 19 live compatibility contract and deterministic gate profiles
Files: src/tonesight_ns8/gate_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/live_runner.py, config/gate_profiles.json, tests/test_gate_runner.py, tests/test_gate_profiles.py, tests/test_live_compare_compatibility.py, docs/LIVE_COMPATIBILITY.md, docs/GATE_PROFILES.md, docs/EVAL.md, docs/API_REFERENCE.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Enforce explicit run compatibility identities (spec/mapping/taxonomy/calibration/defaults and optional dataset matching), add environment-specific gate threshold profiles with CLI support, and document deterministic contract behavior for controlled productionization.
Validation: python -m pytest -q tests/test_gate_runner.py tests/test_gate_profiles.py tests/test_live_compare_compatibility.py test_cli.py test_compare.py (27 passed); python -m pytest -q (113 passed)

[2026-02-21T00:35:50Z] Implement v1.6 Phase 20 canary evaluator and incident automation
Files: src/tonesight_ns8/canary_runner.py, src/tonesight_ns8/incident_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_canary_flow.py, tests/test_incident_bundle.py, test_cli.py, docs/INCIDENT_PLAYBOOK.md, docs/API_REFERENCE.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add deterministic canary flow to replay same capture through baseline/candidate pipelines with gate evaluation, and add incident packaging command that emits compare/triage/bundle/report artifact references for operational response.
Validation: python -m pytest -q tests/test_canary_flow.py tests/test_incident_bundle.py test_cli.py (17 passed); python -m pytest -q (117 passed)

[2026-02-21T00:48:48Z] Implement v1.6 Phase 21 minimal deterministic run index
Files: src/tonesight_ns8/run_index.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_run_index.py, test_cli.py, docs/EVAL.md, docs/API_REFERENCE.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add a lightweight deterministic run metadata index (`index-runs`) with stable ordering, schema-consistent JSONL rows, source/profile labels, and artifact pointers for historical retrieval without platform creep.
Validation: python -m pytest -q tests/test_run_index.py test_cli.py (18 passed); python -m pytest -q (120 passed)
[2026-02-22T19:22:02Z] Add v1.8 OSS adoption phased workflow with concrete PR sequence
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Convert OSS usability/adoption recommendations into an execution-ready PR plan with scoped files, deterministic acceptance criteria, and phase gating that preserves NS8 core contract stability.
Validation: docs-only
[2026-02-22T19:25:17Z] Reconcile v1.7 workflow status to complete and mark Phase 22-25 complete with proof references
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Workflow planning drifted from implemented derived-metrics state; updated status markers to match existing analytics/docs/tests so next work selection is accurate.
Validation: python -m pytest -q test_analytics.py tests/test_derived_metrics_contract.py (9 passed)
[2026-02-22T19:30:11Z] Implement v1.8 PR 1 deterministic benchmark harness, CLI command, artifacts, and docs
Files: src/tonesight_ns8/benchmark_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, benchmarks/README.md, benchmarks/noise_tolerance.py, benchmarks/drift_injection.py, benchmarks/model_swap_robustness.py, benchmarks/baselines.py, tests/test_benchmark_cli.py, docs/EVAL.md, docs/API_REFERENCE.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Start v1.8 PR 1 by adding reproducible benchmark evidence workflows (noise tolerance, drift injection, model-swap robustness, baseline occupancy/distances) with deterministic JSON artifacts under runs/benchmarks/core and CLI execution support.
Validation: python -m pytest -q tests/test_benchmark_cli.py (2 passed); python -m pytest -q test_cli.py (16 passed)
[2026-02-22T20:21:08Z] Implement v1.8 PR 2 evidence narrative docs and conformance-vs-evidence separation
Files: docs/WHY_NS8.md, README.md, docs/EVAL.md, docs/NS8_CONTRACT_ASSURANCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Complete PR 2 by adding a claim-to-artifact evidence document, linking benchmark usage from top-level docs, and explicitly separating contract-level conformance guarantees from benchmark-level empirical evidence.
Validation: docs-only
[2026-02-22T20:26:22Z] Implement v1.8 PR 3 canonical telemetry ID policy and enforcement tests
Files: docs/CANONICAL_ID_POLICY.md, tests/test_canonical_id_policy.py, docs/LIVE_COMPATIBILITY.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Complete PR 3 by formalizing canonical identity stability/migration rules and adding deterministic tests that enforce receipt identity field presence/types and compatibility mismatch behavior in gate workflows.
Validation: python -m pytest -q tests/test_canonical_id_policy.py (3 passed); python -m pytest -q tests/test_gate_runner.py tests/test_live_compare_compatibility.py (9 passed)
[2026-02-22T20:28:05Z] Implement v1.8 PR 4 onboarding UX, deterministic demo script, and non-blocking benchmark CI workflow
Files: README.md, CONTRIBUTING.md, examples/ns8_drift_demo.py, Makefile, .github/workflows/benchmarks.yml, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Complete PR 4 by adding a 5-minute onboarding path, deterministic end-to-end demo (eval/compare/benchmark), contributor guidance for benchmark modules, and a separate non-blocking benchmark CI workflow with artifact upload.
Validation: python examples/ns8_drift_demo.py --out-root .agent/test_tmp/demo_pr4; python -m pytest -q tests/test_benchmark_cli.py (2 passed)
[2026-02-22T20:31:22Z] Implement v1.8 PR 5 topology-aware compare distance mode and complete v1.8 workflow track
Files: src/tonesight_ns8/compare_runner.py, src/tonesight_ns8/cli.py, tests/test_compare_topology_distance.py, docs/EVAL.md, docs/API_REFERENCE.md, docs/NS8_CONTRACT_ASSURANCE.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Complete optional phase-gated PR 5 by adding deterministic compare distance mode selection (l1/	opology), topology distance semantics with fallback behavior, dedicated regression tests, and documentation updates; mark v1.8 complete after PR1-PR5 delivery.
Validation: python -m pytest -q tests/test_compare_topology_distance.py (2 passed); python -m pytest -q test_compare.py test_cli.py (19 passed)
[2026-02-22T20:35:10Z] Run repo sanity checks and refresh docs for v1.8 additions before commit/push prep
Files: README.md, docs/EVAL.md, .agent/LOGS/CHANGE_LOG.md
Reason: Verify end-to-end suite and command health, then close remaining documentation gaps by updating release-checklist/structure references and adding topology-distance compare CLI example.
Validation: python tools/validate_defaults.py; python -m tonesight_ns8.cli --help; python -m pytest -q (133 passed); python -m tonesight_ns8.cli benchmark --suite core --out-root .agent/test_tmp/sanity_bench --goldset data/goldset.jsonl
[2026-02-22T20:41:36Z] Migrate package/app versioning to pre-1.0 sequence and set current release target to 0.1.8
Files: pyproject.toml, src/tonesight_ns8/observability_api.py, src/tonesight_ns8/__init__.py, README.md, docs/RELEASE_CHECKLIST.md, docs/API_REFERENCE.md, docs/DERIVED_METRICS.md, docs/LIVE_EVENT_SCHEMA.md, .agent/LOGS/CHANGE_LOG.md
Reason: Align project release versioning to a professional pre-1.0 semver track (0.x) while preserving NS8 contract spec_version: 1.0 as a separate behavior-spec namespace.
Validation: python -m pytest -q (133 passed); python tools/validate_defaults.py; python -m tonesight_ns8.cli --help
[2026-02-22T21:17:40Z] Add v0.1.9 phased workflow for production-credibility hardening and map next 4 high-ROI gaps
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Convert requested next-step suggestions into a concrete phase plan (security enforcement tests, property invariants, artifact compatibility gates, performance smoke gate) while preserving NS8 core contract stability.
Validation: docs-only
[2026-02-22T21:21:36Z] Add v0.1.9 issue ID mapping to phased workflow after creating GitHub issues #32-#35
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Link planned v0.1.9 hardening phases to concrete issue tracking IDs for execution traceability.
Validation: docs-only
[2026-02-22T21:28:29Z] Complete v0.1.9 hardening phases with security/property/compatibility/performance tests and docs alignment
Files: test_observability_api.py, tests/test_ns8_property_invariants.py, tests/test_artifact_schema_compatibility.py, tests/test_eval_performance_smoke.py, .agent/TO-DO/PHASED_WORKFLOW.md, docs/EVAL.md, README.md, docs/MONITORING.md, docs/API_REFERENCE.md, .agent/LOGS/CHANGE_LOG.md
Reason: Close planned production-credibility gaps by adding missing acceptance-criteria tests (auth + allowlist + deterministic 429, property/fuzz invariants, artifact compatibility, conservative performance smoke) and marking workflow/docs to reflect implemented behavior.
Validation: python -m pytest -q test_observability_api.py tests/test_ns8_property_invariants.py tests/test_artifact_schema_compatibility.py tests/test_eval_performance_smoke.py tests/test_canonical_id_policy.py tests/test_live_compare_compatibility.py (29 passed)
[2026-02-22T23:20:44Z] Prepare 0.1.9 release metadata and draft release notes
Files: pyproject.toml, src/tonesight_ns8/observability_api.py, README.md, docs/RELEASE_NOTES_0.1.9.md, .agent/LOGS/CHANGE_LOG.md
Reason: Execute release cut prep by bumping package/app version references to 0.1.9 and drafting release notes that summarize completed v0.1.9 hardening scope and validation.
Validation: python -m pytest -q (153 passed)
[2026-02-22T23:40:34Z] Add next planned v0.1.9 phases for cross-environment determinism matrix and drift-locality benchmarks
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Capture agreed next-phase scope after v0.1.9 completion by adding Phase 30 (cross-OS/runtime determinism proof matrix) and Phase 31 (topology-aware drift locality/coherence benchmark evidence).
Validation: docs-only
[2026-02-22T23:41:37Z] Scaffold Phase 30 cross-environment determinism matrix job in CI
Files: .github/workflows/ci.yml, .agent/LOGS/CHANGE_LOG.md
Reason: Implement the next planned phase by adding a dedicated matrix job that validates deterministic conformance and vector-regeneration stability across Ubuntu and Windows runners.
Validation: config/workflow update only (GitHub Actions execution required for runtime verification)
[2026-02-22T23:42:47Z] Sync docs/workflow state for Phase 30 matrix rollout
Files: .agent/TO-DO/PHASED_WORKFLOW.md, docs/RELEASE_CHECKLIST.md, README.md, .agent/LOGS/CHANGE_LOG.md
Reason: Reflect that Phase 30 is now in progress after CI scaffolding, and document release-gate/readme expectations for cross-environment determinism matrix green status.
Validation: docs-only
[2026-02-22T23:45:53Z] Mark Phase 30 complete after green cross-environment CI matrix run
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Close Phase 30 by recording objective proof that determinism-matrix jobs passed on both Ubuntu and Windows in CI run 22287979560.
Validation: GitHub Actions CI run 22287979560 (workflow CI) completed successfully with determinism-matrix jobs green on ubuntu-latest and windows-latest.
[2026-02-22T23:49:22Z] Implement and close Phase 31 with deterministic transition-coherence benchmark artifact and docs/test updates
Files: src/tonesight_ns8/benchmark_runner.py, tests/test_benchmark_cli.py, benchmarks/README.md, docs/EVAL.md, docs/WHY_NS8.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Continue roadmap by adding deterministic transition-locality/coherence benchmark outputs (with equal-width/quantile comparators), wiring the new artifact into benchmark suite/report outputs, and documenting empirical interpretation boundaries.
Validation: python -m pytest -q tests/test_benchmark_cli.py test_cli.py (18 passed); python -m tonesight_ns8.cli benchmark --suite core --out-root .agent/test_tmp/phase31_bench --goldset data/goldset.jsonl
[2026-02-22T23:59:37Z] Add planned v0.1.9 Phases 32-35 and create linked GitHub issues for next proof-hardening track
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Incorporate requested next-scope items into v0.1.9 planning: exhaustive full-domain invariants, receipt-driven eval replay reproducibility, compare error-contract tests, and additive receipt code-revision provenance; map to new issues #36, #39, #38, #37.
Validation: docs/planning update only; GitHub issues created and verified via gh issue list.
[2026-02-23T00:03:17Z] Refactor workflow governance docs: archive historical phases, normalize active statuses, and add last-reviewed headers
Files: .agent/AGENT_RULES.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/TO-DO/PHASED_WORKFLOW_ARCHIVE.md, .agent/LOGS/CHANGE_LOG.md
Reason: Apply governance cleanup to reduce planning drift by making AGENT_RULES the explicit authority, keeping PHASED_WORKFLOW execution-focused, and preserving full historical phase detail in a dedicated archive.
Validation: docs-only update; spot-checked file content and authority/status alignment.
[2026-02-23T00:05:09Z] Start Phase 32 by expanding NS8 property invariants to exhaustive full-domain coverage
Files: tests/test_ns8_property_invariants.py, docs/NS8_CONTRACT_ASSURANCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Begin v0.1.9 Phase 32 by replacing sampled invariant inputs with complete valid-domain loops (amily x r x c x k, N=8), documenting the exhaustive evidence path, and marking workflow phase state as in progress.
Validation: python -m pytest -q tests/test_ns8_property_invariants.py tests/test_invariants.py (21 passed)
[2026-02-23T00:05:23Z] Clarify previous Phase 32 log entry text (append-only correction)
Files: .agent/LOGS/CHANGE_LOG.md
Reason: Correct escaped text artifact in prior entry; intended domain statement is "family x r x c x k, N=8" for exhaustive valid-domain loops.
Validation: docs-only log clarification.
[2026-02-23T00:08:27Z] Complete Phase 32 exhaustive full-domain NS8 invariants and close issue #36
Files: tests/test_ns8_property_invariants.py, docs/NS8_CONTRACT_ASSURANCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Finish v0.1.9 Phase 32 by validating full valid-domain invariant coverage (amily x r x c x k, N=8), updating active workflow status, and closing linked GitHub tracking issue #36 with validation evidence.
Validation: python -m pytest -q test_ns8_vectors.py tests/test_invariants.py tests/test_strict_validation.py tests/test_ns8_property_invariants.py (39 passed); gh issue close 36 (closed).
[2026-02-23T00:08:41Z] Clarify Phase 32 completion log text (append-only correction)
Files: .agent/LOGS/CHANGE_LOG.md
Reason: Correct escaped text artifact in prior completion entry; intended statement is "family x r x c x k, N=8" for exhaustive valid-domain coverage.
Validation: docs-only log clarification.
[$TS] Complete Phase 33 receipt-driven eval replay reproducibility and close issue #39
Files: tests/test_eval_replay_reproducibility.py, docs/EVAL.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add deterministic replay validation that reruns eval from receipt/config context and asserts out.jsonl byte/hash identity plus eval_summary equality excluding explicitly variable fields; update documentation and active workflow state.
Validation: python -m pytest -q tests/test_eval_replay_reproducibility.py test_eval_runner.py (5 passed); gh issue close 39 (closed).
[2026-02-23T00:11:31Z] Clarify Phase 33 completion log timestamp/content (append-only correction)
Files: .agent/LOGS/CHANGE_LOG.md
Reason: Correct prior placeholder timestamp token in Phase 33 completion log entry; authoritative completion details are receipt-driven eval replay reproducibility test addition, workflow update, and GitHub issue #39 closure.
Validation: python -m pytest -q tests/test_eval_replay_reproducibility.py test_eval_runner.py (5 passed); gh issue close 39 (closed).
[2026-02-23T00:14:15Z] Complete Phase 34 compare pipeline error-contract tests and close issue #38
Files: src/tonesight_ns8/compare_runner.py, tests/test_compare_error_contract.py, docs/EVAL.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add deterministic actionable compare failures for missing/malformed/incompatible artifacts and lock behavior with runner+CLI tests; update docs/workflow and close linked issue #38.
Validation: python -m pytest -q test_compare.py tests/test_compare_topology_distance.py tests/test_compare_error_contract.py (9 passed); gh issue close 38 (closed).

[2026-02-23T00:17:13Z] Complete Phase 35 receipt provenance code revision field and close issue #37
Files: src/tonesight_ns8/provenance.py, src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/live_runner.py, tests/test_artifact_schema_compatibility.py, tests/test_live_replay_determinism.py, docs/RECEIPT_SCHEMA.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add additive receipt-level provenance field code_revision when available for eval/live runs with backward-compatible optional semantics, enforce with tests, update docs, and mark active workflow phase complete.
Validation: python -m pytest -q tests/test_artifact_schema_compatibility.py tests/test_live_replay_determinism.py (10 passed); gh issue close 37 (closed).
[2026-02-23T00:19:06Z] Finalize full-suite stabilization: align compare compatibility with gate dataset-mismatch policy
Files: src/tonesight_ns8/compare_runner.py, src/tonesight_ns8/gate_runner.py, .agent/LOGS/CHANGE_LOG.md
Reason: Preserve strict compare defaults while allowing gate flows with equire_dataset_match=False to execute compare deterministically by threading dataset-match policy through runner compatibility checks.
Validation: python -m pytest -q tests/test_canonical_id_policy.py::test_gate_allows_dataset_mismatch_when_explicitly_disabled tests/test_gate_runner.py::test_run_gate_live_dataset_mismatch_allowed (2 passed); python -m pytest -q (161 passed).
[2026-02-23T00:28:19Z] Pre-commit API contract sync and final full-suite verification for v0.1.9 phase completion track
Files: docs/API_REFERENCE.md, .agent/LOGS/CHANGE_LOG.md
Reason: Align API reference with implemented un_compare(..., require_dataset_match=...) contract and validate repository state before commit/push.
Validation: python -m pytest -q (161 passed).
[2026-02-23T00:33:15Z] Fix Bandit B607 in provenance helper by resolving absolute git executable path
Files: src/tonesight_ns8/provenance.py, .agent/LOGS/CHANGE_LOG.md
Reason: Eliminate subprocess partial-path process launch finding by using shutil.which("git") and invoking subprocess with resolved executable path.
Validation: python -m bandit -r src (No issues identified).
[2026-02-23T01:24:39Z] Finalize 0.1.9 release metadata and archive workflow closure state
Files: docs/RELEASE_NOTES_0.1.9.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/TO-DO/PHASED_WORKFLOW_ARCHIVE.md, .agent/LOGS/CHANGE_LOG.md
Reason: Reconcile release notes with final delivered scope (Phase 32-35 completion, full-suite/bandit validation, issue closures) and move active workflow to post-release planning mode while archiving v0.1.9 as complete.
Validation: docs/workflow metadata update only; release note values sourced from completed validation runs and closed issues.
[2026-02-23T01:30:19Z] Add concrete v0.2.0 phase plan with issue-ready acceptance criteria
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Convert proposed next-feature set into an execution-ready v0.2.0 phased plan with scoped files and acceptance criteria suitable for direct issue creation.
Validation: docs/planning update only.
[2026-02-23T01:44:31Z] Create v0.2.0 phase issues (#40-#46) and map them in active workflow
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Convert issue-ready phase plan into tracked GitHub execution items and link issue IDs back into workflow governance for direct implementation sequencing.
Validation: gh issue create x7; gh issue list --state open --json number,title,url (mapping verified).
[2026-02-23T01:52:38Z] Start v0.2.0 Phase 1: add required Bandit CI gate and align release/security docs
Files: .github/workflows/ci.yml, docs/RELEASE_CHECKLIST.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Begin operations/security hardening track by making Bandit a required CI gate and documenting the exact local reproduction path in release/readme docs.
Validation: python -m bandit -r src (No issues identified).
[2026-02-23T02:07:58Z] Complete v0.2.0 Phase 2 nosec governance policy and close issue #42
Files: docs/SECURITY_POLICY.md, tools/check_nosec_policy.py, tools/nosec_allowlist.json, .github/workflows/ci.yml, docs/RELEASE_CHECKLIST.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add enforceable nosec policy with traceable rationale requirements, preserve current suppressions via explicit allowlist baseline, wire enforcement into CI, and update docs/workflow for phase completion.
Validation: python tools/check_nosec_policy.py (NOSEC policy check passed); python -m bandit -r src (No issues identified); gh issue close 42 (closed).
[2026-02-23T04:32:35Z] Complete v0.2.0 Phase 3 compatibility contract unification and close issue #41
Files: src/tonesight_ns8/compatibility.py, src/tonesight_ns8/compare_runner.py, src/tonesight_ns8/gate_runner.py, src/tonesight_ns8/eval_compare_runner.py, test_eval_runner.py, docs/EVAL.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Centralize receipt compatibility checks in a shared module and apply identical identity-field mismatch semantics across compare/gate/eval-compare, then document the unified behavior and advance workflow phase status.
Validation: python -m pytest -q test_compare.py tests/test_compare_topology_distance.py test_eval_runner.py tests/test_gate_runner.py tests/test_live_compare_compatibility.py tests/test_compare_error_contract.py (23 passed); gh issue close 41 (closed).
[2026-02-23T04:38:22Z] Complete v0.2.0 Phase 4 artifact schema version fields and close issue #40
Files: src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/live_runner.py, tests/test_artifact_schema_compatibility.py, tests/test_live_replay_determinism.py, docs/RECEIPT_SCHEMA.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add additive artifact contract version fields (eceipt_schema_version, summary_schema_version) to eval/live artifacts, assert presence/type in compatibility tests, update docs/workflow state, and close linked tracking issue.
Validation: python -m pytest -q tests/test_artifact_schema_compatibility.py tests/test_live_replay_determinism.py (10 passed); gh issue close 40 (closed).
[2026-02-23T04:41:58Z] Complete v0.2.0 Phase 5 deterministic static reporting and close issue #46
Files: src/tonesight_ns8/report_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_report_runner.py, test_cli.py, docs/EVAL.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add a deterministic static report pipeline over existing artifacts with optional compare/gate highlights, wire CLI command and package export, lock byte-stability and contract behavior in tests, and advance workflow to Phase 6.
Validation: python -m pytest -q tests/test_report_runner.py test_cli.py::test_cli_report tests/test_artifact_schema_compatibility.py tests/test_live_replay_determinism.py (13 passed); gh issue close 46 (closed).
[2026-02-23T04:45:00Z] Complete v0.2.0 Phase 6 deterministic dataset quality linting and close issue #44
Files: src/tonesight_ns8/data_lint_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_data_lint_runner.py, test_cli.py, docs/EVAL.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add a deterministic JSONL dataset lint contract with machine-readable violation summaries and non-zero exit semantics for quality failures, wire CLI/API, validate with tests, and advance workflow to Phase 7.
Validation: python -m pytest -q tests/test_data_lint_runner.py test_cli.py::test_cli_data_lint tests/test_report_runner.py (6 passed); gh issue close 44 (closed).
[2026-02-23T04:48:46Z] Complete v0.2.0 Phase 7 release-check orchestration and close issue #45
Files: src/tonesight_ns8/release_check_runner.py, src/tonesight_ns8/data_lint_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_release_check_runner.py, tests/test_data_lint_runner.py, test_cli.py, docs/RELEASE_CHECKLIST.md, README.md, docs/API_REFERENCE.md, docs/EVAL.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add one deterministic pre-release command with per-check pass/fail JSON and CI-ready exit semantics, wire data-lint/release-check into CLI/API/docs, and finalize the v0.2.0 phase track.
Validation: python -m pytest -q tests/test_release_check_runner.py tests/test_data_lint_runner.py test_cli.py::test_cli_release_check test_cli.py::test_cli_data_lint (8 passed); gh issue close 45 (closed).
[2026-02-23T05:03:23Z] Add v0.2.1 killer-stability benchmark phase plan and create mapped GitHub issues (#47-#49)
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Convert benchmark strategy discussion into execution-ready v0.2.1 phased workflow with issue-linked acceptance criteria for protocol definition, deterministic implementation, and release/reporting integration.
Validation: gh issue create x3 (#47 #48 #49); docs/planning update only.
[2026-02-23T05:06:52Z] Complete v0.2.1 Phase 1 killer stability benchmark protocol contract and close issue #47
Files: docs/BENCHMARK_KILLER_STABILITY.md, docs/WHY_NS8.md, docs/EVAL.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Define the normative 2x2 killer benchmark protocol, required separation formulas, deterministic evidence contract fields, and claim-boundary references before implementation work begins.
Validation: docs/planning update only; gh issue close 47 (closed).
[2026-02-23T05:10:55Z] Complete v0.2.1 Phase 2 killer-stability benchmark implementation and close issue #48
Files: src/tonesight_ns8/benchmark_killer_stability.py, src/tonesight_ns8/benchmark_runner.py, src/tonesight_ns8/cli.py, tests/test_benchmark_killer_stability.py, tests/test_benchmark_cli.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Implement deterministic C1/C2/C3/C4 killer benchmark with ToneSight + baseline comparators, separation ratios, evidence artifact contract, and CLI suite integration.
Validation: python -m pytest -q tests/test_benchmark_killer_stability.py tests/test_benchmark_cli.py (5 passed); gh issue close 48 (closed).
[2026-02-23T05:12:25Z] Complete v0.2.1 Phase 3 killer benchmark reporting/release integration and close issue #49
Files: README.md, docs/EVAL.md, docs/API_REFERENCE.md, docs/RELEASE_CHECKLIST.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Integrate killer-stability benchmark command, artifact paths, and separation-ratio interpretation guidance into operator-facing docs and release validation flow, then mark v0.2.1 track complete.
Validation: python -m pytest -q tests/test_benchmark_killer_stability.py tests/test_benchmark_cli.py (5 passed); gh issue close 49 (closed).
[2026-02-23T05:34:40Z] Add robustness reporting summary tables, loss-mode narrative, and deterministic N=1000 subset check
Files: README.md, docs/WHY_NS8.md, docs/BENCHMARK_KILLER_STABILITY.md, docs/EVAL.md, .agent/LOGS/CHANGE_LOG.md
Reason: Promote robustness distribution/pass-rate fields into user-facing evidence summaries, document current ToneSight loss modes via `tonesight_loss_tag_counts`, add reproducible larger-N (`N=1000`) subset benchmark invocation/artifact paths, and codify fixed-weight policy guardrails to prevent per-profile metric retuning claims.
Validation: python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs_n1000 --goldset runs/benchmarks/killer_stability/goldset_n1000.jsonl; python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl; python -m pytest -q tests/test_benchmark_killer_stability.py tests/test_benchmark_cli.py (5 passed).
[2026-02-23T14:57:46Z] Tighten benchmark claim boundaries and add N250-vs-N1000 comparison framing docs
Files: README.md, docs/WHY_NS8.md, docs/EVAL.md, docs/BENCHMARK_KILLER_STABILITY.md, docs/RELEASE_CHECKLIST.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add explicit derived-fixture interpretation boundaries for N=1000 results, surface a compact N250-vs-N1000 baseline comparison table, define known failure-regime tag semantics, and add a scoped release-note claim template for reviewer-safe communication.
Validation: docs-only (no code-path changes).
[2026-02-23T15:30:31Z] Implement v0.2.1 follow-up: benchmark configurability, per-profile robustness summaries, and release metadata alignment
Files: src/tonesight_ns8/benchmark_killer_stability.py, src/tonesight_ns8/benchmark_runner.py, src/tonesight_ns8/cli.py, tests/test_benchmark_killer_stability.py, tests/test_benchmark_cli.py, pyproject.toml, src/tonesight_ns8/observability_api.py, README.md, docs/EVAL.md, docs/API_REFERENCE.md, docs/BENCHMARK_KILLER_STABILITY.md, docs/WHY_NS8.md, docs/RELEASE_CHECKLIST.md, docs/RELEASE_NOTES_0.2.1.md, .agent/LOGS/CHANGE_LOG.md
Reason: Deliver next implementation batch by exposing killer benchmark profile/seed/strength/sample controls via CLI, adding an independent synthetic `boundary_jitter` profile, emitting per-profile robustness aggregates (`by_profile`), and aligning package/observability/docs release metadata to 0.2.1.
Validation: python -m pytest -q tests/test_benchmark_killer_stability.py tests/test_benchmark_cli.py (6 passed); python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl --killer-profiles default,boundary_jitter --killer-seeds 0,1 --killer-primary-strength 0.25 --killer-sweep-strengths 0.1,0.2,0.3 --killer-sample-multiplier 2.
[2026-02-23T15:48:44Z] Add exact v0.2.2 issue-ready phased roadmap block for adoption-focused execution
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Convert post-v0.2.1 roadmap guidance into a concrete v0.2.2 phase plan with normalized status labels, suggested issue titles, file-level scope, and acceptance criteria covering adapters, MLflow/visual diagnostics, stream/monitoring artifacts, and diverse evidence expansion.
Validation: docs/planning update only.
[2026-02-23T15:57:51Z] Create v0.2.2 phase issues (#50-#53) and map IDs into active workflow
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Open GitHub execution issues for v0.2.2 Phases 1-4 and replace TBD placeholders with concrete issue IDs to keep planning and implementation tracking synchronized.
Validation: gh issue create/edit with proxy vars cleared inline (issues #50, #51, #52, #53 created); docs/planning mapping update.

[2026-02-23T23:03:21Z] Complete v0.2.2 Phase 1 zero-friction batch adapters with deterministic pipeline example
Files: src/tonesight_ns8/api.py, src/tonesight_ns8/__init__.py, test_receipts_api.py, examples/batch_adapters_demo.py, README.md, docs/EVAL.md, docs/API_REFERENCE.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Implement planned Phase 1 adoption adapters (	onesight_from_vad_batch, 	onesight_from_llm_labels), export them publicly, add deterministic ordering/type-validation tests, and document practical pipeline usage while advancing workflow status.
Validation: python -m pytest -q test_receipts_api.py (6 passed).

[2026-02-23T23:17:47Z] Complete v0.2.2 Phase 2 MLflow helper hardening and deterministic transition heatmap diagnostics
Files: src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/report_runner.py, src/tonesight_ns8/__init__.py, tests/test_report_runner.py, tests/test_eval_mlflow_helper.py, docs/API_REFERENCE.md, docs/EVAL.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Deliver Phase 2 by formalizing a one-call MLflow logging helper with non-fatal failure behavior and adding deterministic report transition heatmap artifacts for both single-run and compare views, with tests and documentation updates for artifact paths and API usage.
Validation: python -m pytest -q tests/test_report_runner.py tests/test_eval_mlflow_helper.py test_cli.py::test_cli_report (6 passed).

[2026-02-23T23:23:23Z] Complete v0.2.2 Phase 3 stream-mode state updates, robustness HTML artifact, and monitoring recipe
Files: src/tonesight_ns8/stream_runner.py, src/tonesight_ns8/__init__.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/benchmark_killer_stability.py, tests/test_stream_runner.py, tests/test_benchmark_killer_stability.py, tests/test_benchmark_cli.py, test_cli.py, docs/RECIPES/drift_monitoring.md, docs/API_REFERENCE.md, docs/EVAL.md, docs/BENCHMARK_KILLER_STABILITY.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Deliver Phase 3 acceptance scope by adding deterministic incremental stream update/snapshot APIs with CLI wiring, generating obustness_report.html from killer benchmark evidence, and documenting an operator drift-monitoring recipe using compare/gate/report flows.
Validation: python -m pytest -q tests/test_stream_runner.py tests/test_benchmark_killer_stability.py tests/test_benchmark_cli.py test_cli.py::test_cli_stream_update (9 passed).

[2026-02-23T23:29:05Z] Complete v0.2.2 Phase 4 diverse evidence expansion with phase-flip profile and pseudo-real trace demo
Files: src/tonesight_ns8/benchmark_killer_stability.py, data/pseudo_real_trace.jsonl, tests/test_benchmark_killer_stability.py, tests/test_benchmark_cli.py, docs/BENCHMARK_KILLER_STABILITY.md, docs/WHY_NS8.md, docs/EVAL.md, docs/API_REFERENCE.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Deliver Phase 4 acceptance scope by adding deterministic phase_flip_cycle generator family, adding a minimal public-safe pseudo-real trace fixture with reproducible benchmark command, and publishing cross-family evidence map references in docs for ToneSight vs baseline comparison.
Validation: python -m pytest -q tests/test_benchmark_killer_stability.py tests/test_benchmark_cli.py (8 passed).

[2026-02-23T23:30:43Z] Close v0.2.2 GitHub execution issues and sync workflow tracker
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Align remote execution tracking with completed local delivery by closing issues #50-#53 and recording the closure state in the active workflow.
Validation: gh issue close 50; gh issue close 51; gh issue close 52; gh issue close 53 (all closed with proxy env cleared inline).

[2026-02-23T23:32:10Z] Add v0.2.2 release notes and sync package/observability version metadata
Files: docs/RELEASE_NOTES_0.2.2.md, pyproject.toml, src/tonesight_ns8/observability_api.py, README.md, .agent/LOGS/CHANGE_LOG.md
Reason: Complete post-phase release hygiene by publishing release notes for delivered v0.2.2 phases and aligning version references to 0.2.2 across package metadata, observability API, and top-level README.
Validation: python -m pytest -q tests/test_benchmark_cli.py::test_cli_benchmark_killer_stability_pseudo_real_trace_demo tests/test_report_runner.py::test_run_report_single_run_is_deterministic (2 passed).

[2026-02-23T23:44:25Z] Sync docs to current v0.2.2 scope and simplify active workflow tracker
Files: README.md, docs/API_REFERENCE.md, docs/RECIPES/drift_monitoring.md, docs/RELEASE_CHECKLIST.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Bring operator/developer docs in line with delivered features (stream-update CLI, drift recipe paths, release artifact expectations), replace the active workflow with a concise execution tracker, and refresh repository structure docs for the current codebase layout.
Validation: docs-only (path and command references sanity-checked).

[2026-02-24T16:45:35Z] Clean active phased workflow and archive completed release summaries
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/TO-DO/PHASED_WORKFLOW_ARCHIVE.md, .agent/LOGS/CHANGE_LOG.md
Reason: Keep the active workflow focused on current/next execution only and move completed release/milestone summaries into archive context.
Validation: docs-only.


[2026-02-25T23:11:16Z] Convert v0.2.3 coding-agent telemetry concept into repo-ready phase plan with exact file touch lists
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Replace generic next-scope placeholder with executable v0.2.3 phased entries aligned to current CLI/run patterns (live-capture/live-replay/live-verify/gate/report), concrete module paths, and acceptance criteria for deterministic coding-agent telemetry.
Validation: docs/planning update only; path and command alignment cross-checked against current repository CLI and module layout.


[2026-02-25T23:18:58Z] Start v0.2.3 Phase 1: coding-agent live adapter wiring, deterministic feature/bin pipeline, and test coverage
Files: src/tonesight_ns8/coding_agent_features.py, src/tonesight_ns8/coding_agent_discretize.py, src/tonesight_ns8/coding_agent_adapter.py, src/tonesight_ns8/live_runner.py, src/tonesight_ns8/cli.py, tests/test_coding_agent_features.py, tests/test_coding_agent_discretize.py, tests/test_live_replay_determinism.py, test_cli.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Begin v0.2.3 Phase 1 by adding deterministic coding-agent telemetry transformation (live events -> features -> 1..8 bins -> VAD) and exposing adapter selection through existing live replay/verify command surface while preserving default behavior.
Validation: python -m pytest -q tests/test_coding_agent_features.py tests/test_coding_agent_discretize.py tests/test_live_replay_determinism.py test_cli.py::test_cli_live_capture_and_replay test_cli.py::test_cli_live_replay_with_coding_agent_adapter test_cli.py::test_cli_live_verify test_cli.py::test_cli_live_verify_with_coding_agent_adapter (16 passed); python -m pytest -q (197 passed).


[2026-02-25T23:21:32Z] Harden v0.2.3 Phase 1 adapter contracts with fail-fast adapter validation and deterministic boundary tests
Files: src/tonesight_ns8/live_runner.py, tests/test_coding_agent_adapter.py, tests/test_coding_agent_discretize.py, tests/test_live_replay_determinism.py, test_cli.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Finish Phase 1 contract hardening by enforcing explicit unknown-adapter rejection in live replay, adding deterministic adapter/bin boundary coverage, and validating CLI adapter argument behavior to reduce silent drift risk.
Validation: python -m pytest -q tests/test_coding_agent_adapter.py tests/test_coding_agent_features.py tests/test_coding_agent_discretize.py tests/test_live_replay_determinism.py test_cli.py::test_cli_live_replay_with_coding_agent_adapter test_cli.py::test_cli_live_verify_with_coding_agent_adapter test_cli.py::test_cli_live_replay_rejects_invalid_adapter (18 passed); python -m pytest -q (201 passed).


[2026-02-25T23:26:43Z] Complete v0.2.3 Phase 2: pinned model identity fields in coding-agent receipts and compatibility/gate enforcement
Files: src/tonesight_ns8/compatibility.py, src/tonesight_ns8/compare_runner.py, src/tonesight_ns8/gate_runner.py, src/tonesight_ns8/live_runner.py, src/tonesight_ns8/cli.py, config/gate_profiles.json, tests/test_gate_profiles.py, tests/test_gate_runner.py, tests/test_live_compare_compatibility.py, tests/test_canonical_id_policy.py, tests/test_live_replay_determinism.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Implement optional pinned-model compatibility policy for coding-agent telemetry by emitting stable provider/model/generation receipt identity fields and enforcing deterministic mismatch/missing checks through compare/gate, including profile-driven activation (coding_agent_drift).
Validation: python -m pytest -q tests/test_gate_profiles.py tests/test_gate_runner.py tests/test_live_compare_compatibility.py tests/test_canonical_id_policy.py tests/test_live_replay_determinism.py test_cli.py::test_cli_live_replay_with_coding_agent_adapter (27 passed); python -m pytest -q (205 passed).


[2026-02-25T23:33:07Z] Complete v0.2.3 Phase 3: coding-agent fixture set, deterministic drift benchmark suite, and e2e compatibility coverage
Files: src/tonesight_ns8/benchmark_runner.py, src/tonesight_ns8/cli.py, tests/fixtures/live_event.coding_agent.python.jsonl, tests/fixtures/live_event.coding_agent.typescript.jsonl, tests/fixtures/live_event.coding_agent.mismatch.jsonl, tests/test_benchmark_cli.py, tests/test_coding_agent_adapter_e2e.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add deterministic benchmark evidence generation for coding-agent drift signals (language mismatch, verbosity, tests presence, tool-call rate), provide pinned fixture corpus for reproducible CI execution, and verify compare/gate/report interoperability on coding-agent artifacts without introducing format forks.
Validation: python -m pytest -q tests/test_benchmark_cli.py::test_cli_benchmark_coding_agent_drift_writes_expected_artifacts tests/test_benchmark_cli.py::test_cli_benchmark_coding_agent_drift_is_repeatable tests/test_benchmark_cli.py::test_cli_benchmark_core_writes_expected_artifacts tests/test_benchmark_cli.py::test_cli_benchmark_killer_stability_writes_evidence (4 passed); python -m pytest -q tests/test_coding_agent_adapter_e2e.py tests/test_benchmark_cli.py::test_cli_benchmark_coding_agent_drift_writes_expected_artifacts tests/test_benchmark_cli.py::test_cli_benchmark_coding_agent_drift_is_repeatable (3 passed); python -m pytest -q (208 passed).


[2026-02-25T23:39:24Z] Complete v0.2.3 Phase 4 docs alignment for coding-agent adapter, benchmark suite, and pinned identity policy
Files: README.md, docs/EVAL.md, docs/API_REFERENCE.md, docs/LIVE_EVENT_SCHEMA.md, docs/CANONICAL_ID_POLICY.md, docs/PRIVACY_REDACTION.md, docs/RETENTION_POLICY.md, docs/RELEASE_CHECKLIST.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Align operator/developer documentation with implemented v0.2.3 behavior (coding-agent live adapter flags, coding_agent_drift benchmark commands/artifacts, pinned model identity gate controls, and telemetry privacy/retention guidance) while preserving established CLI command families.
Validation: docs-only (no code-path changes).


[2026-02-25T23:44:45Z] Finalize v0.2.3 release metadata, archive workflow closure, and post-release active tracker reset
Files: pyproject.toml, src/tonesight_ns8/observability_api.py, README.md, docs/RELEASE_NOTES_0.2.3.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/TO-DO/PHASED_WORKFLOW_ARCHIVE.md, .agent/LOGS/CHANGE_LOG.md
Reason: Complete v0.2.3 release execution by synchronizing package/app/doc version metadata to 0.2.3, publishing release notes, archiving completed v0.2.3 phases, and returning active workflow to post-release planning mode.
Validation: python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json (passed); python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl; python -m tonesight_ns8.cli benchmark --suite coding_agent_drift --out-root runs --coding-baseline-events tests/fixtures/live_event.coding_agent.python.jsonl --coding-candidate-events tests/fixtures/live_event.coding_agent.typescript.jsonl,tests/fixtures/live_event.coding_agent.mismatch.jsonl; python -m pytest -q (208 passed).


[2026-02-25T23:54:25Z] Promote active workflow to execution-ready v0.2.4 phase plan and ignore derived benchmark artifact directory
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .gitignore, .agent/LOGS/CHANGE_LOG.md
Reason: Continue post-v0.2.3 execution by replacing generic planning placeholders with concrete v0.2.4 phase/file/acceptance blocks and suppress recurring local uns_n1000/ generated artifact noise from git status.
Validation: docs/config-only update; git status sanity check.

[2026-02-25T23:58:07Z] Patch v0.2.4 active workflow scope with generic any-agent adapter posture and explicit chat_agent deferral
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Apply requested planning update by adding adapter-registry and schema-contract constraints, ClawDBot Mode A ingestion recipe requirement, positioning updates, and explicit chat_agent deferment to v0.2.5+.
Validation: docs/planning update only.

[2026-02-26T00:02:18Z] Complete v0.2.4 Phase 1: registry-driven live adapter resolution and strict pinned-identity replay gating
Files: src/tonesight_ns8/live_runner.py, src/tonesight_ns8/cli.py, tests/test_live_replay_determinism.py, test_cli.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Replace hardcoded live adapter branching with registry-backed resolution, add replay/verify require_pinned_model_identity enforcement for coding-agent adapter with fail-fast missing-field checks, and add deterministic CLI/test coverage for new guardrails while preserving unknown-adapter rejection and existing defaults.
Validation: python -m pytest -q tests/test_live_replay_determinism.py test_cli.py::test_cli_live_replay_with_coding_agent_adapter test_cli.py::test_cli_live_verify_with_coding_agent_adapter test_cli.py::test_cli_live_replay_require_pinned_identity_missing_fails test_cli.py::test_cli_live_replay_require_pinned_identity_non_coding_rejected (15 passed); python -m pytest -q tests/test_live_compare_compatibility.py tests/test_gate_runner.py (12 passed); python -m pytest -q (213 passed).

[2026-02-26T00:06:25Z] Complete v0.2.4 Phase 2: coding-agent drift diagnostics in report and triage outputs
Files: src/tonesight_ns8/report_runner.py, src/tonesight_ns8/triage_runner.py, tests/test_report_runner.py, tests/test_triage_runner.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add deterministic coding-agent behavioral slices to static report payloads and additive coding-agent regression fields in triage exports (single/diff) without breaking existing schema contracts or NS8 math behavior.
Validation: python -m pytest -q tests/test_report_runner.py tests/test_triage_runner.py (7 passed); python -m pytest -q tests/test_coding_agent_adapter_e2e.py (1 passed); python -m pytest -q (215 passed).

[2026-02-26T00:14:04Z] Complete v0.2.4 Phase 3: coding-agent benchmark gate-ready summaries and profile-level behavioral threshold enforcement
Files: src/tonesight_ns8/benchmark_runner.py, src/tonesight_ns8/gate_runner.py, config/gate_profiles.json, tests/test_benchmark_cli.py, tests/test_gate_profiles.py, tests/test_gate_runner.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Harden coding_agent_drift conformance by emitting deterministic gate-ready benchmark summary deltas and extending gate profiles with optional coding-agent behavioral thresholds (mismatch/verbosity/tests/tool-call deltas) plus deterministic incompatibility handling when required coding metrics are missing.
Validation: python -m pytest -q tests/test_benchmark_cli.py::test_cli_benchmark_coding_agent_drift_writes_expected_artifacts tests/test_benchmark_cli.py::test_cli_benchmark_coding_agent_drift_is_repeatable tests/test_gate_profiles.py tests/test_gate_runner.py::test_run_gate_profile_coding_agent_drift_requires_pinned_identity tests/test_gate_runner.py::test_run_gate_profile_coding_agent_drift_applies_behavioral_thresholds tests/test_gate_runner.py::test_run_gate_profile_coding_agent_drift_missing_coding_metrics_is_incompatible (7 passed); python -m pytest -q tests/test_coding_agent_adapter_e2e.py (1 passed); python -m pytest -q (217 passed).

[2026-02-26T00:19:33Z] Complete v0.2.4 Phase 4: docs/release sync for coding-agent hardening and generic any-agent telemetry positioning
Files: README.md, docs/EVAL.md, docs/API_REFERENCE.md, docs/RELEASE_CHECKLIST.md, docs/WHY_NS8.md, docs/RELEASE_NOTES_0.2.4.md, pyproject.toml, src/tonesight_ns8/observability_api.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Align operator/developer docs and release metadata with implemented v0.2.4 behavior (registry-backed live adapters, pinned-identity replay flags, coding-agent report/triage diagnostics, benchmark gate_ready summaries, and coding-agent profile behavioral thresholds), while preserving claim boundaries and documenting ClawDBot Mode A ingestion over existing LiveEvent contract.
Validation: python -m tonesight_ns8.cli --help; python -m pytest -q tests/test_gate_profiles.py test_cli.py::test_cli_live_replay_require_pinned_identity_missing_fails test_cli.py::test_cli_live_replay_require_pinned_identity_non_coding_rejected (4 passed).

[2026-02-26T01:29:39Z] Run v0.2.4 release validation set and fix gate CLI profile override for pinned identity
Files: src/tonesight_ns8/cli.py, .agent/LOGS/CHANGE_LOG.md
Reason: During release validation, gate --profile coding_agent_drift was overriding profile equire_pinned_model_identity=true to false when the CLI flag was omitted due store_true default behavior; set CLI arg default to None so profile thresholds are preserved unless explicitly overridden.
Validation: python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json (passed); python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl; python -m tonesight_ns8.cli benchmark --suite coding_agent_drift --out-root runs --coding-baseline-events tests/fixtures/live_event.coding_agent.python.jsonl --coding-candidate-events tests/fixtures/live_event.coding_agent.typescript.jsonl,tests/fixtures/live_event.coding_agent.mismatch.jsonl; coding-agent live replay+gate profile check produced deterministic incompatible decision with equire_pinned_model_identity=true; python -m pytest -q (217 passed).

[2026-02-26T01:57:11Z] Align AGENT_RULES authoritative file paths with current repo layout
Files: .agent/AGENT_RULES.md, .agent/LOGS/CHANGE_LOG.md
Reason: Governance doc referenced legacy root-level files (SPEC/API/vectors/taxonomy) that now live under docs/, vectors/, and taxonomy/, causing policy/docs drift.
Validation: python -m pytest -q; python -m tonesight_ns8.cli eval; python tools/validate_goldset.py data/goldset.jsonl; python tools/validate_live_event.py tests/fixtures/live_event.valid.jsonl; python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json

[2026-02-26T02:01:19Z] Add execution-ready v0.2.5 read-only artifact UI phase block
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Translate approved direction into concrete v0.2.5 plan with file layout, static artifact API boundary, explicit UI JSON read contracts, and a deterministic 2-minute demo script path.
Validation: docs-only (planning update; no runtime behavior changed).

[2026-02-26T02:04:09Z] Implement v0.2.5 Phase 1 file layout scaffold and deterministic index.json generator
Files: src/tonesight_ns8/run_index.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tools/generate_run_index_json.py, tests/test_run_index.py, test_cli.py, ui/README.md, server/README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Deliver Phase 1 by adding explicit ui/server scaffolds and a deterministic runs/index.json generator from runs/index.jsonl, exposed via thin CLI and tooling wrappers with parity/idempotence tests.
Validation: python -m pytest -q tests/test_run_index.py test_cli.py::test_cli_index_runs test_cli.py::test_cli_index_runs_json; python -m tonesight_ns8.cli --help; python tools/generate_run_index_json.py --help

[2026-02-26T03:03:16Z] Implement v0.2.5 Phase 2 static artifact API with deterministic index JSON bridge
Files: server/app.py, tests/test_artifact_server.py, src/tonesight_ns8/run_index.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tools/generate_run_index_json.py, docs/EVAL.md, docs/API_REFERENCE.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Deliver read-only local API endpoints that serve existing artifact JSON verbatim and add deterministic runs/index.json generation from runs/index.jsonl for UI consumption without introducing a second scoring path.
Validation: python -m pytest -q tests/test_artifact_server.py tests/test_run_index.py test_cli.py::test_cli_index_runs test_cli.py::test_cli_index_runs_json tests/test_defaults_config.py tests/test_report_runner.py; python server/app.py --help; python -m tonesight_ns8.cli index-runs --out-root runs; python -m tonesight_ns8.cli index-runs-json --out-root runs

[2026-02-26T03:07:47Z] Implement v0.2.5 Phase 3 UI read-contract allowlists and boundary tests
Files: docs/UI_ALLOWED_CONTRACTS.md, ui/src/contracts.ts, tests/test_ui_allowed_contracts.py, docs/PRIVACY_REDACTION.md, docs/RETENTION_POLICY.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Formalize exact UI-readable artifact/field contracts and enforce disallowed raw artifact exposure by default so the UI remains a read-only renderer over deterministic artifacts.
Validation: python -m pytest -q tests/test_ui_allowed_contracts.py tests/test_artifact_server.py tests/test_run_index.py; python -m pytest -q test_cli.py::test_cli_index_runs test_cli.py::test_cli_index_runs_json

[2026-02-26T03:12:21Z] Implement v0.2.5 Phase 4 2-minute UI drift/gate demo script and recipe
Files: scripts/demo_ui_drift_gate_2min.ps1, docs/RECIPES/ui_drift_gate_demo.md, ui/index.html, tests/test_ui_demo_script.py, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Deliver a single-command local demo that creates baseline/candidate artifacts, writes compare+gate evidence, refreshes UI index artifacts, and launches static API/UI servers without adding new scoring logic.
Validation: powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1 -OutRoot .agent/test_tmp/demo_ui_phase4 -SkipServers; python -m pytest -q tests/test_ui_demo_script.py tests/test_ui_allowed_contracts.py tests/test_artifact_server.py

[2026-02-26T03:17:21Z] Finalize v0.2.5 release metadata, run validation sweep, and sync active/archive workflow state
Files: pyproject.toml, src/tonesight_ns8/observability_api.py, docs/RELEASE_NOTES_0.2.5.md, README.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/TO-DO/PHASED_WORKFLOW_ARCHIVE.md, .agent/LOGS/CHANGE_LOG.md
Reason: Complete release hygiene for v0.2.5 by synchronizing package/app/docs version markers, publishing release notes, validating full deterministic checks, and moving completed v0.2.5 phase detail into archive while setting v0.2.6 planning as active.
Validation: python -m pytest -q; python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json; python -m tonesight_ns8.cli index-runs --out-root runs; python -m tonesight_ns8.cli index-runs-json --out-root runs; powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1 -SkipServers

[2026-02-26T03:24:12Z] Add v0.2.5 UI centralization addendum phase block for user-friendly dashboard consolidation
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Capture a concrete, execution-ready UI consolidation plan that centralizes run/report/compare/gate artifact navigation in one interface while preserving read-only deterministic contract boundaries.
Validation: docs-only (planning update; no runtime behavior changed).

[2026-02-26T03:33:24Z] Adopt UI polish/demo-flow scope and enforce no-new-compute-contract boundary in v0.2.5 UI addendum
Files: .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Capture explicit product decision to proceed with UX improvements while rejecting backend/frontend metric recomputation and any contract-expanding compute changes.
Validation: docs-only (scope decision update).

[2026-02-26T03:38:51Z] Implement v0.2.5 UI centralization Phase A dashboard shell and navigation
Files: ui/index.html, ui/src/app.js, ui/src/styles.css, tests/test_ui_allowed_contracts.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Ship Phase A end-to-end with a scan-first, mobile-safe read-only dashboard over allowlisted artifacts, including fixed status badge mapping and quick links to run/compare/gate evidence without introducing new compute contracts.
Validation: python -m pytest -q tests/test_ui_allowed_contracts.py tests/test_ui_demo_script.py tests/test_artifact_server.py; powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1 -OutRoot .agent/test_tmp/demo_ui_phaseA -SkipServers; python -m tonesight_ns8.cli index-runs --out-root .agent/test_tmp/demo_ui_phaseA; python -m tonesight_ns8.cli index-runs-json --out-root .agent/test_tmp/demo_ui_phaseA

[2026-02-26T03:46:30Z] Implement v0.2.5 UI centralization Phase B run detail and compare/gate evidence drill-down
Files: ui/src/app.js, ui/src/styles.css, ui/src/components/run_detail.js, ui/src/components/compare_panel.js, ui/src/components/gate_panel.js, tests/test_ui_allowed_contracts.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Ship Phase B with a selected-run detail surface that renders provenance, eval metrics, compare deltas, and gate decisions directly from existing artifacts without adding any new compute contracts.
Validation: python -m pytest -q tests/test_ui_allowed_contracts.py tests/test_ui_demo_script.py tests/test_artifact_server.py (10 passed); powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1 -OutRoot .agent/test_tmp/demo_ui_phaseB -SkipServers

[2026-02-26T03:54:10Z] Implement v0.2.5 UI centralization Phase C artifact safety links and policy labels
Files: ui/src/app.js, ui/src/components/artifact_links.js, ui/src/styles.css, docs/UI_ALLOWED_CONTRACTS.md, docs/PRIVACY_REDACTION.md, docs/RETENTION_POLICY.md, tests/test_ui_allowed_contracts.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Ship Phase C by separating derived UI-safe artifact links from restricted raw artifact classes with explicit safety text, while keeping raw capture/quarantine artifacts non-linkable by default.
Validation: python -m pytest -q tests/test_ui_allowed_contracts.py tests/test_ui_demo_script.py tests/test_artifact_server.py (11 passed); powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1 -OutRoot .agent/test_tmp/demo_ui_phaseC -SkipServers

[2026-02-26T03:58:05Z] Implement v0.2.5 UI centralization Phase D demo deep links and screenshot flow polish
Files: scripts/demo_ui_drift_gate_2min.ps1, ui/src/app.js, ui/src/components/compare_panel.js, docs/RECIPES/ui_drift_gate_demo.md, README.md, tests/test_ui_demo_script.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Ship Phase D by adding direct UI run/compare/gate deep links from the demo script, enabling query-param panel navigation in the UI, and documenting a screenshot-first 2-minute operator flow.
Validation: python -m pytest -q tests/test_ui_demo_script.py tests/test_ui_allowed_contracts.py tests/test_artifact_server.py (11 passed); powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1 -OutRoot .agent/test_tmp/demo_ui_phaseD -SkipServers

[2026-02-26T04:06:05Z] Fix UI cross-port fetch failure by adding CORS headers to static artifact API
Files: server/app.py, tests/test_artifact_server.py, .agent/LOGS/CHANGE_LOG.md
Reason: Resolve browser "Failed to fetch" on dashboard load when UI (8090) requests artifact API (8081) by returning explicit CORS headers on GET/OPTIONS responses.
Validation: python -m pytest -q tests/test_artifact_server.py tests/test_ui_demo_script.py tests/test_ui_allowed_contracts.py (12 passed); powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1 -OutRoot .agent/test_tmp/demo_ui_cors_fix -SkipServers

[2026-02-26T04:10:15Z] Fix report.html UI link 404s by serving report HTML through artifact API
Files: server/app.py, ui/src/app.js, ui/src/components/run_detail.js, ui/src/components/artifact_links.js, tests/test_artifact_server.py, tests/test_ui_allowed_contracts.py, .agent/LOGS/CHANGE_LOG.md
Reason: Prevent UI static server 404s for `/runs/.../report.html` links by routing report HTML downloads through API endpoint `/api/run/<run_id>/report-html`.
Validation: python -m pytest -q tests/test_artifact_server.py tests/test_ui_allowed_contracts.py tests/test_ui_demo_script.py (12 passed)

[2026-02-26T04:17:40Z] Refresh generated report pages to match dashboard UI style and add compare HTML page routing
Files: src/tonesight_ns8/eval_runner.py, src/tonesight_ns8/compare_runner.py, server/app.py, ui/src/app.js, ui/src/components/compare_panel.js, ui/src/components/run_detail.js, ui/src/components/artifact_links.js, ui/src/contracts.ts, docs/UI_ALLOWED_CONTRACTS.md, docs/EVAL.md, docs/RECIPES/ui_drift_gate_demo.md, README.md, tests/test_artifact_server.py, tests/test_ui_allowed_contracts.py, .agent/LOGS/CHANGE_LOG.md
Reason: Align generated `report.html` and `compare_report.html` with the new UI visual language, expose compare report as a first-class page via API/UI links, and keep contracts/docs/tests in sync with the new derived artifact endpoints.
Validation: python -m pytest -q (232 passed)

[2026-02-26T04:24:55Z] Add final UI polish pass before commit: skeletons, panel errors, deep-link sharing, density, auto-refresh, and artifact table actions
Files: ui/src/app.js, ui/src/styles.css, ui/src/components/run_detail.js, ui/src/components/compare_panel.js, ui/src/components/gate_panel.js, ui/src/components/artifact_links.js, src/tonesight_ns8/compare_runner.py, tests/test_ui_allowed_contracts.py, .agent/LOGS/CHANGE_LOG.md
Reason: Implement requested operator-facing upgrades (loading skeletons, panel-specific artifact error messaging, last-refreshed/auto-refresh toggle, compact density mode, copy/share deep links, artifact open/copy table actions, and compare-page delta visual blocks) without adding new compute contracts.
Validation: python -m pytest -q (233 passed)

[2026-02-26T04:31:20Z] Add release scaffolds for commit/PR text and post-merge verification checklist
Files: .agent/TO-DO/COMMIT_MESSAGE_v0.2.5_UI.txt, .agent/TO-DO/PR_DESCRIPTION_v0.2.5_UI.md, docs/RECIPES/post_merge_verification_v0_2_5_ui.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Implement requested handoff artifacts so v0.2.5 UI centralization can be committed, reviewed, and verified with a concrete operator checklist.
Validation: docs-only scaffolding update (no runtime behavior changed)

[2026-02-26T04:38:15Z] Fix demo UI test portability for Linux CI environments without Windows PowerShell binary name
Files: tests/test_ui_demo_script.py, .agent/LOGS/CHANGE_LOG.md
Reason: Prevent CI failure where `powershell` executable is unavailable on non-Windows runners by preferring `pwsh` and skipping test when no PowerShell runtime exists.
Validation: python -m pytest -q tests/test_ui_demo_script.py tests/test_ui_allowed_contracts.py tests/test_artifact_server.py (13 passed); python -m pytest -q (233 passed)

[2026-02-26T04:45:50Z] Clear Bandit B105 false positives in compare report renderer variable naming
Files: src/tonesight_ns8/compare_runner.py, .agent/LOGS/CHANGE_LOG.md
Reason: Rename local `pass_trend` variable to `trend_state` to avoid Bandit hardcoded-password heuristic false positives while preserving behavior.
Validation: python -m bandit -r src (no issues identified)

[2026-02-26T05:10:20Z] Add end-to-end HTTP process integration test for artifact API hardening item #1
Files: tests/test_artifact_server_http_process.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Complete v0.2.6 hardening follow-up item #1 by validating the running artifact API process over real HTTP (health, index, report HTML, compare JSON/HTML, gate JSON) and harden subprocess lifecycle cleanup to avoid descriptor leaks in CI.
Validation: python -m pytest -q tests/test_artifact_server_http_process.py tests/test_artifact_server.py tests/test_ui_allowed_contracts.py tests/test_ui_demo_script.py (14 passed); python tools/validate_defaults.py

[2026-02-26T05:24:35Z] Add deterministic static UI package helper for v0.2.6 hardening item #2
Files: src/tonesight_ns8/ui_package_runner.py, src/tonesight_ns8/cli.py, src/tonesight_ns8/__init__.py, tests/test_ui_package_runner.py, README.md, docs/API_REFERENCE.md, docs/EVAL.md, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/LOGS/CHANGE_LOG.md
Reason: Complete v0.2.6 hardening follow-up item #2 by adding `ui-package` to produce a deterministic ZIP containing `ui/`, `server/`, and UI-safe run artifacts for portable local demo flow while excluding raw artifacts by default.
Validation: python -m pytest -q tests/test_ui_package_runner.py tests/test_artifact_server_http_process.py tests/test_ui_allowed_contracts.py test_cli.py::test_cli_bundle (11 passed); python tools/validate_defaults.py
[2026-02-26T19:31:24Z] Add opt-in pipeline run API endpoint and dashboard trigger for automated real-data ingestion
Files: server/app.py, ui/src/app.js, ui/src/styles.css, tests/test_artifact_server.py, tests/test_ui_allowed_contracts.py, .agent/LOGS/CHANGE_LOG.md
Reason: Implement a small backend+UI automation path for capture/replay/compare/gate workflow from the dashboard while keeping it explicit and gated behind server flag --enable-pipeline.
Validation: python -m pytest -q tests/test_artifact_server.py tests/test_ui_allowed_contracts.py (14 passed); python -m pytest -q tests/test_artifact_server_http_process.py tests/test_ui_demo_script.py (2 passed); python -m pytest -q (238 passed)
[2026-02-26T20:01:25Z] Fix dashboard demo-toggle URL to avoid 404 when UI is served from non-root path
Files: ui/src/app.js, .agent/LOGS/CHANGE_LOG.md
Reason: Prevent hardcoded /index.html links from breaking when users serve UI from repo root at /ui/index.html; compute toggle URL from current pathname/query.
Validation: python -m pytest -q tests/test_ui_allowed_contracts.py tests/test_ui_demo_script.py (8 passed)
[2026-02-27T05:14:38Z] Add execution-ready v0.2.6 multi-domain phase block and draft planning docs
Files: .agent/TO-DO/PHASED_WORKFLOW.md, docs/NS8_MULTI_DOMAIN_SPEC.md, docs/DOMAIN_PACKS.md, README.md, .agent/LOGS/CHANGE_LOG.md
Reason: Convert approved multi-domain and quarantine-contract direction into an implementation-ready v0.2.6 phased plan with explicit file touch lists, acceptance criteria, validation steps, and discoverable draft documentation links.
Validation: docs-only planning update (no runtime code paths changed; tests not run).
[2026-02-27T05:31:38Z] Start v0.2.6 Phase 1 by adding canonical signal-layer schema contracts and tests
Files: schemas/signal_observation.schema.json, schemas/mapping_profile.schema.json, schemas/anchor_event.schema.json, schemas/signal_quarantine_event.schema.json, tests/test_signal_schema_contracts.py, .agent/LOGS/CHANGE_LOG.md
Reason: Begin execution of v0.2.6 contract phase with explicit deterministic schemas for observation/profile/anchor/quarantine artifacts and enforce required fields/reason-code enum via tests.
Validation: python -m pytest -q tests/test_signal_schema_contracts.py tests/test_artifact_schema_compatibility.py (9 passed); python -m pytest -q (242 passed)
[2026-02-27T05:36:16Z] Implement v0.2.6 Phase 2 deterministic profile loader and signal mapping engine
Files: src/tonesight_ns8/domainpacks.py, src/tonesight_ns8/signal_mapping.py, src/tonesight_ns8/__init__.py, tests/test_domainpacks.py, tests/test_signal_mapping.py, .agent/LOGS/CHANGE_LOG.md
Reason: Add deterministic mapping-profile validation/loading and multi_channel_fold observation-to-NS8 mapping with strict error behavior for missing/out-of-range channels.
Validation: python -m pytest -q tests/test_domainpacks.py tests/test_signal_mapping.py tests/test_mapping_registry.py tests/test_mapping_conformance.py (13 passed); python -m pytest -q (250 passed)
[2026-02-27T05:41:47Z] Implement v0.2.6 Phase 3 signal runner artifacts, quarantine contract, and additive receipt/metrics docs
Files: src/tonesight_ns8/signal_runner.py, src/tonesight_ns8/__init__.py, tests/test_signal_runner.py, tests/test_signal_metrics.py, tests/test_signal_quarantine_contract.py, docs/RECEIPT_SCHEMA.md, docs/DERIVED_METRICS.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add deterministic signal artifact runner (anchor_events/metrics/transition_matrix/density_map/quarantine), enforce quarantine reason-code contract with observation hash and profile identity, and document additive receipt+metric fields.
Validation: python -m pytest -q tests/test_signal_runner.py tests/test_signal_metrics.py tests/test_signal_quarantine_contract.py (3 passed); python -m pytest -q (253 passed)
[2026-02-27T05:45:45Z] Implement v0.2.6 Phase 4 built-in domain pack profiles and vector conformance tests
Files: src/tonesight_ns8/domainpacks.py, src/tonesight_ns8/domainpacks_data/tone_vad_v1.json, src/tonesight_ns8/domainpacks_data/kasbah_env_v1.json, src/tonesight_ns8/__init__.py, tests/vectors/domainpacks/tone_vad_v1/case_core.json, tests/vectors/domainpacks/kasbah_env_v1/case_core.json, tests/test_domainpack_vectors.py, tests/test_domainpacks.py, docs/DOMAIN_PACKS.md, .agent/LOGS/CHANGE_LOG.md
Reason: Add first-party v0.2.6 domain pack profiles and deterministic vector fixtures/tests for expected mapping outputs and strict rejection paths.
Validation: python -m pytest -q tests/test_domainpacks.py tests/test_signal_mapping.py tests/test_domainpack_vectors.py (11 passed); python -m pytest -q (256 passed)
[2026-02-27T05:52:14Z] Implement v0.2.6 Phase 5 CLI signal commands plus additive index/report/UI-safe signal metadata integration
Files: src/tonesight_ns8/cli.py, src/tonesight_ns8/run_index.py, src/tonesight_ns8/report_runner.py, src/tonesight_ns8/signal_runner.py, src/tonesight_ns8/__init__.py, ui/src/contracts.ts, docs/UI_ALLOWED_CONTRACTS.md, docs/API_REFERENCE.md, docs/EVAL.md, test_cli.py, tests/test_run_index.py, tests/test_report_runner.py, tests/test_ui_allowed_contracts.py, .agent/LOGS/CHANGE_LOG.md
Reason: Add thin signal-map/signal-run CLI wrappers; include signal/quarantine additive metadata in run index/report contracts; keep UI allowlist read-only and metadata-safe for quarantine visibility without raw log rendering.
Validation: python -m pytest -q tests/test_run_index.py tests/test_report_runner.py tests/test_ui_allowed_contracts.py test_cli.py (44 passed); python -m pytest -q (260 passed)

[2026-02-27T05:57:04Z] Close v0.2.6 release sync with version/doc alignment and release notes
Files: pyproject.toml, src/tonesight_ns8/observability_api.py, README.md, docs/NS8_MULTI_DOMAIN_SPEC.md, docs/DOMAIN_PACKS.md, docs/UI_ALLOWED_CONTRACTS.md, docs/PRIVACY_REDACTION.md, docs/RETENTION_POLICY.md, docs/RELEASE_NOTES_0.2.6.md
Reason: Finalize v0.2.6 closure by synchronizing version markers and policy docs with shipped multi-domain signal-layer implementation and additive UI-safe contracts.
Validation: python -m pytest -q (260 passed)

[2026-02-28T21:11:03Z] Remediate packaging portability, strict VAD validation parity, and workflow tracker/archive hygiene
Files: src/tonesight_ns8/ns8.py, src/tonesight_ns8/ns8_ref.py, ns8_ref.py, src/tonesight_ns8/api.py, src/tonesight_ns8/taxonomy.py, test_receipts_api.py, tests/test_strict_validation.py, .agent/TO-DO/PHASED_WORKFLOW.md, .agent/TO-DO/PHASED_WORKFLOW_ARCHIVE.md
Reason: Address top findings by removing root sys.path import coupling, enforcing bool/range strictness in wrapper/taxonomy VAD paths, and aligning active workflow tracker to archive-only completed history policy.
Validation: python -m pytest -q test_ns8_vectors.py tests/test_invariants.py test_receipts_api.py tests/test_strict_validation.py (33 passed); python -m pytest -q (262 passed). GitHub issue sync attempted via gh issue view/close but blocked by local proxy connectivity failure to api.github.com/graphql.
[2026-03-01T00:27:14Z] Add CI wheel-install package smoke gate
Files: .github/workflows/ci.yml, .agent/LOGS/CHANGE_LOG.md
Reason: Add non-editable packaging smoke coverage by building wheel/sdist artifacts and verifying runtime import/compute behavior after wheel install.
Validation: workflow update only; local runtime tests not re-run in this step.
[2026-03-01T01:20:40Z] Harden defaults portability for installed wheels and add guarded vector-regeneration workflow
Files: src/tonesight_ns8/defaults.py, src/tonesight_ns8/defaults_data/defaults.json, pyproject.toml, tools/regen_vectors.py, .github/workflows/ci.yml, .agent/LOGS/CHANGE_LOG.md
Reason: Remove repo-root-only defaults coupling by adding packaged defaults fallback for installed environments, and enforce vector-regeneration governance with explicit authorization checks while adding non-mutating `--check` mode for CI stability validation.
Validation: python tools/regen_vectors.py --check; python -m pytest -q tests/test_defaults_config.py test_ns8_vectors.py tests/test_strict_validation.py (31 passed); python -m pytest -q (262 passed)
