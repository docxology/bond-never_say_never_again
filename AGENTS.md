# never_say_never_again — AGENTS

A **PROJECT BOND** film package. Scope is EXACTLY this directory. Canonical
upstream: `docxology/bond-never_say_never_again` on GitHub (branch `main`) —
publish through the GitVault tool, never by an ad-hoc push.

## Mission

Codename **REMOUNT**. Implement the frozen `bond_api.MissionProvider` protocol
over a pure, deterministic domain core that models **legacy mission replay,
op diff, and legacy asset migration** (a software remount of *Thunderball*).

Codename **REMOUNT**. Seven pure domain modules model legacy mission replay, op
diff, asset migration, escalation risk, marginal-gain allocation, replay
learning, and one-at-a-time sensitivity; three adapter modules bind that core to
the protocol, the manuscript, and Matplotlib.

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/never_say_never_again/mission_replay.py`, `op_diff.py`, `legacy_assets.py`, `remount_risk.py`, `asset_allocator.py`, `learning_curve.py` (mathematical core) | Pure deterministic logic — **no** `bond_api`, **no** `infrastructure`; no third-party imports, only the stdlib and other modules of this same core (`asset_allocator.py` and `learning_curve.py` import `mission_replay.py` so their canonical inputs are derived from the scenario rather than re-declared). Enforced by `tests/test_mission_provider.py`, which reads the files. |
| `src/never_say_never_again/mission.py` | The only module importing `bond_api`. Thin adapter: implements the frozen `MissionProvider`, registers gadgets |
| `src/never_say_never_again/manuscript_variables.py` | Hydrates `{{TOKEN}}`s from `manuscript/config.yaml` + the live domain surface |
| `src/never_say_never_again/figures.py` | Deterministic Matplotlib (Agg) to `output/figures/` |
| `scripts/` | Thin orchestrators only — argv, one adapter call, printing, writes under `output/`. No domain object construction. |
| Live counts | `docs/_generated/COUNTS.md` — never hardcode test totals or coverage % in prose |

## Protocol integration

- `pyproject.toml` declares a local path dependency on sibling `bond-api`
  (`[tool.uv.sources] bond-api = { path = ... }`).
- `src/never_say_never_again/mission.py` exposes `MissionProvider` at module
  top level with `film = "never_say_never_again"`, satisfying the
  `@runtime_checkable` protocol structurally (no subclassing).
- Module-level `GADGET_REGISTRY` publishes six gadgets: `engine`,
  `legacy_scenario`, `remount_config`, `remount_risk_report`,
  `allocation_plan`, `learning_forecast`.
- The orchestrator discovers this film by slug via `bond_api.discovery`.
- **Frozen public shape**: `GADGET_REGISTRY`, the class name `MissionProvider`,
  the `film` attribute, and `brief`/`recon`/`plan`/`execute`/`debrief`. Adding
  a module-level name is safe; renaming or removing one breaks the fleet.

## Determinism

No random draws, no wall-clock reads in persisted artifacts, no network.
Replays, diffs, figures, `output/data/manuscript_variables.json`, and the
resolved manuscript tree are all byte-identical across runs — enforced by
`tests/test_regeneration_determinism.py`, which regenerates the whole artifact
set twice, more than a clock-second apart, into two clean roots and compares
SHA-256 per file. The manuscript's date is `paper.date` from
`manuscript/config.yaml` (token `{{MANUSCRIPT_DATE}}`), a committed value; a
generation timestamp read from the clock lived here until 2026-08-05 and made
the byte-identical claim false, so do not reintroduce one. `MISSION_SEED`
(defined in `mission_replay.py`, mirrored in `config.yaml`) is provenance-only:
nothing samples, so changing it cannot change a result. `wall_time_s` is fixed
at `0.0` deliberately — read it as "not recorded", not "instantaneous".

## Build

```bash
uv sync --extra dev                                 # bond-api via local path source
uv run python scripts/00_preflight.py               # protocol conformance
uv run python scripts/run_mission.py                # full five-stage flow
uv run python scripts/z_generate_manuscript_variables.py   # tokens + 4 figures
```

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'   # expect zero
git status --short   # clean after commit
```

Read the output of each; an exit code alone is not evidence. If `uv` reports
`Failed to initialize cache`, that is a sandbox restriction — rerun with the
sandbox disabled. If coverage dies with `no such table: meta` on its data file,
the working tree is on a filesystem its SQLite store rejects — rerun with
`COVERAGE_FILE` pointed at a local disk (`COVERAGE_FILE=/tmp/.coverage`).

## Reference

Operational detail lives in `docs/`: [`docs/AGENTS.md`](docs/AGENTS.md) is the
agent entry point, with [`docs/architecture.md`](docs/architecture.md),
[`docs/agent_instructions.md`](docs/agent_instructions.md) (including the traps
this package has already hit), [`docs/testing_philosophy.md`](docs/testing_philosophy.md),
and [`docs/style_guide.md`](docs/style_guide.md). Manuscript rules are in
[`manuscript/AGENTS.md`](manuscript/AGENTS.md). When a dependency
(`bond-utilities`) is needed but not yet bound, declare the integration point in
`TODO.md` rather than stalling.
