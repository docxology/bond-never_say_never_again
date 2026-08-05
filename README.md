# Never Say Never Again: REMOUNT

A **PROJECT BOND** film package implementing the frozen `bond_api`
`MissionProvider` protocol for mission codename **REMOUNT**.

*Never Say Never Again* (1983) is itself a **remount** of *Thunderball* (1965) —
a re-op of a completed operation, modernized and re-equipped. This package
turns that idea into deterministic special-agent software: it replays a legacy
mission as a remount, diffs the original vs remount outcomes, and migrates the
remastered intelligence assets.

## Concepts

| Module | Concept | What it does |
| --- | --- | --- |
| `src/never_say_never_again/mission_replay.py` | Legacy mission replay | Deterministically re-runs a scenario (Logistic success model over intel vs difficulty) under a remount config |
| `src/never_say_never_again/op_diff.py` | Op diff | Compares original vs remount scores per objective and in aggregate (weighted verdict) |
| `src/never_say_never_again/legacy_assets.py` | Legacy asset migration | Re-fingerprints (SHA-256) and migrates remastered intel; tamper detection and batch migration |
| `src/never_say_never_again/remount_risk.py` | Remount risk | Detection (exponential hazard), series/parallel reliability blocks, campaign expected value |
| `src/never_say_never_again/asset_allocator.py` | Asset allocation | Greedy marginal-gain (submodular) allocation of scarce remastered assets |
| `src/never_say_never_again/learning_curve.py` | Replay learning curve | Exponential forecast of command-score improvement over rehearsals |
| `src/never_say_never_again/mission.py` | Protocol adapter | Implements the frozen `bond_api.MissionProvider`; registers gadgets |
| `src/never_say_never_again/manuscript_variables.py` | Token hydration | Injects `{{TOKEN}}`s from `manuscript/config.yaml` + domain surface |
| `src/never_say_never_again/figures.py` | Rendering | Deterministic Matplotlib figures to `output/figures/` |

Mission codename **REMOUNT** (phase 4 codename **REPLAY**): the replay, diff,
and migration core is extended with escalation-risk, marginal-gain allocation,
and replay-learning models.

## Quick start

```bash
# From this package directory (deps include the sibling bond-api via path)
uv sync --extra dev

# Run the full five-stage mission
uv run python scripts/run_mission.py

# Per-phase CLIs
uv run python scripts/brief.py
uv run python scripts/recon.py
uv run python scripts/plan.py
uv run python scripts/execute.py
uv run python scripts/debrief.py

# Hydrate the manuscript + render figures
uv run python scripts/z_generate_manuscript_variables.py
```

## Deterministic result

Replaying the canonical `THUNDERBALL-65` scenario raises the weighted command
score from ~0.311 (original) to ~0.516 (remount), verdict **improved**, and
migrates 3 legacy intel dossiers with verified fingerprints. The deepened
models add the cost and trajectory of replay: campaign detection risk
~0.777 with reliability ~0.958, a marginal-gain allocation of 6 assets worth
~0.78 of the saturation ceiling, and a learning curve reaching its target at
iteration 3. Every number is a generated `{{TOKEN}}` in the manuscript — never
hand-authored in prose.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'
```

Live test count and coverage: `docs/_generated/COUNTS.md`.

## Local-only

This is a local-only PROJECT BOND working tree — there is no remote and nothing
is pushed. See `STANDALONE.md`.
