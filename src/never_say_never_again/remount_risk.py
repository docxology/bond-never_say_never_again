"""Remount risk — escalation hazard, mission reliability, campaign value.

A legacy remount is never free: every replay operation raises the probability
that the adversary (Spectre) detects the re-op, and the mission only pays off
if the operation's critical objectives all succeed. This module models both
deterministically:

* :func:`detection_probability` — the memoryless exponential (Poisson) hazard:
  ``P(alert within N replays) = 1 - exp(-rate * N)``.
* :func:`expected_operations_before_alert` — ``E[N] = 1 / rate``.
* :func:`series_reliability` / :func:`parallel_reliability` /
  :func:`block_reliability` — mission success under series/parallel
  (redundancy) structure, i.e. a reliability block diagram.
* :func:`campaign_expected_value` — ``P(success) * reward - P(detected) *
  penalty``.
* :func:`assess_campaign` — aggregates the four into a
  :class:`RemountRiskReport`, and :func:`canonical_risk_report` locks the
  canonical dataset.

The module is pure (stdlib only): no randomness, no wall-clock — a campaign is
assessed in closed form.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "CAMPAIGN_PENALTY",
    "CAMPAIGN_REWARD",
    "DETECTION_RATE",
    "REMOUNT_RISK_BLOCKS",
    "REPLAY_CAMPAIGN_LENGTH",
    "RemountRiskReport",
    "assess_campaign",
    "block_reliability",
    "campaign_expected_value",
    "canonical_risk_report",
    "detection_probability",
    "expected_operations_before_alert",
    "optimal_campaign_length",
    "parallel_reliability",
    "series_reliability",
]

#: Canonical per-replay detection hazard (adversary alert rate).
DETECTION_RATE = 0.25

#: Canonical replay-campaign length (number of replay operations considered).
REPLAY_CAMPAIGN_LENGTH = 6

#: Canonical reward for a successful mission and penalty for a detected re-op.
CAMPAIGN_REWARD = 100.0
CAMPAIGN_PENALTY = 100.0

#: Canonical reliability blocks: a series of parallel blocks, each block a
#: tuple of per-path success probabilities. (intel acquisition has two
#: redundant paths; insertion one path; extraction three.)
#: Upper limit for the :func:`optimal_campaign_length` scan. Generous but
#: bounded so a shrinking detection horizon cannot spin indefinitely.
_MAX_CROSSING_SCAN = 10000


REMOUNT_RISK_BLOCKS: tuple[tuple[float, ...], ...] = (
    (0.86, 0.92),
    (0.97,),
    (0.88, 0.81, 0.94),
)


def _require_probability(value: float, label: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not (0.0 <= value <= 1.0)
    ):
        raise ValueError(f"{label} must be a number in [0, 1]")


def _require_non_negative(value: float, label: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value < 0.0
    ):
        raise ValueError(f"{label} must be a finite non-negative number")


def detection_probability(rate: float, replays: int) -> float:
    """P(adversary alert within ``replays`` replay operations).

    The exponential hazard ``1 - exp(-rate * replays)`` is the closed form of a
    Poisson detection process with per-replay intensity ``rate``.
    """
    _require_non_negative(rate, "rate")
    if isinstance(replays, bool) or not isinstance(replays, int) or replays < 1:
        raise ValueError("replays must be a positive integer")
    return 1.0 - math.exp(-rate * replays)


def expected_operations_before_alert(rate: float) -> float:
    """Expected number of replay operations before the first alert (1/rate)."""
    if (
        isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(float(rate))
        or rate <= 0.0
    ):
        raise ValueError("rate must be a finite positive number")
    return 1.0 / rate


def series_reliability(probabilities: tuple[float, ...] | list[float]) -> float:
    """Reliability of a series structure: every element must succeed."""
    if not probabilities:
        raise ValueError("probabilities must be non-empty")
    reliability = 1.0
    for probability in probabilities:
        _require_probability(probability, "probability")
        reliability *= probability
    return reliability


def parallel_reliability(probabilities: tuple[float, ...] | list[float]) -> float:
    """Reliability of a parallel structure: any one element suffices."""
    if not probabilities:
        raise ValueError("probabilities must be non-empty")
    failure = 1.0
    for probability in probabilities:
        _require_probability(probability, "probability")
        failure *= 1.0 - probability
    return 1.0 - failure


def block_reliability(blocks: tuple[tuple[float, ...], ...]) -> float:
    """Reliability of a series of parallel blocks (a reliability block diagram).

    Each block is a tuple of per-path success probabilities; the mission
    succeeds when every block succeeds and each block succeeds when any of its
    redundant paths succeeds.
    """
    if not blocks:
        raise ValueError("blocks must be non-empty")
    block_probabilities: list[float] = []
    for block in blocks:
        if not block:
            raise ValueError("each reliability block must be non-empty")
        block_probabilities.append(parallel_reliability(block))
    return series_reliability(tuple(block_probabilities))


def campaign_expected_value(
    success_probability: float,
    detection_probability_value: float,
    reward: float,
    penalty: float,
) -> float:
    """Expected value of a replay campaign: success reward minus detection cost."""
    _require_probability(success_probability, "success_probability")
    _require_probability(detection_probability_value, "detection_probability")
    _require_non_negative(reward, "reward")
    _require_non_negative(penalty, "penalty")
    return success_probability * reward - detection_probability_value * penalty


def optimal_campaign_length(
    *,
    rate: float,
    blocks: tuple[tuple[float, ...], ...],
    reward: float,
    penalty: float,
) -> int:
    """Smallest replay count ``N`` at which the campaign expected value (first)
    becomes non-positive, i.e. the last length at which the campaign still pays.

    ``campaign_ev`` is strictly decreasing in the replay count ``N`` (reliability
    is constant in ``N`` while the detection term ``1 - exp(-rate * N)`` rises),
    so the crossing is unique. Returns ``1`` when even a single replay is
    already non-positive. Raises ``ValueError`` when the campaign never crosses
    into non-positive territory within ``1.._MAX_CROSSING_SCAN`` replays (the
    asymptote ``reliability * reward - penalty`` stays positive).
    """
    _require_non_negative(rate, "rate")
    _require_non_negative(reward, "reward")
    _require_non_negative(penalty, "penalty")
    reliability = block_reliability(blocks)

    def _ev(n: int) -> float:
        return campaign_expected_value(
            reliability,
            detection_probability(rate, n),
            reward,
            penalty,
        )

    # Scan upward from 1. The sequence is strictly decreasing, so the first
    # non-positive value is the crossing. The bound is generous: detection
    # probability reaches 1 - exp(-rate * N) which drives EV toward the
    # asymptote; with finite reward/penalty the crossing is reached quickly or
    # the asymptote is positive (never crosses).
    for n in range(1, _MAX_CROSSING_SCAN):
        if _ev(n) <= 0.0:
            return n
    raise ValueError(
        "campaign never crosses non-positive within "
        f"{_MAX_CROSSING_SCAN - 1} replays at the given parameters"
    )


@dataclass(frozen=True)
class RemountRiskReport:
    """Deterministic risk assessment of a replay campaign.

    Attributes:
        replays: Number of replay operations assessed.
        detection_probability: P(adversary alert within the campaign).
        expected_operations: Expected replays before the first alert (1/rate).
        reliability: Mission success probability under the block structure.
        campaign_ev: Expected value of the campaign (reward minus detection).
    """

    replays: int
    detection_probability: float
    expected_operations: float
    reliability: float
    campaign_ev: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.replays, bool)
            or not isinstance(self.replays, int)
            or self.replays < 1
        ):
            raise ValueError("RemountRiskReport.replays must be a positive integer")
        _require_probability(
            self.detection_probability, "RemountRiskReport.detection_probability"
        )
        _require_non_negative(
            self.expected_operations, "RemountRiskReport.expected_operations"
        )
        _require_probability(self.reliability, "RemountRiskReport.reliability")


def assess_campaign(
    *,
    rate: float,
    replays: int,
    blocks: tuple[tuple[float, ...], ...],
    reward: float,
    penalty: float,
) -> RemountRiskReport:
    """Assess a replay campaign: detection hazard, reliability, and expected value."""
    detection = detection_probability(rate, replays)
    reliability = block_reliability(blocks)
    campaign_ev = campaign_expected_value(reliability, detection, reward, penalty)
    return RemountRiskReport(
        replays=replays,
        detection_probability=detection,
        expected_operations=expected_operations_before_alert(rate),
        reliability=reliability,
        campaign_ev=campaign_ev,
    )


def canonical_risk_report() -> RemountRiskReport:
    """The canonical deterministic risk assessment used across the package."""
    return assess_campaign(
        rate=DETECTION_RATE,
        replays=REPLAY_CAMPAIGN_LENGTH,
        blocks=REMOUNT_RISK_BLOCKS,
        reward=CAMPAIGN_REWARD,
        penalty=CAMPAIGN_PENALTY,
    )
