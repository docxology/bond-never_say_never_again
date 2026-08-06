"""Sensitivity / robustness analysis for the REMOUNT conclusions.

The manuscript's two headline conclusions are produced at a single canonical
parameter set. This module asks how *fragile* they are: for each of the three
parameters the conclusions rest on, it sweeps that parameter over a declared
range (holding the other two at their canonical values) and reports the largest
contiguous sub-range — containing the canonical value — over which **both**
headline conclusions still hold:

* **(a)** ``OpDiff.overall == "improved"`` — the remount beats the original;
* **(b)** the campaign expected value stays positive at the canonical campaign
  length (its zero crossing sits above ``REPLAY_CAMPAIGN_LENGTH``) — i.e. the
  "keep the remount short" advice is still operating advice.

``(b)`` is evaluated via :func:`~.remount_risk.optimal_campaign_length`, so this
module binds the two conclusions to the same crossing the risk model reports.

The module is pure (stdlib only).

The three swept parameters:

* ``DEFAULT_SENSITIVITY`` (``mission_replay``) — sway over conclusion (a);
* ``DETECTION_RATE`` (``remount_risk``) — sway over conclusion (b);
* ``LEARNING_RATE`` (``learning_curve``) — by construction affects neither
  ``(a)`` (op diff ignores rehearsal) nor ``(b)`` (risk ignores rehearsal), so
  its robust sub-range is the *whole* declared range; that insensitivity is
  itself a reported result, not an omission.
"""

from __future__ import annotations

from dataclasses import dataclass

from never_say_never_again.learning_curve import LEARNING_RATE
from never_say_never_again.mission_replay import (
    DEFAULT_SENSITIVITY,
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    RemountConfig,
    ReplayEngine,
)
from never_say_never_again.op_diff import diff_outcomes
from never_say_never_again.remount_risk import (
    CAMPAIGN_PENALTY,
    CAMPAIGN_REWARD,
    DETECTION_RATE,
    REMOUNT_RISK_BLOCKS,
    REPLAY_CAMPAIGN_LENGTH,
    optimal_campaign_length,
)

__all__ = [
    "DETECTION_RATE_RANGE",
    "LEARNING_RATE_RANGE",
    "SENSITIVITY_RANGE",
    "STEP_COUNT",
    "SensitivityResult",
    "conclusions_hold",
    "robust_range",
    "sensitivity_summary",
]

#: Declared sweep ranges for each canonical parameter (inclusive lower/upper).
SENSITIVITY_RANGE = (0.5, 20.0)
DETECTION_RATE_RANGE = (0.05, 1.0)
LEARNING_RATE_RANGE = (0.05, 1.0)

#: Number of linearly-spaced samples per sweep.
STEP_COUNT = 401

#: The identity config (no remount deltas) used as the ``original`` reference.
_IDENTITY_CONFIG = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)


@dataclass(frozen=True)
class SensitivityResult:
    """Robust sub-range of one parameter over which both conclusions hold.

    Attributes:
        name: The parameter key (``sensitivity`` / ``detection_rate`` /
            ``learning_rate``).
        canonical: The canonical value of the parameter.
        lo: Lower bound of the robust sub-range (parameter units).
        hi: Upper bound of the robust sub-range (parameter units).
        spans_range: True when the robust sub-range hits both declared ends of
            the sweep, meaning the conclusion does not break anywhere tested.
    """

    name: str
    canonical: float
    lo: float
    hi: float
    spans_range: bool

    @property
    def width(self) -> float:
        """Signed width ``hi - lo`` of the robust sub-range."""
        return self.hi - self.lo


def conclusions_hold(
    sensitivity: float | None = None,
    detection_rate: float | None = None,
) -> bool:
    """True when both headline conclusions hold at the given parameter values.

    ``(a)`` requires an ``improved`` op diff; ``(b)`` requires the campaign EV
    zero crossing to sit above the canonical campaign length. Parameters left
    ``None`` use their canonical values as defaults for whichever conclusion
    does not depend on them.
    """
    engine = ReplayEngine(sensitivity=float(sensitivity or DEFAULT_SENSITIVITY))
    original = engine.replay(LEGACY_SCENARIO, _IDENTITY_CONFIG)
    remount = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    a_improved = diff_outcomes(original, remount).overall == "improved"

    rate = float(detection_rate if detection_rate is not None else DETECTION_RATE)
    b_positive = (
        optimal_campaign_length(
            rate=rate,
            blocks=REMOUNT_RISK_BLOCKS,
            reward=CAMPAIGN_REWARD,
            penalty=CAMPAIGN_PENALTY,
        )
        > REPLAY_CAMPAIGN_LENGTH
    )

    return a_improved and b_positive


def _linspace(lo: float, hi: float, steps: int) -> list[float]:
    """``steps`` samples from ``lo`` to ``hi`` inclusive (deterministic)."""
    return [lo + (hi - lo) * i / (steps - 1) for i in range(steps)]


def _longest_run_containing(
    values: list[float],
    holds: list[bool],
    index: int,
) -> tuple[float, float]:
    """Extent of the contiguous ``True`` run in ``holds`` containing ``index``."""
    lo_idx = index
    while lo_idx > 0 and holds[lo_idx - 1]:
        lo_idx -= 1
    hi_idx = index
    while hi_idx < len(holds) - 1 and holds[hi_idx + 1]:
        hi_idx += 1
    return values[lo_idx], values[hi_idx]


def robust_range(name: str) -> SensitivityResult:
    """Robust sub-range for one swept parameter (see module docstring).

    Args:
        name: One of ``"sensitivity"``, ``"detection_rate"``,
            ``"learning_rate"``.

    Returns:
        The robust sub-range containing the canonical value. For
        ``"learning_rate"`` the conclusion is independent of the parameter, so
        the returned range spans the whole declared sweep (``spans_range=True``).
    """
    if name == "sensitivity":
        lo, hi = SENSITIVITY_RANGE
        canonical = DEFAULT_SENSITIVITY
        values = _linspace(lo, hi, STEP_COUNT)
        holds = [conclusions_hold(sensitivity=v) for v in values]
    elif name == "detection_rate":
        lo, hi = DETECTION_RATE_RANGE
        canonical = DETECTION_RATE
        values = _linspace(lo, hi, STEP_COUNT)
        holds = [conclusions_hold(detection_rate=v) for v in values]
    elif name == "learning_rate":
        lo, hi = LEARNING_RATE_RANGE
        canonical = LEARNING_RATE
        values = _linspace(lo, hi, STEP_COUNT)
        holds = [conclusions_hold() for _ in values]
    else:
        raise ValueError(f"unknown parameter name: {name!r}")

    index = min(range(len(values)), key=lambda i: abs(values[i] - canonical))
    sub_lo, sub_hi = _longest_run_containing(values, holds, index)
    spans = sub_lo == values[0] and sub_hi == values[-1]
    return SensitivityResult(
        name=name, canonical=canonical, lo=sub_lo, hi=sub_hi, spans_range=spans
    )


def sensitivity_summary() -> dict[str, SensitivityResult]:
    """Robust sub-range for each of the three swept parameters, keyed by name."""
    return {
        name: robust_range(name)
        for name in ("sensitivity", "detection_rate", "learning_rate")
    }
