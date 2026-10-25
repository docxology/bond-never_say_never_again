# Agent instructions — Never Say Never Again (REMOUNT)

Concrete operational rules for modifying this package. `AGENTS.md` is the
orientation; this is the checklist.

## 1. Scope and safety

- Work only inside this package directory. Never edit a sibling BOND package,
  a bond root file, or the template repository.
- The canonical upstream is **`docxology/bond-never_say_never_again`** (private,
  branch `main`). Commit here; publish only through the GitVault tool
  (`./_tools/vault --wait with-repo docxology/bond-never_say_never_again -- git push origin main`),
  never by an ad-hoc push. Commit with path-scoped adds inside this repo only.
- `output/` is git-ignored and fully regenerable. Never hand-edit anything
  under it, and never edit a generated artifact to make a gate pass.

## 2. Read before editing

| Before you change… | Read |
| --- | --- |
| any `src/` or `scripts/` boundary | [`architecture.md`](architecture.md) |
| any file under `tests/` | [`testing_philosophy.md`](testing_philosophy.md) |
| formatting, typing, or docstrings | [`style_guide.md`](style_guide.md) |

## 3. The invariants

1. **Domain purity.** `mission_replay.py`, `op_diff.py`, `legacy_assets.py`,
   `remount_risk.py`, `asset_allocator.py`, `learning_curve.py`, and
   `sensitivity.py` import stdlib only — no `bond_api`, no `infrastructure`, no third-party runtime
   dependency. Only `mission.py` imports `bond_api`; only `figures.py` imports
   Matplotlib; only `manuscript_variables.py` imports `yaml`.
2. **Protocol stability.** `mission.py` must keep exposing, unchanged:
   module-level `GADGET_REGISTRY`; a top-level class named `MissionProvider`;
   its `film = "never_say_never_again"` attribute; and the five methods
   `brief`/`recon`/`plan`/`execute`/`debrief`. `bond-cli`, the coordinator
   reconcile, and the orchestrator consume these across packages. Adding a
   module-level name is safe. Renaming or removing one breaks discovery for the
   whole fleet.
3. **No mocks.** No `MagicMock`, no `mocker.patch`, no `unittest.mock`, no stub
   objects standing in for collaborators. Real data and real computation.
4. **Determinism.** No RNG, no wall-clock reads in persisted artifacts, no
   network. Re-runs must be byte-identical, and
   `tests/test_regeneration_determinism.py` proves it by regenerating twice
   across a clock-second boundary. Dates in the manuscript come from
   `paper.date` in `manuscript/config.yaml`, never from `datetime.now()`.
   `MISSION_SEED` is provenance-only — nothing samples, so changing it cannot
   change a result.
5. **No hand-authored metrics.** Every number in `manuscript/` is a `{{TOKEN}}`
   hydrated from `manuscript_variables.py`. A test scans the results section for
   bare decimals and fails on any it finds.
6. **Thin scripts.** `scripts/` may parse argv, call one adapter, print, and
   write under `output/`. Business logic belongs in `src/`. If a script starts
   constructing domain objects, move that construction into `src/` and expose a
   factory — this has already happened once, with the asset catalog the figure
   script used to build inline.
7. **Single source per constant.** A canonical value lives in exactly one
   domain module. Do not redeclare it in a script, a test, or the config; read
   it. `manuscript/config.yaml` mirrors these values for humans and the mirror
   is gate-checked against the code.

## 4. Traps this package has already hit

Each of these was a real defect. They are listed so they are not reintroduced.

- **Two derivations of one quantity.** The manuscript's migrated-asset count
  was computed from the scenario's *objective* count while the mission migrated
  a different list. Anything the manuscript states about the mission must be
  read from the same object the mission uses.
- **Optimizing a different function than you report.** The allocator selected
  greedily on unweighted marginal gain while reporting a weight-weighted score,
  so it lost to a uniform baseline while claiming a `(1 − 1/e)` guarantee. If
  you change a scoring function, check what the selection rule maximizes.
- **A boundary that returns a plausible wrong answer.** `iterations_to_target`
  returned 1 when the asymptote equalled the target — the one case where no
  finite iteration reaches it. Boundary equality deserves its own test.
- **Unreachable guards.** A `denominator <= 0` check sat below guards that made
  it impossible. Dead defensive code reads as safety while testing nothing.
- **A test that encodes the bug.** The asymptote case above was asserted as
  correct behaviour in the suite. A green test is not evidence the behaviour is
  right.
- **A citation to something that does not exist.** The scope section referenced
  a "reference film `sable`" that is not in the 33-package roster. Verify a
  cross-reference before writing it.

## 5. Adding a domain module

1. Create `src/never_say_never_again/<name>.py`: stdlib-only, module docstring
   explaining the *concept* and its link to the film, full type hints,
   `__all__`, and validation raising `ValueError` with actionable messages.
2. Export public names from `__init__.py` (keep `__all__` sorted).
3. Add `tests/test_<name>.py`: happy path, boundaries, every error path, and a
   positive control for each guard.
4. If it yields a number the manuscript should state, add the token in
   `manuscript_variables.py`, reference `{{TOKEN}}` in prose, and mirror any new
   constant into `manuscript/config.yaml`.
5. If it yields a figure, add a renderer to `figures.py` taking an explicit
   output path and returning it.
6. Update [`architecture.md`](architecture.md), the module table in
   `../README.md`, and `../TODO.md`.

## 6. Before you claim done

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py   # tokens still resolve
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'   # expect zero
git status --short                                         # clean after commit
```

Read the output of each. An exit code alone is not evidence — a suite that
collects zero tests also exits 0. If you regenerate
`_generated/COUNTS.md`, take the numbers from the run you just watched, never
from an earlier report.

If a gate fails with `Failed to initialize cache` from `uv`, that is a sandbox
restriction, not a package failure. Rerun it with the sandbox disabled.
