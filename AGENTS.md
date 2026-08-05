# never_say_never_again — AGENTS

A **PROJECT BOND** film package. Scope is EXACTLY this directory. Local-only
working tree — never push, there is no remote.

## Mission

Codename **REMOUNT**. Implement the frozen `bond_api.MissionProvider` protocol
over a pure, deterministic domain core that models **legacy mission replay,
op diff, and legacy asset migration** (a software remount of *Thunderball*).

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/never_say_never_again/mission_replay.py`, `op_diff.py`, `legacy_assets.py`, `remount_risk.py`, `asset_allocator.py`, `learning_curve.py` (mathematical core) | Pure deterministic logic — **no** `bond_api`, **no** `infrastructure` imports |
| `src/never_say_never_again/mission.py` | Thin `bond_api` adapter: implements frozen `MissionProvider`, registers gadgets |
| `src/never_say_never_again/manuscript_variables.py` | Hydrates `{{TOKEN}}`s from `manuscript/config.yaml` + domain surface |
| `src/never_say_never_again/figures.py` | Deterministic Matplotlib (Agg) to `output/figures/` |
| `scripts/` | Thin orchestrators; may import the package and `bond_api` |
| Live counts | `docs/_generated/COUNTS.md` — never hardcode test totals or coverage % |

## Protocol integration

- `pyproject.toml` declares a local path dependency on sibling `bond-api`
  (`[tool.uv.sources] bond-api = { path = ... }`).
- `src/never_say_never_again/mission.py` exposes `MissionProvider` at module
  top level (`film = "never_say_never_again"`) and registers
  `engine`/`legacy_scenario`/`remount_config` gadgets with a `GadgetRegistry`.
- The orchestrator discovers this film by slug via `bond_api.discovery`.

## Determinism

No random draws, no wall-clock in persisted artifacts. Replays, diffs, and
figures are byte-identical across runs. Seed 13 is provenance-only.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'
git status --short   # clean after commit
```

## Reference

The prose in `docs/` (`architecture.md`, `testing_philosophy.md`,
`agent_instructions.md`) carries the operational constraints for anyone
modifying this package. When a dependency (`bond-utilities`) is needed but not
yet bound, declare the integration point in `TODO.md` rather than stalling.
