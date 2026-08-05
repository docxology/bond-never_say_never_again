"""Never Say Never Again — REMOUNT.

A BOND film package implementing the frozen ``bond_api.MissionProvider``
protocol for *REMOUNT*: a legacy mission replay/remount engine, op
diff/comparison, and legacy asset migration.

Pure domain modules (no ``bond_api`` / ``infrastructure`` imports):

* :mod:`~never_say_never_again.mission_replay` — deterministic scenario replay.
* :mod:`~never_say_never_again.op_diff` — original vs remount comparison.
* :mod:`~never_say_never_again.legacy_assets` — remastered intel migration.
* :mod:`~never_say_never_again.remount_risk` — escalation hazard, reliability
  blocks, and campaign expected value.
* :mod:`~never_say_never_again.asset_allocator` — marginal-gain (submodular
  greedy) allocation of remastered assets.
* :mod:`~never_say_never_again.learning_curve` — exponential replay-learning
  forecast of command-score improvement.

The protocol adapter (``mission.py``) and manuscript-variable hydration build
on these. See :mod:`~never_say_never_again.mission` for the provider.
"""

from __future__ import annotations

__version__ = "0.1.0"

from never_say_never_again.asset_allocator import (
    ALLOCATION_BUDGET,
    ALLOCATION_POOL,
    AllocatableObjective,
    AllocationPlan,
    allocate,
    canonical_allocation,
)
from never_say_never_again.learning_curve import (
    LearningReplayForecast,
    canonical_learning_forecast,
    exponential_learning,
    forecast_curve,
    forecast_replay,
    iterations_to_target,
)
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
from never_say_never_again.remount_risk import (
    RemountRiskReport,
    assess_campaign,
    canonical_risk_report,
    detection_probability,
    expected_operations_before_alert,
    parallel_reliability,
    series_reliability,
)

__all__ = [
    "ALLOCATION_BUDGET",
    "ALLOCATION_POOL",
    "LEGACY_SCENARIO",
    "REMOUNT_CONFIG",
    "AllocatableObjective",
    "AllocationPlan",
    "AssetCatalog",
    "LearningReplayForecast",
    "LegacyAsset",
    "MigratedAsset",
    "MigrationBatch",
    "ObjectiveDiff",
    "ObjectiveOutcome",
    "ObjectiveSpec",
    "OpDiff",
    "RemountConfig",
    "RemountRiskReport",
    "ReplayEngine",
    "ReplayResult",
    "Scenario",
    "allocate",
    "assess_campaign",
    "canonical_allocation",
    "canonical_learning_forecast",
    "canonical_risk_report",
    "detection_probability",
    "diff_outcomes",
    "expected_operations_before_alert",
    "exponential_learning",
    "forecast_curve",
    "forecast_replay",
    "iterations_to_target",
    "parallel_reliability",
    "remaster",
    "series_reliability",
    "verify",
]
