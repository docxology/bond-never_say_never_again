# src/ — REMOUNT domain core

The package source for `never_say_never_again` (codename REMOUNT / REPLAY).
Layout:

| Module | Concept |
| --- | --- |
| `mission_replay.py` | Deterministic scenario replay (`ObjectiveSpec`, `Scenario`, `RemountConfig`, `ReplayEngine`, `ReplayResult`, `LEGACY_SCENARIO`, `REMOUNT_CONFIG`) |
| `op_diff.py` | Original vs remount comparison (`ObjectiveDiff`, `OpDiff`, `diff_outcomes`) |
| `legacy_assets.py` | Asset migration + integrity (`LegacyAsset`, `verify`, `remaster`, `AssetCatalog`, `MigrationBatch`) |
| `remount_risk.py` | Detection hazard, reliability blocks, campaign EV (`RemountRiskReport`, `assess_campaign`) |
| `asset_allocator.py` | Marginal-gain allocation (`AllocatableObjective`, `allocate`, `AllocationPlan`) |
| `learning_curve.py` | Exponential replay-learning forecast (`forecast_replay`, `LearningReplayForecast`) |
| `sensitivity.py` | One-at-a-time sensitivity analysis (`robust_range`, `sensitivity_summary`) |
| `mission.py` | Thin `bond_api.MissionProvider` adapter + gadget registration |
| `manuscript_variables.py` | `{{TOKEN}}` hydration from `manuscript/config.yaml` + domain surface |
| `figures.py` | Deterministic Matplotlib figures (Agg) to `output/figures/` |
| `__init__.py` | Public API + `__version__ = "0.1.0"` |

The mathematical core (all six `*_replay/op_diff/legacy_assets/remount_risk/
asset_allocator/learning_curve` modules) is **pure and stdlib-only** — no
`bond_api`, no `infrastructure`. `mission.py` is the only module that imports
`bond_api`. Keep it that way.
