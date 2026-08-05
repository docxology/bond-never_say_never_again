# Agent instructions — REMOUNT

Operational constraints for anyone modifying this package.

1. **Scope**: work only inside this package directory. Never touch sibling BOND
   packages, bond root files, or the template repo. Never push — it is
   local-only and has no remote.
2. **Read first**: consult `docs/architecture.md` before altering `src/` or
   `scripts/` boundaries, and `docs/testing_philosophy.md` before writing or
   modifying any pytest file.
3. **Purity**: keep the mathematical core (`mission_replay.py`, `op_diff.py`,
   `legacy_assets.py`, `remount_risk.py`, `asset_allocator.py`,
   `learning_curve.py`) free of `bond_api` and `infrastructure` imports. Only
   `mission.py` imports `bond_api`.
4. **Protocol stability**: keep `mission.py`'s public shape stable —
   `GADGET_REGISTRY` (module-level), `film`, and the five protocol methods
   (`brief`/`recon`/`plan`/`execute`/`debrief`). Deepen inside the package;
   never break discovery.
5. **No mocks**: no `MagicMock` / `mocker.patch` / `unittest.mock`. Real data +
   computation only, deterministic.
6. **Determinism**: fixed seed, no untracked RNG, no wall-clock in persisted
   artifacts. Re-runs must be byte-identical.
7. **Metadata injection**: manuscript metrics are `{{TOKEN}}`s hydrated from
   `manuscript/config.yaml` + `src/.../manuscript_variables.py` — never
   hand-author metrics in prose.
8. **Thin scripts**: business logic lives in `src/`; `scripts/` only
   orchestrates and forwards argv.
9. **Gates before done**: `uv run pytest tests/ --cov=src --cov-fail-under=90`;
   `ruff check` + `ruff format`; `mypy src/ scripts/`;
   `rg -n "template[_]code_project" .` → zero; `git status` clean after commit.
