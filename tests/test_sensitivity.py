"""Tests for the sensitivity / robustness module (sensitivity.py).

Real deterministic sweeps over the three canonical parameters; each test binds
the reported robust sub-range to both headline conclusions directly. No mocks.
"""

from __future__ import annotations

import pytest

from never_say_never_again.learning_curve import LEARNING_RATE
from never_say_never_again.mission_replay import DEFAULT_SENSITIVITY
from never_say_never_again.remount_risk import DETECTION_RATE
from never_say_never_again.sensitivity import (
    STEP_COUNT,
    SensitivityResult,
    conclusions_hold,
    robust_range,
    sensitivity_summary,
)


def test_canonical_parameters_hold_both_conclusions():
    """The canonical set is inside the robust region (positive control)."""
    assert conclusions_hold() is True
    assert conclusions_hold(sensitivity=DEFAULT_SENSITIVITY) is True
    assert conclusions_hold(detection_rate=DETECTION_RATE) is True


def test_sensitivity_result_shape_and_canonical():
    result = robust_range("sensitivity")
    assert isinstance(result, SensitivityResult)
    assert result.name == "sensitivity"
    assert result.canonical == DEFAULT_SENSITIVITY
    assert result.lo <= result.canonical <= result.hi
    assert result.hi >= result.lo
    assert result.width == pytest.approx(result.hi - result.lo)
    assert result.width > 0.0


def test_sensitivity_improvement_holds_across_the_declared_sweep():
    """Conclusion (a) — remount beats original — holds over the whole sweep.

    The remount config raises effective intel on every objective, so the op
    diff delta is positive at every sensitivity in the declared range; the
    robust sub-range therefore spans the sweep. Pinned so a future model change
    that breaks improvement at some sensitivity is a visible edit, not a
    silent one.
    """
    result = robust_range("sensitivity")
    assert result.spans_range is True
    assert result.lo == pytest.approx(0.5)
    assert result.hi == pytest.approx(20.0)
    # And the conclusion genuinely holds at both extremes of the sweep.
    assert conclusions_hold(sensitivity=0.5) is True
    assert conclusions_hold(sensitivity=20.0) is True


def test_detection_rate_robust_range_is_bounded_and_contains_canonical():
    """Conclusion (b) — keep-the-campaign-short still pays — breaks at high rate.

    As the per-replay detection rate rises, the accumulated hazard crosses the
    mission reliability sooner, so the EV zero-crossing eventually falls at or
    below the canonical campaign length. The robust sub-range is therefore
    bounded above; the canonical rate must sit inside it, and some higher rate
    must fall outside it.
    """
    result = robust_range("detection_rate")
    assert result.canonical == DETECTION_RATE
    assert result.lo <= result.canonical <= result.hi
    # Not spans: it must break inside the declared range, or the claim that the
    # campaign-short conclusion is conditional would be vacuous.
    assert result.spans_range is False
    # The rate just below the robust upper bound still holds, just above fails.
    assert conclusions_hold(detection_rate=result.hi) is True
    # A strictly higher rate that exceeds the sweep may or may not hold; use a
    # value we can verify breaks the (b) conclusion by construction: rate that
    # pushes the crossing to exactly the campaign length.
    from never_say_never_again.remount_risk import (
        CAMPAIGN_PENALTY,
        CAMPAIGN_REWARD,
        REMOUNT_RISK_BLOCKS,
        REPLAY_CAMPAIGN_LENGTH,
        optimal_campaign_length,
    )

    def crossing(rate: float) -> int:
        return optimal_campaign_length(
            rate=rate,
            blocks=REMOUNT_RISK_BLOCKS,
            reward=CAMPAIGN_REWARD,
            penalty=CAMPAIGN_PENALTY,
        )

    # At the robust upper bound itself the crossing is still above the length.
    assert crossing(result.hi) > REPLAY_CAMPAIGN_LENGTH
    assert conclusions_hold(detection_rate=result.hi) is True
    # Just past the bound the crossing falls to the campaign length (or lower),
    # so the conjunction no longer holds. Scan upward from the bound to the
    # first rate at which the crossing collapses to the canonical length.
    probe = result.hi
    while crossing(probe) > REPLAY_CAMPAIGN_LENGTH and probe < 1.0:
        probe += 0.0001
    assert crossing(probe) <= REPLAY_CAMPAIGN_LENGTH
    assert conclusions_hold(detection_rate=probe) is False


def test_learning_rate_is_insensitive_by_construction():
    """Conclusion (a)/(b) do not depend on the learning rate: full-range span."""
    result = robust_range("learning_rate")
    assert result.canonical == LEARNING_RATE
    assert result.spans_range is True
    assert result.lo == pytest.approx(0.05)
    assert result.hi == pytest.approx(1.0)


def test_summary_contains_all_three_parameters():
    summary = sensitivity_summary()
    assert set(summary) == {"sensitivity", "detection_rate", "learning_rate"}
    for result in summary.values():
        assert result.canonical > 0.0
        assert result.hi >= result.lo


def test_unknown_parameter_name_raises():
    with pytest.raises(ValueError, match="unknown parameter"):
        robust_range("not-a-parameter")


def test_detection_rate_is_the_only_parameter_where_conclusion_b_breaks():
    """Sensitivity and learning-rate robustness span the sweep; only the
    detection rate is bounded — that asymmetry is the analysis's substance."""
    summary = sensitivity_summary()
    assert summary["sensitivity"].spans_range is True
    assert summary["learning_rate"].spans_range is True
    assert summary["detection_rate"].spans_range is False


def test_step_count_is_odd_and_matches_config_contract():
    # An odd step count guarantees the canonical (mid) value is sampled exactly,
    # so the robust range is computed at the canonical point, not interpolated.
    assert STEP_COUNT % 2 == 1
