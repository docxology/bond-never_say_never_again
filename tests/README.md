# tests/ README — REMOUNT

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

The suite uses only real data and computation — determinism replaces mocks. The
manuscript-variable test enforces that every `{{TOKEN}}` used in a numbered
prose section resolves through `generate_variables()`.
