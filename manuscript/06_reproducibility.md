# Reproducibility

## Determinism by construction

REMOUNT commits to byte-level reproducibility. The domain core performs no
random draws and no wall-clock reads, so replaying `{{SCENARIO_NAME}}` twice
yields identical `ReplayResult` objects; rendering a figure twice yields
identical PNG bytes.

The claim covers the whole persisted artifact set — every file under
`output/`: `data/manuscript_variables.json`, the resolved manuscript tree under
`manuscript/`, and the four PNGs under `figures/`. No token reads the clock.
The date on this document, `MANUSCRIPT_DATE`, is `paper.date` from the
committed `manuscript/config.yaml`, so it changes only when a human changes it
in version control — never merely because the generator ran again. That is
enforced, not asserted: `tests/test_regeneration_determinism.py` runs the
generator twice, more than a clock-second apart, into two separate output
roots and compares the SHA-256 of every file.

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

This manuscript is produced on Python {{PYTHON_VERSION}}; its document date is
{{MANUSCRIPT_DATE}}.
