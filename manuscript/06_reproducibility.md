# Reproducibility

## Determinism by construction

REMOUNT commits to byte-level reproducibility. The domain core performs no
random draws and no wall-clock reads, so replaying `THUNDERBALL-65` twice
yields identical `ReplayResult` objects; rendering a figure twice yields
identical PNG bytes. The only non-deterministic token, `GENERATION_TIMESTAMP`,
is an audit stamp, not a computation input.

## Provenance

Every mission outcome carries a `Provenance` block with:

- `package_version` — {{PACKAGE_VERSION}}.
- `seed` — the deterministic seed (13).
- `input_hash` — a canonical SHA-256 fingerprint of the mission brief.
- `wall_time_s` — always `0.0` (the engine is stateless and instantaneous).

The migrated-asset catalog exposes `stable_integrity()`, a catalog-wide
fingerprint (`{{ASSET_FINGERPRINT}}`) so an artifact set can be audited without
re-running the suite.

## Verification commands

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'
```

This manuscript is produced on Python {{PYTHON_VERSION}}, generated
{{GENERATION_TIMESTAMP}}.
