# Gate Profiles

Gate profiles provide deterministic threshold sets for different operational contexts.

## Config File

Default path:

- `config/gate_profiles.json`

Current bundled profiles:

- `support_chat`
- `sales_chat`
- `strict_regression`

Each profile defines:

- `min_pass_rate_delta`
- `max_avg_l1_delta`
- `max_p95_l1_delta`

## CLI Usage

Use a profile:

```bash
python -m tonesight_ns8.cli gate \
  --run runs/new \
  --baseline runs/base \
  --profile support_chat
```

Use a custom profile file:

```bash
python -m tonesight_ns8.cli gate \
  --run runs/new \
  --baseline runs/base \
  --profile support_chat \
  --gate-profiles config/gate_profiles.json
```

Override profile thresholds explicitly:

```bash
python -m tonesight_ns8.cli gate \
  --run runs/new \
  --baseline runs/base \
  --profile strict_regression \
  --max-avg-l1-delta 0.15
```

Explicit CLI threshold flags always override profile values.

## Error Behavior

- Unknown profile names fail deterministically with an explicit error.
- Invalid profile config shape fails with a deterministic validation error.
