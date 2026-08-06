"""Tests for the REMOUNT replay engine (mission_replay.py).

Real deterministic data only: the canonical THUNDERBALL scenario and hand-
constructed edge cases. No mocks, no RNG.
"""

from __future__ import annotations

import pytest

from never_say_never_again.mission_replay import (
    DEFAULT_SENSITIVITY,
    DEFAULT_SUCCESS_THRESHOLD,
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    ObjectiveSpec,
    RemountConfig,
    ReplayEngine,
    ReplayResult,
    Scenario,
)

#: A float tolerance generous enough for the fixed-point logistic arithmetic.
TOL = 1e-9


def test_canonical_scenario_and_remount_constants_are_valid():
    assert LEGACY_SCENARIO.name == "THUNDERBALL-65"
    assert len(LEGACY_SCENARIO.objectives) >= 4
    assert all(isinstance(o, ObjectiveSpec) for o in LEGACY_SCENARIO.objectives)
    assert REMOUNT_CONFIG.intel_bonus > 0.0
    assert 0.0 <= REMOUNT_CONFIG.realism_ceiling <= 1.0


def test_replay_is_deterministic():
    engine = ReplayEngine()
    first = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    second = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    assert first.command_score == second.command_score
    assert [o.score for o in first.outcomes] == [o.score for o in second.outcomes]
    assert isinstance(first, ReplayResult)


def test_remount_improves_command_score():
    engine = ReplayEngine()
    identity = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)
    original = engine.replay(LEGACY_SCENARIO, identity)
    remount = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    assert remount.command_score > original.command_score
    assert remount.objectives_fulfilled >= original.objectives_fulfilled


def test_identity_config_matches_zero_delta():
    engine = ReplayEngine()
    identity = RemountConfig(intel_bonus=0.0, doctrine=1.0)
    result = engine.replay(LEGACY_SCENARIO, identity)
    # With no deltas, the replay is deterministic and bounded; the aggregate
    # command score lies within [0, 1].
    assert 0.0 <= result.command_score <= 1.0
    assert (
        result.command_score == engine.replay(LEGACY_SCENARIO, identity).command_score
    )


def test_intel_capped_at_realism_ceiling():
    engine = ReplayEngine()
    config = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=0.5)
    result = engine.replay(LEGACY_SCENARIO, config)
    for outcome in result.outcomes:
        assert outcome.effective_intel <= 0.5 + TOL


def test_fully_optimistic_config_achieves_every_objective():
    engine = ReplayEngine()
    config = RemountConfig(intel_bonus=1.0, doctrine=10.0, realism_ceiling=1.0)
    result = engine.replay(LEGACY_SCENARIO, config)
    assert result.objectives_fulfilled == len(LEGACY_SCENARIO.objectives)


def test_outcome_for_returns_none_for_unknown_objective():
    engine = ReplayEngine()
    result = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    assert result.outcome_for("does-not-exist") is None
    assert result.outcome_for(LEGACY_SCENARIO.objectives[0].objective_id) is not None


def test_sigmoid_halfway_threshold_for_zero_input():
    engine = ReplayEngine(success_threshold=0.5)
    # Build a single objective where baseline == difficulty (score = 0.5).
    spec = ObjectiveSpec(
        objective_id="tie", weight=1.0, difficulty=0.5, baseline_intel=0.5
    )
    scenario = Scenario(name="tie-op", objectives=(spec,))
    result = engine.replay(scenario, RemountConfig(intel_bonus=0.0))
    outcome = result.outcomes[0]
    assert abs(outcome.score - 0.5) < 1e-3
    assert outcome.achieved is True  # score == threshold counts as achieved


def test_sigmoid_saturates_high_and_low():
    engine = ReplayEngine()
    high = Scenario(
        name="high",
        objectives=(
            ObjectiveSpec(
                objective_id="h", weight=1.0, difficulty=0.0, baseline_intel=1.0
            ),
        ),
    )
    low = Scenario(
        name="low",
        objectives=(
            ObjectiveSpec(
                objective_id="l", weight=1.0, difficulty=1.0, baseline_intel=0.0
            ),
        ),
    )
    assert engine.replay(high, RemountConfig()).outcomes[0].score > 0.99
    assert engine.replay(low, RemountConfig()).outcomes[0].score < 0.01


def test_sigmoid_is_symmetric_around_zero():
    # A difficulty delta of +d and -d around the same baseline yields scores
    # summing to ~1.0 (Logistic symmetry).
    engine = ReplayEngine()
    up = Scenario(
        name="up",
        objectives=(
            ObjectiveSpec(
                objective_id="u", weight=1.0, difficulty=0.5, baseline_intel=0.6
            ),
        ),
    )
    down = Scenario(
        name="down",
        objectives=(
            ObjectiveSpec(
                objective_id="d", weight=1.0, difficulty=0.6, baseline_intel=0.5
            ),
        ),
    )
    s_up = engine.replay(up, RemountConfig()).outcomes[0].score
    s_down = engine.replay(down, RemountConfig()).outcomes[0].score
    assert abs((s_up + s_down) - 1.0) < 1e-3


