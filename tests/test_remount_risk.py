"""Tests for the remount risk module (remount_risk.py).

Real deterministic math: exponential detection hazard, series/parallel
reliability blocks, campaign expected value, and their error paths. No mocks.
"""

from __future__ import annotations

import itertools
import math

import pytest

from never_say_never_again.remount_risk import (
    CAMPAIGN_PENALTY,
    CAMPAIGN_REWARD,
    DETECTION_RATE,
    REMOUNT_RISK_BLOCKS,
    REPLAY_CAMPAIGN_LENGTH,
    RemountRiskReport,
    assess_campaign,
    block_reliability,
    campaign_expected_value,
    canonical_risk_report,
    detection_probability,
    expected_operations_before_alert,
    parallel_reliability,
    series_reliability,
)

TOL = 1e-6


def test_detection_probability_known_value():
    # 1 - exp(-0.25 * 6) = 1 - exp(-1.5) = 0.776869...
    value = detection_probability(0.25, 6)
    assert abs(value - 0.7768698398515702) < TOL
    # rate 0 -> no hazard -> P = 0.
    assert detection_probability(0.0, 5) == pytest.approx(0.0)
    # More replays -> more chance of detection (monotone).
    assert detection_probability(0.25, 10) > detection_probability(0.25, 3)


def test_detection_probability_errors():
    with pytest.raises(ValueError):
        detection_probability(-0.1, 5)
    with pytest.raises(ValueError):
        detection_probability(0.25, 0)
    with pytest.raises(ValueError):
        detection_probability(0.25, 1.5)  # type: ignore[arg-type]


def test_expected_operations_before_alert():
    assert expected_operations_before_alert(0.25) == pytest.approx(4.0)
    with pytest.raises(ValueError):
        expected_operations_before_alert(0.0)
    with pytest.raises(ValueError):
        expected_operations_before_alert(-1.0)


def test_series_reliability():
    assert series_reliability((1.0, 0.5)) == pytest.approx(0.5)
    assert series_reliability([0.8, 0.9]) == pytest.approx(0.72)
    assert series_reliability((0.5,)) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        series_reliability(())
    with pytest.raises(ValueError):
        series_reliability((1.5, 0.5))


def test_parallel_reliability():
    assert parallel_reliability((0.5,)) == pytest.approx(0.5)
    assert parallel_reliability((0.5, 0.5)) == pytest.approx(0.75)
    assert parallel_reliability((1.0, 0.0)) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        parallel_reliability(())


def test_block_reliability_matches_manual():
    blocks = ((0.86, 0.92), (0.97,), (0.88, 0.81, 0.94))
    block1 = parallel_reliability((0.86, 0.92))
    block2 = parallel_reliability((0.97,))
    block3 = parallel_reliability((0.88, 0.81, 0.94))
    expected = series_reliability((block1, block2, block3))
    assert block_reliability(blocks) == pytest.approx(expected)
    assert block_reliability(REMOUNT_RISK_BLOCKS) == canonical_risk_report().reliability


def test_block_reliability_errors():
    with pytest.raises(ValueError):
        block_reliability(())
    with pytest.raises(ValueError):
        block_reliability(((1.0,), ()))


def test_campaign_expected_value():
    # EV = 0.5 * 100 - 0.2 * 100 = 50 - 20 = 30.
    assert campaign_expected_value(0.5, 0.2, 100.0, 100.0) == pytest.approx(30.0)
    with pytest.raises(ValueError):
        campaign_expected_value(1.5, 0.2, 1.0, 1.0)
    with pytest.raises(ValueError):
        campaign_expected_value(0.5, -0.1, 1.0, 1.0)
    with pytest.raises(ValueError):
        campaign_expected_value(0.5, 0.2, -1.0, 1.0)
    with pytest.raises(ValueError):
        campaign_expected_value(0.5, 0.2, 1.0, -1.0)


