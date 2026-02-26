# ToneSight NS8 `0.2.4` Release Notes

Release date: `2026-02-26`

This release completes the `v0.2.4` coding-agent operations hardening track without changing NS8 core math/spec behavior.

## Highlights

- Phase 1: live adapter and pinned identity replay hardening
  - live adapter resolution is registry-driven (explicit unknown-adapter rejection preserved)
  - `live-replay` / `live-verify` support `--require-pinned-model-identity` for `coding_agent`
  - fail-fast enforcement for missing pinned identity fields (`provider`, `model_tag`, `model_digest|model_version`, `generation_settings`)

- Phase 2: coding-agent diagnostics in report and triage
  - report JSON includes additive `coding_agent_drift` slices when coding-agent rows are present
  - triage exports include additive coding-agent regression fields (language mismatch and bin deltas)

- Phase 3: benchmark and gate profile hardening
  - `benchmark --suite coding_agent_drift` emits deterministic `gate_ready` summaries
  - `coding_agent_drift` gate profile now includes behavioral thresholds:
    - `max_language_mismatch_rate_delta`
    - `max_verbosity_bin_mean_delta`
    - `min_tests_presence_rate_delta`
    - `min_tool_call_rate_delta`
  - gate enforces these thresholds deterministically when profile fields are set

## Claim Boundaries

- This release strengthens deterministic behavioral consistency telemetry.
- It does not add code-correctness scoring.
- It does not add cognition or emotion inference claims.
- NS8 core mapping math and spec remain unchanged.

## Validation

- Targeted Phase 1/2/3 test sets: passed
- Full test suite:
  - `python -m pytest -q` -> `217 passed`

## Metadata Sync

- Package version set to `0.2.4` in `pyproject.toml`
- Observability API app version set to `0.2.4`
- README/docs command and profile guidance aligned to implemented `v0.2.4` behavior