def test_validation_errors():
    with pytest.raises(ValueError):
        ObjectiveSpec(objective_id="", weight=1.0, difficulty=0.5, baseline_intel=0.5)
    with pytest.raises(ValueError):
        ObjectiveSpec(objective_id="x", weight=0.0, difficulty=0.5, baseline_intel=0.5)
    with pytest.raises(ValueError):
        ObjectiveSpec(objective_id="x", weight=1.0, difficulty=1.5, baseline_intel=0.5)
    with pytest.raises(ValueError):
        ObjectiveSpec(objective_id="x", weight=1.0, difficulty=0.5, baseline_intel=-0.1)
    with pytest.raises(ValueError):
        Scenario(name="", objectives=())
    with pytest.raises(ValueError):
        RemountConfig(intel_bonus=1.5)
    with pytest.raises(ValueError):
        RemountConfig(doctrine=-1.0)
    with pytest.raises(ValueError):
        ReplayEngine(sensitivity=0.0)
    with pytest.raises(ValueError):
        ReplayEngine(success_threshold=2.0)


def test_scenario_rejects_malformed_objective_collections():
    """Scenario validation error paths — each must fail, none may pass silently."""
    good = ObjectiveSpec(
        objective_id="ok", weight=1.0, difficulty=0.5, baseline_intel=0.5
    )
    # Not a tuple.
    with pytest.raises(ValueError, match="non-empty tuple"):
        Scenario(name="S", objectives=[good])  # type: ignore[arg-type]
    # Empty tuple.
    with pytest.raises(ValueError, match="non-empty tuple"):
        Scenario(name="S", objectives=())
    # Right container, wrong element type.
    with pytest.raises(ValueError, match="ObjectiveSpec instances"):
        Scenario(name="S", objectives=("not-a-spec",))  # type: ignore[arg-type]


def test_scenario_rejects_bad_timeline_days():
    good = ObjectiveSpec(
        objective_id="ok", weight=1.0, difficulty=0.5, baseline_intel=0.5
    )
    for bad in (0, -1, True, 2.5):
        with pytest.raises(ValueError, match="timeline_days"):
            Scenario(name="S", objectives=(good,), timeline_days=bad)  # type: ignore[arg-type]


def test_scenario_accepts_a_valid_timeline():
    """Positive control: the guard above rejects bad input without rejecting good."""
    good = ObjectiveSpec(
        objective_id="ok", weight=1.0, difficulty=0.5, baseline_intel=0.5
    )
    assert Scenario(name="S", objectives=(good,), timeline_days=1).timeline_days == 1


def test_mission_seed_is_a_shared_constant():
    """The seed is sourced from the pure core, not duplicated per module."""
    from never_say_never_again import mission_replay

    assert isinstance(mission_replay.MISSION_SEED, int)
    assert not isinstance(mission_replay.MISSION_SEED, bool)


def test_engine_defaults_come_from_the_module_constants():
    engine = ReplayEngine()
    tuned = ReplayEngine(
        sensitivity=DEFAULT_SENSITIVITY, success_threshold=DEFAULT_SUCCESS_THRESHOLD
    )
    result_a = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    result_b = tuned.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    assert result_a == result_b


def test_validation_rejects_non_finite_parameters():
    """NaN and infinity must be rejected, not propagate into the model.

    A regression against a real defect class: the positivity and non-negative
    guards compared ``value <= 0.0`` / ``value < 0.0``, which NaN (and signed
    infinity) fool — every NaN comparison is False, so a NaN weight, doctrine,
    or sensitivity sailed through validation and produced NaN scores, EV, and
    allocations. Every parameter check must now require a *finite* number.
    """
    non_finite = (float("nan"), float("inf"), float("-inf"))
    for bad in non_finite:
        with pytest.raises(ValueError, match="finite"):
            ObjectiveSpec(
                objective_id="x", weight=bad, difficulty=0.5, baseline_intel=0.5
            )
        with pytest.raises(ValueError, match="finite"):
            RemountConfig(intel_bonus=0.1, doctrine=bad)
        with pytest.raises(ValueError, match="finite"):
            ReplayEngine(sensitivity=bad)

    # The in-[0,1] guards already rejected NaN via the range comparison; keep
    # them pinned (a NaN baseline_intel / difficulty must also fail loudly).
    for bad in non_finite:
        with pytest.raises(ValueError, match=r"[0, 1]"):
            ObjectiveSpec(
                objective_id="x", weight=1.0, difficulty=bad, baseline_intel=0.5
            )
