# AGENT_RULES - ToneSight NS8 Deterministic Library

You are implementing this repository in VS Code. Follow these rules strictly.

## 0) Prime Directive

Ship a deterministic, domain-agnostic NS8 library that:
- maps discrete Valence-Arousal-Dominance (VAD) signals through NS8 symmetry math
- enforces strict input validation
- is pinned by normative test vectors
- remains reproducible and audit-friendly

No cloud dependencies. No external API keys. No hidden stochastic behavior in core math.

## 1) Scope (v1)

### Must implement
A) NS8 core correctness
1. Maintain a reference implementation with deterministic behavior.
2. Keep canonical-seed routing and derived-family transforms explicit.
3. Enforce strict domain validation (`InvalidInput` on invalid family/r/c/k/N).

B) Taxonomy mapping
4. Keep a versioned, human-authored tone taxonomy file.
5. Validate taxonomy schema and V/A/D domain constraints.

C) Verification
6. Keep vector-based tests as normative behavior checks.
7. Keep invariant tests for symmetry identities and family equivalences.
8. Test suite must pass under `pytest -q`; environment-specific warnings should be triaged, not ignored.
   - New unexpected warnings should fail CI once CI is enabled.
   - Known warnings must be documented or filtered explicitly.

D) Packaging and interface (library-first)
9. Implement/maintain Python package layout and small public API surface.
10. Provide deterministic JSON-serializable receipts for wrapper APIs.
   - Receipts must conform to `docs/RECEIPT_SCHEMA.md`.
   - Receipt field names and types are contract-stable once released.
11. Keep CLI minimal and deterministic (if implemented in this phase).
   - CLI must remain a thin wrapper over library functions.
   - No business logic duplication in CLI layer.

### Optional (only if explicitly requested)
- Docker services, monitoring stacks, and GPU telemetry.
- External generation harnesses.

## 2) Non-negotiables

### Determinism
- Same input -> same output, always.
- No random branching in NS8 core.
- No silent fallback behavior.

### Strict validation
- `family in {TLF, TRF, BLF, BRF, TRB, TLB, BLB, BRB}`
- `r,c,k in {1..8}`
- Invalid input must raise explicit exceptions.
- Do not silently wrap external invalid inputs.

### NS8 correctness and scope
- NS8 is a deterministic encoding/mapping layer, not an emotion model.
- Do not claim NS8 improves detection accuracy.
- Derived families must be transform-only routes to canonical seeds.
- Avoid duplicate arithmetic implementations across derived families.
- Default family selection policy (if used by higher-level helpers) must be deterministic and documented.

### Spec authority
- `SPEC_NS8.md` is authoritative for formulas and behavior.
- Any behavior change to formulas/transforms/strictness requires:
  - `spec_version` bump
  - vector updates
  - test updates
  - docs updates

### Formula mismatch safety gate
- If external guidance conflicts with `SPEC_NS8.md`, do not change behavior silently.
- Document mismatch, then update spec+vectors+tests atomically only after explicit decision.

## 3) Test Vector and Taxonomy Policies

### Test vectors (normative)
- `ns8_test_vectors.json` defines expected behavior for conformance.
- Implementations must pass vector suite.
- Invalid vectors with `expected_error` must assert strict exceptions.
- Do not update expected values only to make failing tests pass.
- Vector edits should be append-preferred; corrective edits are allowed only for approved spec changes or verified vector defects.
- Vector regeneration via `tools/regen_vectors.py` is restricted.
- Agents must NOT regenerate vectors unless:
  - `SPEC_NS8.md` version is incremented, and
  - the change is documented in `.agent/LOGS/CHANGE_LOG.md`, and
  - the update is explicitly authorized in the active phase plan.

### Taxonomy (authoritative for labels)
- `tone_taxonomy.v1.json` is source of truth for label -> VAD mapping.
- Labels must be stable lowercase snake_case.
- Core taxonomy mappings are human-authored and deterministic.
- Do not generate/infer new core labels at runtime.

## 4) Engineering rules

- Python 3.11+
- Type hints for public functions
- `pytest` for tests
- Keep dependencies minimal
- Keep modules small and readable
- Prefer pure functions in NS8 core logic
- Avoid introducing app/framework complexity unless requested

## 5) Documentation rules

Documentation must be:
- technical and precise
- neutral and professional
- reproducible and audit-friendly

Avoid:
- marketing/hype language
- speculative claims
- domain-specific deployment assumptions

Terminology consistency:
- Always use: `Valence-Arousal-Dominance (VAD)`, `canonical seed`, `derived family`, `deterministic`, `strict validation`, `test vectors`.

Versioning note:
- Public API behavior is backward-stable within a minor version once packaging/semver is established.

## 6) Deliverables checklist (current project goal)

- [x] `SPEC_NS8.md` kept authoritative and versioned
- [x] reference NS8 implementation maintained (`ns8_ref.py` now; package module next)
- [x] normative vectors maintained (`ns8_test_vectors.json`)
- [x] vector tests passing (`test_ns8_vectors.py`)
- [x] taxonomy file maintained (`tone_taxonomy.v1.json`)
- [x] taxonomy tests passing (`test_tone_taxonomy.py`)
- [x] public API docs maintained (`API_REFERENCE.md`)
- [x] phased workflow maintained (`.agent/TO-DO/PHASED_WORKFLOW.md`)

Phase-gated (enable only when eval layer is in active scope):
- [x] default config artifact added (`config/defaults.json` or equivalent)
- [x] goldset seed file added (`data/goldset.jsonl`)

## 7) Non-goals (v1)

- Do not claim psychological emotion accuracy.
- Do not implement emotion recognition in core.
- Do not add cloud dependencies.
- Do not add heavy ML training/inference stacks by default.
- Do not add high-cardinality observability requirements unless scope changes.

## 8) Agent activity logging (required)

- After every meaningful project change, append a log entry to `.agent/LOGS/CHANGE_LOG.md`.
- Logging must be append-only; do not rewrite or delete prior entries.
- Each entry should include:
  - UTC timestamp
  - changed files
  - short summary of what changed
  - reason for the change
  - validation status (for example: tests run, lint, docs-only, or not run)
- If no files were changed, do not create a no-op entry.
