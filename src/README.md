# src/ README — REMOUNT

This package builds a deterministic **legacy mission remount**: replay a prior
operation, diff original vs remount outcomes, migrate the intelligence.

## Canvas

```python
from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    ReplayEngine,
    RemountConfig,
)
from never_say_never_again.op_diff import diff_outcomes

engine = ReplayEngine()
original = engine.replay(LEGACY_SCENARIO, RemountConfig(intel_bonus=0.0))
remount = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
print(remount.command_score)
print(diff_outcomes(original, remount).overall)  # 'improved'
```

## Mission provider

`mission.py` implements the frozen `bond_api.MissionProvider` protocol
(`brief`, `recon`, `plan`, `execute`, `debrief`) and registers gadgets
(`engine`, `legacy_scenario`, `remount_config`) with a `GadgetRegistry`.

## Determinism

Everything is deterministic: fixed seed, no random draws, no wall-clock in
artifacts. `figures.py` renders byte-identical PNGs on re-run.
