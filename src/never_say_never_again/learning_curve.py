"""Replay learning curve — deterministic forecast of remount improvement.

A remount gets better with each rehearsal: the crew learns the scenario, the
remastered intel is refined, and the command score rises toward an asymptote
with diminishing returns. This module models that as a classic exponential
learning curve (Wright 1936 family):

* :func:`exponential_learning` — ``final - (final - initial) * exp(-rate * n)``.
* :func:`forecast_curve` — the score trajectory over ``n = 1..iterations``.
* :func:`iterations_to_target` — smallest ``n`` reaching a target score
  (``None`` when the asymptote cannot reach it).
* :func:`forecast_replay` — a curve over real :class:`~.mission_replay`
  command scores: the baseline replay (identity config) is the initial value
  and a fully-reinforced replay (capped config) is the asymptote.

The module is pure (stdlib only) and fully deterministic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    RemountConfig,
    ReplayEngine,
    Scenario,
)

__all__ = [
    "LEARNING_BONUS_CAP",
    "LEARNING_ITERATIONS",
    "LEARNING_RATE",
    "LEARNING_TARGET_SCORE",
    "LearningReplayForecast",
    "canonical_learning_forecast",
    "exponential_learning",
    "forecast_curve",
    "forecast_replay",
    "iterations_to_target",
]

#: Canonical learning rate (per-replay improvement factor).
LEARNING_RATE = 0.4

#: Canonical number of forecast iterations.
LEARNING_ITERATIONS = 8

#: Canonical intel-bonus cap for the fully-reinforced (asymptote) replay.
LEARNING_BONUS_CAP = 0.30

#: Canonical command-score target whose reach iteration is reported.
LEARNING_TARGET_SCORE = 0.55


def _require_non_negative(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0.0:
        raise ValueError(f"{label} must be a non-negative number")


def exponential_learning(
    initial: float, final: float, rate: float, iteration: int
) -> float:
    """Score at ``iteration`` under an exponential learning curve.

    ``final - (final - initial) * exp(-rate * iteration)``: monotonically
    approaches ``final`` with diminishing per-iteration gains.
    """
    _require_non_negative(rate, "rate")
    if isinstance(iteration, bool) or not isinstance(iteration, int) or iteration < 0:
        raise ValueError("iteration must be a non-negative integer")
    return final - (final - initial) * math.exp(-rate * iteration)


def forecast_curve(
    initial: float,
    final: float,
    rate: float,
    iterations: int,
) -> tuple[float, ...]:
    """Score trajectory for ``n = 1..iterations`` (deterministic)."""
    if (
        isinstance(iterations, bool)
        or not isinstance(iterations, int)
        or iterations < 1
    ):
        raise ValueError("iterations must be a positive integer")
    return tuple(
        exponential_learning(initial, final, rate, n) for n in range(1, iterations + 1)
    )


def iterations_to_target(
    initial: float,
    final: float,
    rate: float,
    target: float,
) -> int | None:
    """Smallest replay count reaching ``target``, or ``None`` if unreachable.

    Returns 1 when the initial score already meets the target; ``None`` when
    the asymptote (``final``) sits below the target or the rate is zero with an
    unmet target (no learning happens).
    """
    if initial >= target:
        return 1
    if final < target:
        return None
    if rate == 0.0:
        return None
    denominator = final - initial
    if denominator <= 0.0:
        return None
    ratio = (final - target) / denominator
    if ratio <= 0.0:
        return 1
    iterations = math.ceil(-math.log(ratio) / rate)
    return max(1, iterations)


@dataclass(frozen=True)
class LearningReplayForecast:
    """Deterministic learning-curve forecast over real replay command scores.

    Attributes:
        scores: Command score per forecast iteration (n = 1..iterations).
        iterations: Number of forecast iterations.
        initial_score: Baseline command score (zero reinforcement).
        final_score: Command score at the last forecast iteration.
        delta: ``final_score - initial_score``.
        target_iteration: First iteration meeting the target score, or None.
    """

    scores: tuple[float, ...]
    iterations: int
    initial_score: float
    final_score: float
    delta: float
    target_iteration: int | None

    def __post_init__(self) -> None:
        if (
            isinstance(self.iterations, bool)
            or not isinstance(self.iterations, int)
            or self.iterations < 1
        ):
            raise ValueError(
                "LearningReplayForecast.iterations must be a positive integer"
            )
        if not isinstance(self.scores, tuple) or len(self.scores) != self.iterations:
            raise ValueError("LearningReplayForecast.scores must match iterations")


def forecast_replay(
    engine: ReplayEngine,
    scenario: Scenario,
    *,
    base_config: RemountConfig,
    capped_config: RemountConfig,
    rate: float,
    iterations: int,
    target_score: float,
) -> LearningReplayForecast:
    """Forecast the replay learning curve over a real scenario.

    The baseline replay under ``base_config`` fixes the curve's initial value;
    the fully-reinforced replay under ``capped_config`` fixes its asymptote;
    the trajectory is the deterministic exponential curve between them.
    """
    initial_score = engine.replay(scenario, base_config).command_score
    asymptote = engine.replay(scenario, capped_config).command_score
    scores = forecast_curve(initial_score, asymptote, rate, iterations)
    return LearningReplayForecast(
        scores=scores,
        iterations=iterations,
        initial_score=initial_score,
        final_score=scores[-1],
        delta=scores[-1] - initial_score,
        target_iteration=iterations_to_target(
            initial_score, asymptote, rate, target_score
        ),
    )


def canonical_learning_forecast(
    engine: ReplayEngine | None = None,
) -> LearningReplayForecast:
    """The canonical deterministic learning forecast used across the package."""
    engine = engine if engine is not None else ReplayEngine()
    return forecast_replay(
        engine,
        LEGACY_SCENARIO,
        base_config=RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0),
        capped_config=RemountConfig(
            intel_bonus=LEARNING_BONUS_CAP, doctrine=1.0, realism_ceiling=1.0
        ),
        rate=LEARNING_RATE,
        iterations=LEARNING_ITERATIONS,
        target_score=LEARNING_TARGET_SCORE,
    )
