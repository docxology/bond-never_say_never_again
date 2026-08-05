# Reproducibility

## Determinism by construction

REMOUNT commits to byte-level reproducibility. The domain core performs no
random draws and no wall-clock reads, so replaying `{{SCENARIO_NAME}}` twice
yields identical `ReplayResult` objects; rendering a figure twice yields
identical PNG bytes. The only non-deterministic token, `GENERATION_TIMESTAMP`,
is an audit stamp, not a computation input.

## Provenance

Every mission outcome carries a `Provenance` block with:

- `package_version` — {{PACKAGE_VERSION}}.
- `seed` — the deterministic seed ({{MISSION_SEED}}).
- `input_hash` — a canonical SHA-256 fingerprint of the mission brief.
- `wall_time_s` — reported as `0.0`. This is a deliberate choice, not a
  measurement: the provider does not read the clock, because a real elapsed
  time would make otherwise-identical outcomes differ byte-for-byte between
  runs. Read it as "wall time not recorded", never as "the mission took no
  time".

The migrated-asset catalog exposes `stable_integrity()`, a catalog-wide
fingerprint over its sorted `(id, kind, content-digest)` rows. The manuscript
token `{{ASSET_FINGERPRINT}}` is that digest truncated for display, so an
artifact set can be audited without re-running the suite. The same catalog
factory (`canonical_catalog()`) feeds the mission provider, the manuscript
tokens, and the asset-distribution figure — there is no second derivation that
could disagree about what was migrated.

## Verification commands

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'
```

This manuscript is produced on Python {{PYTHON_VERSION}}, generated
{{GENERATION_TIMESTAMP}}.
