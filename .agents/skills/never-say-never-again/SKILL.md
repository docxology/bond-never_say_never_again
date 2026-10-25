---
name: never-say-never-again
description: BOND film package (codename REMOUNT) — legacy mission replay, op diff, remastered-intel migration.
version: 1.0.0
author: docxology
license: MIT
tags: [bond, film, remount, mission-replay, op-diff, asset-migration]
---

# never-say-never-again (REMOUNT)

Project-scoped skill for the BOND film package checked out as this repository
(`docxology/bond-never_say_never_again`, branch `main`). Load this when working
inside the project.

## When to Use

- Working inside the `never_say_never_again` package — running the mission
  CLIs, editing `src/`, or regenerating manuscript variables / figures.
- Implementing or auditing the frozen `bond_api.MissionProvider` adapter
  (`src/never_say_never_again/mission.py`).
- Verifying the layer contract (pure domain core vs protocol adapter),
  no-mocks testing, and determinism.

## Quick Reference

```bash
# From the package directory
uv sync --extra dev
uv run python scripts/run_mission.py                  # full five-stage mission
uv run python scripts/z_generate_manuscript_variables.py   # tokens + figures
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
```

## Concepts

- `mission_replay.py` — `ReplayEngine` runs a `Scenario` (THUNDERBALL-65) under
  a `RemountConfig`; Logistic success model; weighted `command_score`.
- `op_diff.py` — `diff_outcomes` compares original vs remount (per-objective
  verdicts + weighted aggregate).
- `legacy_assets.py` — SHA-256 fingerprinting, tamper detection, `remaster`,
  `AssetCatalog` batch migration.
- `remount_risk.py` — exponential detection hazard, series/parallel
  reliability blocks, campaign expected value.
- `asset_allocator.py` — greedy marginal-gain (submodular) allocation of scarce
  assets.
- `learning_curve.py` — exponential replay-learning forecast + iteration-to-
  target solver.
- `mission.py` — the thin `bond_api.MissionProvider` adapter + gadgets
  (codename REMOUNT).

## Pitfalls

- **Keep the core pure.** `mission_replay.py`, `op_diff.py`,
  `legacy_assets.py` must import neither `bond_api` nor `infrastructure`.
- **No mocks.** Determinism replaces the mock framework; real data only.
- **Outputs are disposable.** `output/` is git-ignored; never hand-edit it.
- **Manuscript metrics are tokens.** Never hand-author a computed number in a
  prose section; inject it as `{{TOKEN}}`.
- **Lineage grep.** Use `rg "template[_]code_project"` (bracket-split) so a
  doc describing the verification cannot trip its own gate.
- **Publish through the GitVault tool.** The canonical remote is
  `docxology/bond-never_say_never_again`; never force-push.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
