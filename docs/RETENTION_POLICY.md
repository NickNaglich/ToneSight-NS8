# Retention Policy (Deterministic Purge)

ToneSight provides deterministic local retention cleanup through the `purge` CLI command.

Command:

```bash
python -m tonesight_ns8.cli purge --out-root runs --older-than-days 30
```

Defaults:
- dry-run mode (`--apply` not provided)
- capture directories are skipped unless `--include-captures`
- run directories containing `bundles/` are skipped unless `--include-bundles`

Apply deletion:

```bash
python -m tonesight_ns8.cli purge --out-root runs --older-than-days 30 --apply
```

Explicitly include bundle/capture targets:

```bash
python -m tonesight_ns8.cli purge --out-root runs --older-than-days 30 --apply --include-bundles --include-captures
```

Safety guarantees:
- deterministic candidate discovery and evaluation ordering
- dry-run by default
- canonical bundle artifacts are preserved unless explicitly included

Output contract:
- `evaluated`: path-level actions (`keep`, `skip`, `delete`) with reasons
- `would_delete_count`: number of delete candidates in dry-run/apply mode
- `deleted_count`: number of paths actually removed (apply mode)

Coding-agent telemetry note:
- retain deterministic derived artifacts (`out.jsonl`, summaries, receipts, benchmark evidence) as primary records
- treat raw capture text as higher-sensitivity data; prefer shorter retention windows and explicit purge cadence

## UI Retention Boundary (v0.2.5)

UI should default to retained derived artifacts:
- `runs/index.json`
- receipt/summary/report/compare/gate artifacts

UI should not depend on raw retention artifacts:
- capture payloads under `runs/captures/**`
- quarantine/raw event logs

Operational implication:
- UI remains stable when raw capture retention windows are shorter than derived artifact retention windows.
- UI may show restricted raw artifact classes as disabled labels with safety text, but does not link them by default.
