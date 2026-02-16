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


[2026-02-14T19:05:22Z] Implement Path B monitoring stack in requested order (workflow activation, Docker services, FastAPI metrics API, Prometheus/Grafana configs, docs runbook, smoke tests)
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


