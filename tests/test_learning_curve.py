"""Tests for the replay learning curve module (learning_curve.py).

Real deterministic math: exponential learning curve, iteration-to-target
solver, and the replay forecast over actual command scores. No mocks.
"""

from __future__ import annotations

import itertools
import math

import pytest

from never_say_never_again.learning_curve import (
    LEARNING_BONUS_CAP,
    LEARNING_ITERATIONS,
    LEARNING_RATE,
    LearningReplayForecast,
    canonical_learning_forecast,
    exponential_learning,
    forecast_curve,
    forecast_replay,
    iterations_to_target,
)
from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    RemountConfig,
    ReplayEngine,
)

TOL = 1e-9


def test_exponential_learning_basics():
    initial, final, rate = 0.4, 0.7, 0.5
    assert exponential_learning(initial, final, rate, 0) == pytest.approx(initial)
    assert exponential_learning(initial, final, rate, 1) == pytest.approx(
        final - (final - initial) * math.exp(-rate)
    )
    assert exponential_learning(initial, final, rate, 100) == pytest.approx(
        final, abs=1e-6
    )
    # Monotone from initial up to final.
    values = [exponential_learning(initial, final, rate, n) for n in range(10)]
    assert all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def test_exponential_learning_errors():
    with pytest.raises(ValueError):
        exponential_learning(0.4, 0.7, -0.1, 1)
    with pytest.raises(ValueError):
        exponential_learning(0.4, 0.7, 0.5, -1)


def test_forecast_curve():
    curve = forecast_curve(0.4, 0.7, 0.5, 8)
    assert isinstance(curve, tuple)
    assert len(curve) == 8
    assert all(a <= b for a, b in itertools.pairwise(curve))  # non-decreasing
    assert curve[-1] < 0.7  # below the asymptote at a finite horizon
    assert forecast_curve(0.4, 0.7, 0.5, 8) == forecast_curve(0.4, 0.7, 0.5, 8)
    with pytest.raises(ValueError):
        forecast_curve(0.4, 0.7, 0.5, 0)


def test_iterations_to_target_normal_case():
    # initial 0.4, final 0.7, rate 0.5, target 0.6.
    # n = ceil(-ln((0.7-0.6)/(0.7-0.4)) / 0.5) = ceil(2.197) = 3.
    assert iterations_to_target(0.4, 0.7, 0.5, 0.6) == 3


def test_iterations_to_target_edge_cases():
    # Already at/above target -> first replay counts.
    assert iterations_to_target(0.7, 0.7, 0.5, 0.6) == 1
    # Unreachable: asymptote below target.
    assert iterations_to_target(0.4, 0.6, 0.5, 0.9) is None
    # Zero rate with unmet target -> no learning -> unreachable.
    assert iterations_to_target(0.4, 0.7, 0.0, 0.6) is None
    # Negative rate -> the curve diverges from the target -> unreachable.
    assert iterations_to_target(0.4, 0.7, -0.5, 0.6) is None
    # Flat curve (final == initial) under target -> unreachable.
    assert iterations_to_target(0.4, 0.4, 0.5, 0.6) is None


def test_iterations_to_target_asymptote_equal_to_target_is_unreachable():
    """final == target is unreachable: the curve approaches but never attains.

    This pins a real fixed defect. The solver previously returned 1 here,
    claiming the target was met on the first replay. The positive control below
    shows that claim was false: the curve is strictly under the target at every
    finite iteration tested, including the one it used to return.
    """
    initial, final, rate = 0.4, 0.6, 0.5
    target = final

    assert iterations_to_target(initial, final, rate, target) is None

    # Positive control: had the answer been n, the score at n would meet the
    # target. It does not — over the whole operationally meaningful range,
    # including the n = 1 the buggy version used to return.
    for n in range(1, 21):
        assert exponential_learning(initial, final, rate, n) < target

    # Honest bound on the above. "Never attains" is a statement about the real
    # numbers. In float64 the residual (final - initial) * exp(-rate * n)
    # eventually falls below the ULP of `final` and the score rounds up to the
    # asymptote exactly. That happens far outside any useful replay count, and
    # it is a property of binary floating point, not of the model — so the
    # solver still correctly reports the target as unreachable.
    assert exponential_learning(initial, final, rate, 1000) == target


def test_iterations_to_target_answer_is_the_smallest_that_works():
    """The returned n reaches the target and n-1 does not — a tight bound."""
    initial, final, rate, target = 0.4, 0.7, 0.5, 0.6
    n = iterations_to_target(initial, final, rate, target)
    assert n is not None
    assert exponential_learning(initial, final, rate, n) >= target - TOL
    assert exponential_learning(initial, final, rate, n - 1) < target


def test_canonical_learning_forecast_values():
    forecast = canonical_learning_forecast()
    assert isinstance(forecast, LearningReplayForecast)
    assert forecast.iterations == LEARNING_ITERATIONS
    assert len(forecast.scores) == LEARNING_ITERATIONS
    assert forecast.initial_score == pytest.approx(0.3110890495940921, rel=1e-6)
    assert forecast.final_score > forecast.initial_score
    assert forecast.delta > 0.0
    assert forecast.target_iteration == 3

    # Scores rise toward the asymptote but stay strictly below it. The
    # asymptote is recomputed here from a *second real replay* under the capped
    # config — not read off the forecast — so this compares two independently
    # produced numbers. (The previous version of this assertion compared
    # `scores[-1]` to `final_score + 0.3`; since `final_score` IS `scores[-1]`,
    # it was `x < x + 0.3` and could not fail.)
    asymptote = (
        ReplayEngine()
        .replay(LEGACY_SCENARIO, RemountConfig(intel_bonus=LEARNING_BONUS_CAP))
        .command_score
    )
    assert forecast.scores[-1] < asymptote
    # ...and has closed most of the gap by the final iteration: the residual is
    # exp(-rate * iterations) of the initial gap, which pins the curve's shape.
    residual = (asymptote - forecast.initial_score) * math.exp(
        -LEARNING_RATE * LEARNING_ITERATIONS
    )
    assert asymptote - forecast.scores[-1] == pytest.approx(residual)


def test_canonical_learning_forecast_is_deterministic():
    assert canonical_learning_forecast() == canonical_learning_forecast()


def test_forecast_replay_with_custom_engine():
    engine = ReplayEngine()
    forecast = forecast_replay(
        engine,
        LEGACY_SCENARIO,
        base_config=RemountConfig(intel_bonus=0.0),
        capped_config=RemountConfig(intel_bonus=0.5),
        rate=0.5,
        iterations=5,
        target_score=0.6,
    )
    assert forecast.iterations == 5
    assert len(forecast.scores) == 5
    assert forecast.target_iteration is not None
    # A capped replay at +0.5 must exceed the base.
    assert forecast.final_score > forecast.initial_score
    assert all(s >= forecast.initial_score for s in forecast.scores)


def test_forecast_replay_monotone_scores():
    forecast = canonical_learning_forecast()
    assert all(
        forecast.scores[i] <= forecast.scores[i + 1]
        for i in range(len(forecast.scores) - 1)
    )


def test_learning_forecast_validation():
    with pytest.raises(ValueError):
        LearningReplayForecast(
            scores=(),
            iterations=0,
            initial_score=0.3,
            final_score=0.5,
            delta=0.2,
            target_iteration=None,
        )
    with pytest.raises(ValueError):
        LearningReplayForecast(
            scores=(0.4, 0.5),
            iterations=3,
            initial_score=0.3,
            final_score=0.5,
            delta=0.2,
            target_iteration=None,
        )
