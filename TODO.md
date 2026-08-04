# never_say_never_again TODO

Forward-only backlog for the REMOUNT film package (codename REMOUNT).

## Built (phase 2)

- **Pure domain core** (`src/never_say_never_again/`), stdlib-only:
  - `mission_replay.py` — `ObjectiveSpec`, `Scenario`, `RemountConfig`,
    `ReplayEngine` (deterministic Logistic success model), `ReplayResult`,
    canonical `LEGACY_SCENARIO` (THUNDERBALL-65) + `REMOUNT_CONFIG`.
  - `op_diff.py` — `ObjectiveDiff`, `OpDiff`, `diff_outcomes` (per-objective
    verdicts + weighted aggregate verdict).
  - `legacy_assets.py` — `LegacyAsset`, `verify`, `remaster`, `AssetCatalog`,
    `MigrationBatch` (SHA-256 fingerprinting, tamper detection).
- **Protocol adapter** — `mission.py` implements the frozen `bond_api`
  `MissionProvider` (brief/recon/plan/execute/debrief) and registers gadgets
  with a `GadgetRegistry`.
- **Thin CLI scripts** — `brief.py`, `recon.py`, `plan.py`, `execute.py`,
  `debrief.py`, `run_mission.py`, `00_preflight.py`,
  `z_generate_manuscript_variables.py`.
- **Manuscript + rendering** — numbered prose sections with hydrated
  `{{TOKEN}}`s; deterministic figures (`op_diff_scores.png`,
  `asset_distribution.png`).

## Verification (measured)

- `uv run pytest tests/ --cov=src --cov-fail-under=90` — **60 passed**,
  **97.24 %** coverage on `src/` (floor 90 %).
- `ruff check` + `ruff format` clean on `src/ scripts/ tests/`.
- `mypy src/ scripts/` — clean (0 issues, 15 files).
- `rg template[_]code_project` — **zero** occurrences (built fresh; the only
  lineage reference is this bracket-split verification command).
- Because output/ is git-ignored, `execute.py` and the manuscript-variable
  smoke tests leave the tree clean.

## Declared integration points

- **Provenance persistence**: outcomes carry an in-package `Provenance` block
  computed directly. Acceptance: delegate outcome persistence to
  `bond_utilities.mission_io.record_provenance_outcome` once `bond-utilities`
  is reachable, keeping `Provenance.input_hash` semantics.
- **Signed asset chains**: `legacy_assets` is fingerprint-only. Acceptance:
  layer a signed-chain/integrity-registry helper (e.g. `bond_utilities`) over
  `AssetCatalog` without changing its pure core.

## Guardrails to preserve

1. Domain core stays `bond_api`- and `infrastructure`-free.
2. No mock framework — real data + computation only.
3. Manuscript metrics stay `{{TOKEN}}`-injected, never hand-authored.
4. Deterministic: fixed seed, no wall-clock in persisted artifacts.
