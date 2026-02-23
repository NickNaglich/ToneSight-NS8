# Security Policy

This document defines repository security controls for static analysis suppressions and CI gating.

## Scope

- Applies to Python source under `src/`.
- Governs `# nosec` suppression usage for Bandit findings.

## Bandit CI Gate

- CI must run:
  - `python -m bandit -r src`
- CI must fail on Bandit findings.

## `# nosec` Usage Policy

`# nosec` suppressions are allowed only when all of the following are true:

- the finding is reviewed and deemed acceptable for this repository context
- an inline rationale is provided
- a traceability reference is provided

Required inline format for new suppressions:

```python
# nosec BXXX - <brief rationale> [ref:#<issue_number>]
```

Example:

```python
subprocess.run(cmd, check=True)  # nosec B603 - input is constant and internal-only [ref:#42]
```

Notes:

- Existing historical suppressions are tracked in `tools/nosec_allowlist.json`.
- New suppressions that do not match the required format must fail CI.

## Enforcement

- Local/CI command:
  - `python tools/check_nosec_policy.py`
- The checker fails when it detects:
  - a new suppression not in allowlist and missing required rationale format
  - an allowlist entry that no longer exists (stale allowlist)
