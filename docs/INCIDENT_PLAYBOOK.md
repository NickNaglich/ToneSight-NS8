# Incident Playbook

This playbook defines deterministic incident automation for run-to-run regressions.

## Goal

Given a baseline run (`run_a`) and candidate run (`run_b`), produce a portable response package with stable artifact paths:

- compare summary/report
- triage export reference
- forensics bundle path
- markdown incident template

## CLI

```bash
python -m tonesight_ns8.cli incident --run-a runs/<baseline> --run-b runs/<candidate>
```

Optional controls:

```bash
python -m tonesight_ns8.cli incident \
  --run-a runs/<baseline> \
  --run-b runs/<candidate> \
  --top-n 50 \
  --triage-score delta_compliance_l1 \
  --triage-format jsonl
```

## Artifacts

Generated under candidate run:

- compare artifacts:
  - `runs/<runB>/comparisons/<runA>/compare_summary.json`
  - `runs/<runB>/comparisons/<runA>/compare_report.html`
- triage export:
  - `runs/<runB>/comparisons/<runA>/triage_<score>.<jsonl|csv>`
- bundle:
  - `runs/<runB>/bundles/forensics_bundle__vs__<runA>.zip`
- incident markdown:
  - `runs/<runB>/incidents/<runA>/incident_report.md`

## Determinism

- path conventions are fixed
- compare/triage ordering is stable
- bundle archive ordering and timestamps are fixed
- markdown template has static section ordering
