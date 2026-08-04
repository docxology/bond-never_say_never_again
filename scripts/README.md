# scripts/ README — REMOUNT

Thin per-phase CLIs. All bootstrap `src/` themselves, so
`uv run python scripts/<name>.py` works from the package directory.

```bash
uv run python scripts/run_mission.py            # full five-stage mission
uv run python scripts/execute.py --out /tmp/o.json
uv run python scripts/z_generate_manuscript_variables.py
```

Run the suite with:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```
