# src/ — REMOUNT domain core

The package source for `never_say_never_again` (codename REMOUNT). Layout:

| Module | Concept |
| --- | --- |
| `mission_replay.py` | Deterministic scenario replay (`ObjectiveSpec`, `Scenario`, `RemountConfig`, `ReplayEngine`, `ReplayResult`, `LEGACY_SCENARIO`, `REMOUNT_CONFIG`) |
| `op_diff.py` | Original vs remount comparison (`ObjectiveDiff`, `OpDiff`, `diff_outcomes`) |
| `legacy_assets.py` | Asset migration + integrity (`LegacyAsset`, `verify`, `remaster`, `AssetCatalog`, `MigrationBatch`) |
| `mission.py` | Thin `bond_api.MissionProvider` adapter + gadget registration |
| `manuscript_variables.py` | `{{TOKEN}}` hydration from `manuscript/config.yaml` + domain surface |
| `figures.py` | Deterministic Matplotlib figures (Agg) to `output/figures/` |
| `__init__.py` | Public API + `__version__ = "0.1.0"` |

The mathematical core (`mission_replay.py`, `op_diff.py`, `legacy_assets.py`)
is **pure and stdlib-only** — no `bond_api`, no `infrastructure`. `mission.py`
is the only module that imports `bond_api`. Keep it that way.
