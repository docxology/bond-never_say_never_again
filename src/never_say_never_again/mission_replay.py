"""Legacy mission replay / remount engine — the core of REMOUNT.

REMOUNT's first concept is *legacy mission replay*: a prior operation (here
the 1965 THUNDERBALL op) is re-opened and re-run as a remount, with intel
reinforcements and doctrine adjustments folded in. The engine models each
objective deterministically — no randomness, no wall-clock — as a smooth
(Logistic) success curve over effective intel vs. difficulty.

* :class:`ObjectiveSpec` — a single objective: weight, difficulty, baseline
  intel readiness.
* :class:`Scenario` — an ordered set of objectives plus a mission timeline.
* :class:`RemountConfig` — the remount deltas: intel bonus, doctrine
  multiplier, realism ceiling.
* :class:`ReplayEngine` — replays a scenario under a config to a
  :class:`ReplayResult` (per-objective scores + a weighted command score).
* :class:`ReplayResult` — the deterministic outcome of one replay.

The module is pure (stdlib only). The exported ``LEGACY_SCENARIO`` and
``REMOUNT_CONFIG`` constants provide the canonical, deterministic Thunderball
dataset used by the mission provider and the figures.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "DEFAULT_SENSITIVITY",
    "DEFAULT_SUCCESS_THRESHOLD",
    "LEGACY_SCENARIO",
    "MISSION_SEED",
    "REMOUNT_CONFIG",
    "ObjectiveOutcome",
    "ObjectiveSpec",
    "RemountConfig",
    "ReplayEngine",
    "ReplayResult",
    "Scenario",
]

#: Package-wide deterministic seed. Recorded in every mission's ``Provenance``
#: and mirrored by ``manuscript/config.yaml``. It is *provenance-only*: no code
#: path in this package draws a random number, so changing it cannot change a
#: result. It lives in the pure core so the mission adapter, the manuscript
#: tokens, and the config cross-check test all read one value.
MISSION_SEED = 13

#: Default steepness of the Logistic success curve.
DEFAULT_SENSITIVITY = 6.0

#: Default score at or above which an objective counts as achieved.
DEFAULT_SUCCESS_THRESHOLD = 0.5


def _require_in_unit(value: float, label: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not (0.0 <= value <= 1.0)
    ):
        raise ValueError(f"{label} must be a number in [0, 1]")


def _sigmoid(z: float) -> float:
    """Numerically stable Logistic function."""
    if z >= 0.0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


@dataclass(frozen=True)
class ObjectiveSpec:
    """A single mission objective.

    Attributes:
        objective_id: Stable objective identifier.
        weight: Relative importance (> 0; weights need not sum to 1).
        difficulty: Base difficulty in [0, 1].
        baseline_intel: Baseline intel readiness in [0, 1].
    """

    objective_id: str
    weight: float
    difficulty: float
    baseline_intel: float

    def __post_init__(self) -> None:
        if not isinstance(self.objective_id, str) or not self.objective_id.strip():
            raise ValueError("ObjectiveSpec.objective_id must be a non-empty string")
        if (
            isinstance(self.weight, bool)
            or not isinstance(self.weight, (int, float))
            or self.weight <= 0.0
        ):
            raise ValueError("ObjectiveSpec.weight must be a positive number")
        _require_in_unit(self.difficulty, "ObjectiveSpec.difficulty")
        _require_in_unit(self.baseline_intel, "ObjectiveSpec.baseline_intel")


@dataclass(frozen=True)
class Scenario:
    """An ordered set of objectives and a mission timeline."""

    name: str
    objectives: tuple[ObjectiveSpec, ...]
    timeline_days: int = 30

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Scenario.name must be a non-empty string")
        if not isinstance(self.objectives, tuple) or not self.objectives:
            raise ValueError(
                "Scenario.objectives must be a non-empty tuple of ObjectiveSpec"
            )
        for objective in self.objectives:
            if not isinstance(objective, ObjectiveSpec):
                raise ValueError(
                    "Scenario.objectives entries must be ObjectiveSpec instances"
                )
        if (
            isinstance(self.timeline_days, bool)
            or not isinstance(self.timeline_days, int)
            or self.timeline_days < 1
        ):
            raise ValueError("Scenario.timeline_days must be a positive integer")


@dataclass(frozen=True)
class RemountConfig:
    """The remount deltas applied on top of a legacy scenario.

    Attributes:
        intel_bonus: Extra effective intel added to every objective in [0, 1].
        doctrine: Multiplier on effective intel (>= 0); 1.0 is neutral.
        realism_ceiling: Cap on effective intel in [0, 1].
    """

    intel_bonus: float = 0.0
    doctrine: float = 1.0
    realism_ceiling: float = 1.0

    def __post_init__(self) -> None:
        _require_in_unit(self.intel_bonus, "RemountConfig.intel_bonus")
        if (
            isinstance(self.doctrine, bool)
            or not isinstance(self.doctrine, (int, float))
            or self.doctrine < 0.0
        ):
            raise ValueError("RemountConfig.doctrine must be a non-negative number")
        _require_in_unit(self.realism_ceiling, "RemountConfig.realism_ceiling")


@dataclass(frozen=True)
class ObjectiveOutcome:
    """The deterministic outcome of one replayed objective."""

    objective_id: str
    effective_intel: float
    score: float
    achieved: bool


@dataclass(frozen=True)
class ReplayResult:
    """The deterministic outcome of a full scenario replay."""

    scenario: str
    config: RemountConfig
    outcomes: tuple[ObjectiveOutcome, ...]
    command_score: float
    objectives_fulfilled: int

    def outcome_for(self, objective_id: str) -> ObjectiveOutcome | None:
        """Return the outcome for ``objective_id``, or ``None`` if absent."""
        for outcome in self.outcomes:
            if outcome.objective_id == objective_id:
                return outcome
        return None


class ReplayEngine:
    """Deterministic scenario replayer for the REMOUNT engine."""

    def __init__(
        self,
        *,
        sensitivity: float = DEFAULT_SENSITIVITY,
        success_threshold: float = DEFAULT_SUCCESS_THRESHOLD,
    ) -> None:
        if (
            isinstance(sensitivity, bool)
            or not isinstance(sensitivity, (int, float))
            or sensitivity <= 0.0
        ):
            raise ValueError("sensitivity must be a positive number")
        _require_in_unit(success_threshold, "success_threshold")
        self._sensitivity = float(sensitivity)
        self._success_threshold = float(success_threshold)

    def effective_intel(self, spec: ObjectiveSpec, config: RemountConfig) -> float:
        """Compute the capped effective intel for an objective under a config."""
        blended = spec.baseline_intel + config.intel_bonus
        blended *= config.doctrine
        return max(0.0, min(config.realism_ceiling, blended))

    def replay(self, scenario: Scenario, config: RemountConfig) -> ReplayResult:
        """Replay ``scenario`` under ``config``, returning a deterministic result."""
        outcomes: list[ObjectiveOutcome] = []
        weighted_sum = 0.0
        weight_total = 0.0
        fulfilled = 0
        for spec in scenario.objectives:
            effective = self.effective_intel(spec, config)
            score = _sigmoid(self._sensitivity * (effective - spec.difficulty))
            achieved = score >= self._success_threshold
            outcomes.append(
                ObjectiveOutcome(
                    objective_id=spec.objective_id,
                    effective_intel=effective,
                    score=score,
                    achieved=achieved,
                )
            )
            weight_total += spec.weight
            weighted_sum += spec.weight * score
            if achieved:
                fulfilled += 1
        command_score = weighted_sum / weight_total if weight_total > 0.0 else 0.0
        return ReplayResult(
            scenario=scenario.name,
            config=config,
            outcomes=tuple(outcomes),
            command_score=command_score,
            objectives_fulfilled=fulfilled,
        )


#: Canonical deterministic dataset for the REMOUNT narrative: the 1965
#: THUNDERBALL operation re-opened as the 1983 remount.
LEGACY_SCENARIO = Scenario(
    name="THUNDERBALL-65",
    timeline_days=30,
    objectives=(
        ObjectiveSpec(
            objective_id="recover_weapons",
            weight=0.35,
            difficulty=0.70,
            baseline_intel=0.50,
        ),
        ObjectiveSpec(
            objective_id="neutralize_cell",
            weight=0.30,
            difficulty=0.60,
            baseline_intel=0.45,
        ),
        ObjectiveSpec(
            objective_id="extract_agent",
            weight=0.20,
            difficulty=0.50,
            baseline_intel=0.50,
        ),
        ObjectiveSpec(
            objective_id="deny_blackmail",
            weight=0.15,
            difficulty=0.55,
            baseline_intel=0.40,
        ),
    ),
)

#: Canonical remount config: reinforced intel + doctrine, realism-capped.
REMOUNT_CONFIG = RemountConfig(intel_bonus=0.15, doctrine=1.0, realism_ceiling=1.0)
