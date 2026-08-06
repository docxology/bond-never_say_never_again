"""Asset allocation — deterministic marginal-gain assignment for the remount.

Remastered assets (captured gadgets, refined intel dossiers) are scarce: the
remount can deploy only ``budget`` assets across its objectives. This module
allocates them greedily by *marginal gain* — the canonical submodular
maximization heuristic of Nemhauser–Wolsey–Fisher (1978), whose general
guarantee is a ``(1 - 1/e)`` approximation for monotone submodular objectives.
The problem here is the easier separable-concave special case (the objective is
a weighted sum of per-objective concave curves in the assets assigned to that
objective), where greedy incremental allocation is not merely within a factor
but *exactly optimal*. ``tests/test_asset_allocator.py`` confirms that by
exhaustive enumeration on the canonical pool rather than resting on the
citation.

* :func:`improvement_curve` — concave (diminishing-returns) improvement of an
  objective's score with ``k`` assigned assets: ``cap * (1 - exp(-e * k))``.
* :func:`marginal_gain` — the improvement curve's increment per extra asset.
* :func:`allocate` — deterministic greedy: at each of ``budget`` rounds assign
  one asset to the objective with the largest *weight-scaled* capped marginal
  gain, breaking ties by objective order (stable, byte-identical). Scaling by
  weight is what makes the greedy maximize the same weighted score the plan
  reports; selecting on the raw score gain instead maximizes a different
  function and forfeits the guarantee.
* :class:`AllocationPlan` — assignments, per-asset marginal gains, final
  weighted score, and the gain ratio vs full saturation.
* :func:`build_allocation_pool` — derives the allocatable objectives from a
  scenario and one of its replays, so ids, weights, and base scores are never
  re-declared here.

The module is deterministic and depends only on the stdlib plus the pure
:mod:`~never_say_never_again.mission_replay` core.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    RemountConfig,
    ReplayEngine,
    Scenario,
)

__all__ = [
    "ALLOCATION_BUDGET",
    "ALLOCATION_CURVES",
    "ALLOCATION_POOL",
    "AllocatableObjective",
    "AllocationPlan",
    "allocate",
    "build_allocation_pool",
    "canonical_allocation",
    "improvement_curve",
    "marginal_gain",
]


def improvement_curve(assets: int, cap: float, efficiency: float) -> float:
    """Concave improvement after assigning ``assets`` assets.

    ``cap * (1 - exp(-efficiency * assets))`` — grows toward ``cap`` with
    strictly diminishing returns (submodular).
    """
    if isinstance(assets, bool) or not isinstance(assets, int) or assets < 0:
        raise ValueError("assets must be a non-negative integer")
    _require_non_negative(cap, "cap")
    _require_non_negative(efficiency, "efficiency")
    return cap * (1.0 - math.exp(-efficiency * assets))


def marginal_gain(assets: int, cap: float, efficiency: float) -> float:
    """Marginal score improvement of the next asset at count ``assets``."""
    return improvement_curve(assets + 1, cap, efficiency) - improvement_curve(
        assets, cap, efficiency
    )


def _require_non_negative(value: float, label: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value < 0.0
    ):
        raise ValueError(f"{label} must be a finite non-negative number")


def _require_probability(value: float, label: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not (0.0 <= value <= 1.0)
    ):
        raise ValueError(f"{label} must be a number in [0, 1]")


@dataclass(frozen=True)
class AllocatableObjective:
    """An objective eligible for asset allocation.

    Attributes:
        objective_id: Stable objective identifier.
        weight: Relative importance (> 0).
        base_score: Score with zero assigned assets, in [0, 1].
        improvement_cap: Maximum score improvement from assets, >= 0.
        efficiency: Concavity/steepness of the improvement curve, >= 0.
    """

    objective_id: str
    weight: float
    base_score: float
    improvement_cap: float
    efficiency: float

    def __post_init__(self) -> None:
        if not isinstance(self.objective_id, str) or not self.objective_id.strip():
            raise ValueError(
                "AllocatableObjective.objective_id must be a non-empty string"
            )
        if (
            isinstance(self.weight, bool)
            or not isinstance(self.weight, (int, float))
            or not math.isfinite(float(self.weight))
            or self.weight <= 0.0
        ):
            raise ValueError(
                "AllocatableObjective.weight must be a finite positive number"
            )
        _require_probability(self.base_score, "AllocatableObjective.base_score")
        _require_non_negative(
            self.improvement_cap, "AllocatableObjective.improvement_cap"
        )
        _require_non_negative(self.efficiency, "AllocatableObjective.efficiency")


def _score_with(objective: AllocatableObjective, assets: int) -> float:
    """Capped final score of an objective with ``assets`` assigned."""
    return min(
        1.0,
        objective.base_score
        + improvement_curve(assets, objective.improvement_cap, objective.efficiency),
    )


def _capped_marginal(objective: AllocatableObjective, assets: int) -> float:
    """True marginal gain at ``assets``, respecting the score ceiling of 1.0."""
    return _score_with(objective, assets + 1) - _score_with(objective, assets)


def _weighted_marginal(objective: AllocatableObjective, assets: int) -> float:
    """Marginal gain in the *objective function the plan reports*.

    The plan's ``total_weighted_score`` is a weight-weighted sum, so the
    quantity a greedy must maximize per asset is the weight-scaled marginal
    gain — not the raw score gain.

    This distinction is load-bearing, not cosmetic. Selecting on the unweighted
    marginal maximizes the wrong function: on the canonical pool it produces a
    plan strictly worse than this one — and worse than the exhaustive optimum —
    while still claiming an optimality guarantee that only holds for the
    function actually being maximized. ``tests/test_asset_allocator.py`` pins
    that comparison as the negative control for the optimality gate.
    """
    return objective.weight * _capped_marginal(objective, assets)


@dataclass(frozen=True)
class AllocationPlan:
    """Deterministic allocation result.

    Attributes:
        assignments: objective_id → number of assets assigned.
        final_scores: objective_id → capped final score.
        marginal_gains: Per-asset *weighted* marginal gains, in allocation
            order — each entry is the increase in ``total_weighted_score``
            bought by that asset, so the entries sum to ``total_gain``.
        total_weighted_score: Weighted sum of final scores.
        total_gain: Weighted score improvement over the zero-asset baseline.
        gain_ratio: ``total_gain`` over the weighted full-saturation ceiling,
            in [0, 1] (1.0 = every objective saturated).
    """

    assignments: dict[str, int]
    final_scores: dict[str, float]
    marginal_gains: tuple[float, ...]
    total_weighted_score: float
    total_gain: float
    gain_ratio: float


def allocate(
    objectives: tuple[AllocatableObjective, ...], budget: int
) -> AllocationPlan:
    """Greedily allocate ``budget`` assets across ``objectives`` by marginal gain.

    Each round assigns one asset to the objective with the largest
    *weight-scaled* capped marginal gain — the marginal increase in the plan's
    own ``total_weighted_score``, which is the monotone submodular function the
    ``(1 - 1/e)`` guarantee applies to. Ties resolve to the earlier objective in
    the given order, so the result is deterministic and byte-stable.

    The loop stops early when every objective is saturated (gain <= 0), in
    which case fewer than ``budget`` assets are deployed.
    """
    if not objectives:
        raise ValueError("objectives must be non-empty")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        raise ValueError("budget must be a non-negative integer")
    for objective in objectives:
        if not isinstance(objective, AllocatableObjective):
            raise ValueError(
                "objectives entries must be AllocatableObjective instances"
            )

    assignments = {objective.objective_id: 0 for objective in objectives}
    gains: list[float] = []
    for _ in range(budget):
        best: AllocatableObjective | None = None
        best_gain = -1.0
        for objective in objectives:
            candidate = _weighted_marginal(
                objective, assignments[objective.objective_id]
            )
            if candidate > best_gain:  # strict > keeps the first objective on ties
                best_gain = candidate
                best = objective
        if best is None or best_gain <= 0.0:
            break
        assignments[best.objective_id] += 1
        gains.append(best_gain)

    final_scores = {
        objective.objective_id: _score_with(
            objective, assignments[objective.objective_id]
        )
        for objective in objectives
    }
    baseline = sum(objective.weight * objective.base_score for objective in objectives)
    total_weighted = sum(
        objective.weight * final_scores[objective.objective_id]
        for objective in objectives
    )
    ceiling = sum(
        objective.weight * min(1.0, objective.base_score + objective.improvement_cap)
        for objective in objectives
    )
    total_gain = total_weighted - baseline
    gain_ratio = total_gain / (ceiling - baseline) if ceiling > baseline else 0.0

    return AllocationPlan(
        assignments=assignments,
        final_scores=final_scores,
        marginal_gains=tuple(gains),
        total_weighted_score=total_weighted,
        total_gain=total_gain,
        gain_ratio=gain_ratio,
    )


#: Per-objective allocation-curve parameters, ``objective_id -> (cap,
#: efficiency)``. These two numbers are *stipulated model inputs*: how much a
#: remastered asset can ultimately buy on an objective, and how fast those
#: returns diminish. No operational data calibrates them.
#:
#: What is deliberately NOT declared here: objective ids, weights, and base
#: scores. Those are derived in :func:`build_allocation_pool` from the
#: canonical scenario and its remount replay. An earlier version re-declared
#: all of them alongside the scenario's own copies, with nothing binding the
#: two sets — a silent-drift hazard, and the reason the manuscript's claim that
#: allocation gains are in units of weighted command score was unsupported.
ALLOCATION_CURVES: dict[str, tuple[float, float]] = {
    "recover_weapons": (0.30, 1.2),
    "neutralize_cell": (0.35, 1.0),
    "extract_agent": (0.25, 1.4),
    "deny_blackmail": (0.40, 0.8),
}


def build_allocation_pool(
    scenario: Scenario = LEGACY_SCENARIO,
    config: RemountConfig = REMOUNT_CONFIG,
    *,
    engine: ReplayEngine | None = None,
    curves: dict[str, tuple[float, float]] | None = None,
) -> tuple[AllocatableObjective, ...]:
    """Derive allocatable objectives from a scenario and one of its replays.

    Each objective keeps the scenario's ``objective_id`` and ``weight``, and
    takes as its ``base_score`` the score that objective actually achieves when
    ``scenario`` is replayed under ``config``. Only the improvement cap and
    efficiency come from ``curves``.

    Because the base scores are real replay scores, the plan's weighted totals
    are in the same units as :attr:`~.mission_replay.ReplayResult.command_score`
    (exactly equal to it whenever the scenario's weights sum to one, which
    ``tests/test_asset_allocator.py`` pins for the canonical scenario).

    Raises:
        ValueError: if any scenario objective has no declared curve.
    """
    curves = ALLOCATION_CURVES if curves is None else curves
    engine = engine if engine is not None else ReplayEngine()
    result = engine.replay(scenario, config)
    scores = {outcome.objective_id: outcome.score for outcome in result.outcomes}
    missing = [
        spec.objective_id
        for spec in scenario.objectives
        if spec.objective_id not in curves
    ]
    if missing:
        raise ValueError(f"no allocation curve declared for objectives: {missing}")
    return tuple(
        AllocatableObjective(
            objective_id=spec.objective_id,
            weight=spec.weight,
            base_score=scores[spec.objective_id],
            improvement_cap=curves[spec.objective_id][0],
            efficiency=curves[spec.objective_id][1],
        )
        for spec in scenario.objectives
    )


#: Canonical allocatable objectives — derived from THUNDERBALL-65 replayed
#: under ``REMOUNT_CONFIG``, never re-declared.
ALLOCATION_POOL: tuple[AllocatableObjective, ...] = build_allocation_pool()

#: Canonical asset budget for the remount.
ALLOCATION_BUDGET = 6


def canonical_allocation() -> AllocationPlan:
    """The canonical deterministic allocation used across the package."""
    return allocate(ALLOCATION_POOL, ALLOCATION_BUDGET)
