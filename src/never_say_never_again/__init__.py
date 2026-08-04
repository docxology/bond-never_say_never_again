"""Never Say Never Again — REMOUNT.

A BOND film package implementing the frozen ``bond_api.MissionProvider``
protocol for *REMOUNT*: a legacy mission replay/remount engine, op
diff/comparison, and legacy asset migration.

Pure domain modules (no ``bond_api`` / ``infrastructure`` imports):

* :mod:`~never_say_never_again.mission_replay` — deterministic scenario replay.
* :mod:`~never_say_never_again.op_diff` — original vs remount comparison.
* :mod:`~never_say_never_again.legacy_assets` — remastered intel migration.

The protocol adapter (``mission.py``) and manuscript-variable hydration build
on these. See :mod:`~never_say_never_again.mission` for the provider.
"""

from __future__ import annotations

__version__ = "0.1.0"

from never_say_never_again.legacy_assets import (
    AssetCatalog,
    LegacyAsset,
    MigratedAsset,
    MigrationBatch,
    remaster,
    verify,
)
from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    ObjectiveOutcome,
    ObjectiveSpec,
    RemountConfig,
    ReplayEngine,
    ReplayResult,
    Scenario,
)
from never_say_never_again.op_diff import ObjectiveDiff, OpDiff, diff_outcomes

__all__ = [
    "LEGACY_SCENARIO",
    "REMOUNT_CONFIG",
    "AssetCatalog",
    "LegacyAsset",
    "MigratedAsset",
    "MigrationBatch",
    "ObjectiveDiff",
    "ObjectiveOutcome",
    "ObjectiveSpec",
    "OpDiff",
    "RemountConfig",
    "ReplayEngine",
    "ReplayResult",
    "Scenario",
    "diff_outcomes",
    "remaster",
    "verify",
]
