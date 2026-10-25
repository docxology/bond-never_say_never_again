# Working inside never_say_never_again (REMOUNT)

Entry point for any agent modifying this package. Read this page in full before
your first edit; it is short, and the four rules in "Before you touch anything"
are the ones that have actually caused problems here.

## Orientation

- **What this is**: one film package in PROJECT BOND. It implements the frozen
  `bond_api.MissionProvider` protocol over a pure, deterministic domain core
  modelling legacy mission *remount* — replay, diff, asset migration, risk,
  allocation, and learning.
- **Your scope**: this directory and nothing else. No sibling BOND package, no
  bond root file, no template repo.
- **Upstream is GitHub.** The canonical remote is
  `docxology/bond-never_say_never_again` (branch `main`). Commit here; publish
  only through the GitVault tool, never by an ad-hoc push.

## Before you touch anything

1. **Do not change the public shape of `mission.py`.** `GADGET_REGISTRY`
   (module level), the class name `MissionProvider`, the class attribute
   `film`, and the five methods `brief`/`recon`/`plan`/`execute`/`debrief` are
   consumed across packages by `bond-cli`, the coordinator's reconcile, and the
   orchestrator. Deepen *inside* — add modules, enrich results dicts, register
   more gadgets — but never rename or remove those. Adding a new module-level
   name is safe; removing or renaming one is not.
2. **Keep the domain core pure.** The seven modules `mission_replay.py`,
   `op_diff.py`, `legacy_assets.py`, `remount_risk.py`, `asset_allocator.py`,
   `learning_curve.py`, and `sensitivity.py` import stdlib only — no `bond_api`, no
   `infrastructure`. `tests/test_mission_provider.py` enforces this by reading
   the files, so a stray import fails the suite rather than degrading quietly.
3. **Never hand-author a metric.** Every number in `manuscript/` arrives as a
   `{{TOKEN}}` from `manuscript_variables.py`. A test scans the results section
   for bare decimals and fails on any it finds.
4. **No mock framework.** No `MagicMock`, no `mocker.patch`, no
   `unittest.mock`. See `testing_philosophy.md` for what to do instead.

## Routing

| You want to… | Read |
| --- | --- |
| Understand the modules and how they compose | [`architecture.md`](architecture.md) |
| Know the exact operational rules and gate commands | [`agent_instructions.md`](agent_instructions.md) |
| Write or change a test | [`testing_philosophy.md`](testing_philosophy.md) |
| Match the code style | [`style_guide.md`](style_guide.md) |
| Quote a coverage number or test count | [`_generated/COUNTS.md`](_generated/COUNTS.md) — or better, re-measure |
| See what is actually left to do | [`../TODO.md`](../TODO.md) |

## Build and verify

```bash
# From this package directory. bond-api resolves via a local path source.
uv sync --extra dev

# The five gates. All five must pass before you claim done.
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
git status --short          # clean after your commit
```

Run the mission and regenerate artifacts:

```bash
uv run python scripts/00_preflight.py               # protocol conformance check
uv run python scripts/run_mission.py                # full five-stage flow
uv run python scripts/z_generate_manuscript_variables.py   # tokens + figures
```

`uv` cannot write its cache under a restrictive sandbox. A
`Failed to initialize cache` error is an environment restriction, not a package
failure — rerun with the sandbox disabled.

## Adding a domain module

1. Write it in `src/never_say_never_again/`, stdlib-only, fully typed, with
   module and function docstrings. Validate inputs in `__post_init__` or at the
   top of the function and raise `ValueError` with an actionable message.
2. Export its public names from `__init__.py` and list them in the module's
   own `__all__`.
3. Test it in `tests/test_<module>.py`, covering the happy path, the boundary
   cases, *and* the error paths — plus a positive control proving each guard
   rejects bad input without rejecting good input.
4. If it produces a number the manuscript should state, add the token in
   `manuscript_variables.py`, reference `{{TOKEN}}` in the prose, and mirror any
   new constant into `manuscript/config.yaml` (the mirror is gate-checked).
5. Update `architecture.md`, the module table in `../README.md`, and `../TODO.md`.
