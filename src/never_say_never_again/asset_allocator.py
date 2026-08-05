"""Asset allocation — deterministic marginal-gain assignment for the remount.

Remastered assets (captured gadgets, refined intel dossiers) are scarce: the
remount can deploy only ``budget`` assets across its objectives. This module
allocates them greedily by *marginal gain* — the canonical submodular
maximization heuristic of Nemhauser–Wolsey–Fisher (1978), which guarantees a
``(1 - 1/e)`` approximation for monotone submodular objectives.

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

The module is pure (stdlib only) and fully deterministic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "ALLOCATION_BUDGET",
    "ALLOCATION_POOL",
    "AllocatableObjective",
    "AllocationPlan",
    "allocate",
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
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0.0:
        raise ValueError(f"{label} must be a non-negative number")


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
            or self.weight <= 0.0
        ):
            raise ValueError("AllocatableObjective.weight must be a positive number")
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
    marginal maximizes the wrong function: on the canonical pool it produced a
    plan strictly worse than a naive uniform spread, while still reporting a
    ``(1 - 1/e)`` guarantee that only holds for the function actually being
    maximized. ``tests/test_asset_allocator.py`` pins the comparison.
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


#: Canonical allocatable objectives (mirrors the THUNDERBALL-65 objective set).
ALLOCATION_POOL: tuple[AllocatableObjective, ...] = (
    AllocatableObjective(
        objective_id="recover_weapons",
        weight=0.35,
        base_score=0.42,
        improvement_cap=0.30,
        efficiency=1.2,
    ),
    AllocatableObjective(
        objective_id="neutralize_cell",
        weight=0.30,
        base_score=0.40,
        improvement_cap=0.35,
        efficiency=1.0,
    ),
    AllocatableObjective(
        objective_id="extract_agent",
        weight=0.20,
        base_score=0.45,
        improvement_cap=0.25,
        efficiency=1.4,
    ),
    AllocatableObjective(
        objective_id="deny_blackmail",
        weight=0.15,
        base_score=0.38,
        improvement_cap=0.40,
        efficiency=0.8,
    ),
)

#: Canonical asset budget for the remount.
ALLOCATION_BUDGET = 6


def canonical_allocation() -> AllocationPlan:
    """The canonical deterministic allocation used across the package."""
    return allocate(ALLOCATION_POOL, ALLOCATION_BUDGET)