def test_canonical_risk_report_values():
    report = canonical_risk_report()
    assert isinstance(report, RemountRiskReport)
    assert report.replays == REPLAY_CAMPAIGN_LENGTH
    assert (
        abs(
            report.detection_probability
            - (1.0 - math.exp(-DETECTION_RATE * REPLAY_CAMPAIGN_LENGTH))
        )
        < TOL
    )
    assert report.expected_operations == pytest.approx(1.0 / DETECTION_RATE)
    assert 0.0 < report.reliability < 1.0
    assert report.campaign_ev == pytest.approx(
        report.reliability * CAMPAIGN_REWARD
        - report.detection_probability * CAMPAIGN_PENALTY
    )
    # Canonical narrative: a 6-replay campaign still has positive EV but the
    # accumulated detection hazard is substantial.
    assert report.detection_probability > 0.7
    assert report.campaign_ev > 0.0


def test_campaign_ev_declines_as_replays_grow():
    short = assess_campaign(
        rate=0.25, replays=2, blocks=REMOUNT_RISK_BLOCKS, reward=100.0, penalty=100.0
    )
    long = assess_campaign(
        rate=0.25, replays=12, blocks=REMOUNT_RISK_BLOCKS, reward=100.0, penalty=100.0
    )
    assert long.detection_probability > short.detection_probability
    assert long.campaign_ev < short.campaign_ev


def test_risk_report_validation():
    with pytest.raises(ValueError):
        RemountRiskReport(
            replays=0,
            detection_probability=0.5,
            expected_operations=4.0,
            reliability=0.9,
            campaign_ev=1.0,
        )
    with pytest.raises(ValueError):
        RemountRiskReport(
            replays=3,
            detection_probability=1.5,
            expected_operations=4.0,
            reliability=0.9,
            campaign_ev=1.0,
        )
    with pytest.raises(ValueError):
        RemountRiskReport(
            replays=3,
            detection_probability=0.5,
            expected_operations=-1.0,
            reliability=0.9,
            campaign_ev=1.0,
        )
    with pytest.raises(ValueError):
        RemountRiskReport(
            replays=3,
            detection_probability=0.5,
            expected_operations=4.0,
            reliability=1.5,
            campaign_ev=1.0,
        )


def test_campaign_ev_is_strictly_decreasing_in_replay_count():
    """The manuscript's central risk claim, asserted over the real model.

    03_results.md argues the campaign expected value strictly decreases in the
    replay count N, because reliability is constant in N while the detection
    term rises monotonically. This binds that prose to the code.
    """
    reliability = block_reliability(REMOUNT_RISK_BLOCKS)
    values = [
        campaign_expected_value(
            reliability,
            detection_probability(DETECTION_RATE, n),
            CAMPAIGN_REWARD,
            CAMPAIGN_PENALTY,
        )
        for n in range(1, 41)
    ]
    assert all(later < earlier for earlier, later in itertools.pairwise(values))


def test_campaign_ev_crosses_zero_and_stays_negative():
    """The crossing the manuscript describes exists and is not an artifact.

    A monotone-decreasing sequence is only interesting if it actually changes
    sign inside a plausible campaign length — otherwise "keep the campaign
    short" would be advice about nothing.
    """
    reliability = block_reliability(REMOUNT_RISK_BLOCKS)

    def ev(n: int) -> float:
        return campaign_expected_value(
            reliability,
            detection_probability(DETECTION_RATE, n),
            CAMPAIGN_REWARD,
            CAMPAIGN_PENALTY,
        )

    assert ev(REPLAY_CAMPAIGN_LENGTH) > 0.0, "canonical campaign should still pay"

    crossing = next(n for n in range(1, 200) if ev(n) <= 0.0)
    assert crossing > REPLAY_CAMPAIGN_LENGTH
    # Once negative it never recovers.
    assert all(ev(n) < 0.0 for n in range(crossing + 1, crossing + 20))
    # With equal reward and penalty the crossing is where hazard meets
    # reliability — the specific claim made in the results section.
    assert detection_probability(DETECTION_RATE, crossing) >= reliability
    assert detection_probability(DETECTION_RATE, crossing - 1) < reliability


def test_redundancy_strictly_helps_and_series_strictly_hurts():
    """Positive control on the block model: structure must actually matter."""
    single = block_reliability(((0.8,),))
    redundant = block_reliability(((0.8, 0.8),))
    chained = block_reliability(((0.8,), (0.8,)))
    assert redundant > single > chained
    assert redundant == pytest.approx(1 - 0.2 * 0.2, abs=TOL)
    assert chained == pytest.approx(0.64, abs=TOL)
