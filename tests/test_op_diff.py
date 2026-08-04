"""Tests for the op diff module (op_diff.py).

Compares the canonical original vs remount replays, plus hand-built edge cases
for verdicts and unmatched objectives. Real computation, no mocks.
"""

from __future__ import annotations

import pytest

from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    ObjectiveSpec,
    RemountConfig,
    ReplayEngine,
    Scenario,
)
from never_say_never_again.op_diff import (
    OBJECTIVE_DIFF_ORDER,
    ObjectiveDiff,
    OpDiff,
    diff_outcomes,
)

TOL = 1e-9


@pytest.fixture(scope="module")
def canonical_diff() -> OpDiff:
    engine = ReplayEngine()
    identity = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)
    original = engine.replay(LEGACY_SCENARIO, identity)
    remount = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    return diff_outcomes(original, remount)


def test_canonical_overall_verdict(canonical_diff: OpDiff):
    assert canonical_diff.overall == "improved"
    assert canonical_diff.weighted_delta > 0.0


def test_canonical_per_objective_improvement(canonical_diff: OpDiff):
    assert len(canonical_diff.diffs) == len(LEGACY_SCENARIO.objectives)
    assert canonical_diff.improved == len(LEGACY_SCENARIO.objectives)
    assert canonical_diff.regressed == 0
    assert canonical_diff.unchanged == 0
    for diff in canonical_diff.diffs:
        assert isinstance(diff, ObjectiveDiff)
        assert diff.verdict == "improved"
        assert diff.remount_score > diff.original_score


def test_objective_diff_order_is_constant():
    assert OBJECTIVE_DIFF_ORDER == ("improved", "regressed", "unchanged")


def test_identical_replays_produce_no_change():
    engine = ReplayEngine()
    config = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)
    a = engine.replay(LEGACY_SCENARIO, config)
    b = engine.replay(LEGACY_SCENARIO, config)
    diff = diff_outcomes(a, b)
    assert diff.overall == "unchanged"
    assert diff.unchanged == len(LEGACY_SCENARIO.objectives)
    assert abs(diff.weighted_delta) < TOL


def test_regression_verdict_when_remount_hurts():
    engine = ReplayEngine()
    # A stunningly bad remount: everyone's intel drops to baseline 0.
    bad = Scenario(
        name="degraded",
        objectives=(
            ObjectiveSpec(
                objective_id="a", weight=1.0, difficulty=0.5, baseline_intel=0.9
            ),
            ObjectiveSpec(
                objective_id="b", weight=1.0, difficulty=0.5, baseline_intel=0.9
            ),
        ),
    )
    good_original = engine.replay(
        bad, RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)
    )
    # A regressive remount that somehow lowers effective intel below baseline.
    low_ceiling = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=0.1)
    worse_remount = engine.replay(bad, low_ceiling)
    diff = diff_outcomes(good_original, worse_remount)
    assert diff.overall == "regressed"
    assert diff.regressed >= 1


def test_unmatched_remount_objective_skipped():
    engine = ReplayEngine()
    original = Scenario(
        name="o",
        objectives=(
            ObjectiveSpec(
                objective_id="keep", weight=1.0, difficulty=0.5, baseline_intel=0.8
            ),
        ),
    )
    remount = Scenario(
        name="o",
        objectives=(
            ObjectiveSpec(
                objective_id="keep", weight=1.0, difficulty=0.5, baseline_intel=0.8
            ),
            ObjectiveSpec(
                objective_id="new-only", weight=1.0, difficulty=0.5, baseline_intel=0.8
            ),
        ),
    )
    diff = diff_outcomes(
        engine.replay(original, RemountConfig(intel_bonus=0.0)),
        engine.replay(remount, RemountConfig(intel_bonus=0.0)),
    )
    # Only the shared objective is diffed.
    assert [d.objective_id for d in diff.diffs] == ["keep"]
    assert diff.unchanged == 1


def test_diff_requires_replay_results():
    with pytest.raises(ValueError):
        diff_outcomes("not-a-result", "not-a-result")  # type: ignore[arg-type]


def test_mean_delta_matches_computation():
    engine = ReplayEngine()
    identity = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)
    original = engine.replay(LEGACY_SCENARIO, identity)
    remount = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    diff = diff_outcomes(original, remount)
    expected_mean = sum(d.delta for d in diff.diffs) / len(diff.diffs)
    assert abs(diff.mean_delta - expected_mean) < TOL
    # The weight-weighted delta differs from the unweighted mean because the
    # objectives are weighted unequally.
    assert abs(diff.weighted_delta - diff.mean_delta) > 1e-4


def test_custom_epsilon_reclassifies_tiny_deltas_as_unchanged():
    engine = ReplayEngine()
    scenario = Scenario(
        name="tiny",
        objectives=(
            ObjectiveSpec(
                objective_id="t", weight=1.0, difficulty=0.5, baseline_intel=0.51
            ),
            ObjectiveSpec(
                objective_id="u", weight=1.0, difficulty=0.5, baseline_intel=0.50
            ),
        ),
    )
    a = engine.replay(scenario, RemountConfig(intel_bonus=0.0))
    b = engine.replay(scenario, RemountConfig(intel_bonus=0.0))
    # A tiny epsilon keeps both unchanged; a huge epsilon also forces unchanged.
    strict = diff_outcomes(a, b, epsilon=1e-12)
    assert strict.unchanged == 2
    loose = diff_outcomes(a, b, epsilon=1.0)
    assert loose.overall == "unchanged"
    assert all(d.verdict == "unchanged" for d in loose.diffs)
