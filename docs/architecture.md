# Architecture — REMOUNT

## Layering

```
scripts/            thin orchestrators (may import package + bond_api)
  | runs
src/never_say_never_again/
  mission.py        protocol adapter: implements bond_api.MissionProvider,
                    registers gadgets with a GadgetRegistry
  manuscript_variables.py   token hydration (config.yaml + domain surface)
  figures.py        deterministic matplotlib (Agg) rendering
  ----------------- pure domain core (stdlib only) -----------------
  mission_replay.py   Scenario / RemountConfig / ReplayEngine
  op_diff.py          diff_outcomes / OpDiff
  legacy_assets.py    LegacyAsset / AssetCatalog / migration
```

## Layer contract

The mathematical core (`mission_replay.py`, `op_diff.py`, `legacy_assets.py`)
must remain pure: no `bond_api`, no `infrastructure` imports. `mission.py` is
the thin adapter that knows the protocol. This keeps the analysis reusable if
either dependency is replaced.

## Data flow

1. `ReplayEngine.replay(scenario, config)` → `ReplayResult` (per-objective
   Logistic scores + weighted command score).
2. `diff_outcomes(original, remount)` → `OpDiff` (per-objective verdicts +
   weighted aggregate).
3. `AssetCatalog.migrate(new_contents)` → `MigrationBatch` (re-fingerprinted
   remastered intel).
4. `mission.execute` combines 1–3 into a `MissionOutcome` carrying
   `Provenance`.

## Determinism

Fixed seed, no random draws, no wall-clock in persisted artifacts. Replays,
diffs, and figures are byte-identical across runs.
