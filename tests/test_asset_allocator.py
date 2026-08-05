"""Tests for the asset allocator module (asset_allocator.py).

Real deterministic math: concave improvement curves, diminishing marginal
gains, and the greedy (submodular) allocation with deterministic tie-breaking.
No mocks.
"""

from __future__ import annotations

import math

import pytest

from never_say_never_again.asset_allocator import (
    ALLOCATION_BUDGET,
    ALLOCATION_POOL,
    AllocatableObjective,
    AllocationPlan,
    allocate,
    canonical_allocation,
    improvement_curve,
    marginal_gain,
)

TOL = 1e-9


def test_improvement_curve_is_concave_diminishing():
    cap, efficiency = 0.40, 1.0
    v0 = improvement_curve(0, cap, efficiency)
    v1 = improvement_curve(1, cap, efficiency)
    v2 = improvement_curve(2, cap, efficiency)
    v3 = improvement_curve(3, cap, efficiency)
    assert v0 == pytest.approx(0.0)
    # Strictly diminishing increments (concave).
    assert (v1 - v0) > (v2 - v1) > (v3 - v2) > 0.0
    # Approaches the cap asymptotically.
    assert improvement_curve(100, cap, efficiency) == pytest.approx(cap, rel=1e-6)


def test_improvement_curve_exact_value():
    # cap * (1 - exp(-e * k)) with cap=0.4, e=1.0, k=2.
    assert improvement_curve(2, 0.4, 1.0) == pytest.approx(0.4 * (1 - math.exp(-2.0)))
    # e=0 -> no improvement.
    assert improvement_curve(5, 0.4, 0.0) == pytest.approx(0.0)


def test_improvement_curve_errors():
    with pytest.raises(ValueError):
        improvement_curve(-1, 0.4, 1.0)
    with pytest.raises(ValueError):
        improvement_curve(1, -0.1, 1.0)
    with pytest.raises(ValueError):
        improvement_curve(1, 0.4, -0.1)
    with pytest.raises(ValueError):
        improvement_curve(True, 0.4, 1.0)  # type: ignore[arg-type]


def test_marginal_gain_equals_curve_increment():
    cap, efficiency = 0.30, 1.2
    assert marginal_gain(3, cap, efficiency) == pytest.approx(
        improvement_curve(4, cap, efficiency) - improvement_curve(3, cap, efficiency)
    )


def test_canonical_allocation_is_deterministic():
    first = allocate(ALLOCATION_POOL, ALLOCATION_BUDGET)
    second = allocate(ALLOCATION_POOL, ALLOCATION_BUDGET)
    assert first.assignments == second.assignments
    assert first.marginal_gains == second.marginal_gains
    assert first == second
    assert canonical_allocation() == first


def test_canonical_allocation_uses_full_budget_and_improves():
    plan = canonical_allocation()
    assert isinstance(plan, AllocationPlan)
    assert sum(plan.assignments.values()) == ALLOCATION_BUDGET
    assert len(plan.marginal_gains) == ALLOCATION_BUDGET
    baseline = sum(o.weight * o.base_score for o in ALLOCATION_POOL)
    assert plan.total_weighted_score > baseline
    assert 0.0 < plan.gain_ratio < 1.0
    assert plan.total_gain > 0.0


def test_allocation_assigns_all_budget_across_pool():
    plan = canonical_allocation()
    assert sum(plan.assignments.values()) == 6
    assert sorted(plan.assignments) == sorted(o.objective_id for o in ALLOCATION_POOL)
    for objective in ALLOCATION_POOL:
        assert plan.final_scores[objective.objective_id] >= objective.base_score


def test_allocation_zero_budget_returns_baseline():
    plan = allocate(ALLOCATION_POOL, 0)
    assert sum(plan.assignments.values()) == 0
    assert plan.marginal_gains == ()
    assert plan.total_gain == pytest.approx(0.0)


def test_allocation_saturates_with_large_budget():
    plan = allocate(ALLOCATION_POOL, 100)
    # Every objective saturates to the score ceiling (1.0 or base+cap).
    for objective in ALLOCATION_POOL:
        expected = min(1.0, objective.base_score + objective.improvement_cap)
        assert plan.final_scores[objective.objective_id] == pytest.approx(expected)


def test_allocation_zero_cap_yields_zero_gain_ratio():
    objectives = (
        AllocatableObjective(
            objective_id="a",
            weight=1.0,
            base_score=0.5,
            improvement_cap=0.0,
            efficiency=1.0,
        ),
    )
    plan = allocate(objectives, 5)
    assert plan.total_gain == pytest.approx(0.0)
    assert plan.gain_ratio == pytest.approx(0.0)


def test_allocation_deterministic_tie_break():
    # Two objectives with identical curves: the earlier id always wins each
    # asset, never oscillating.
    objectives = (
        AllocatableObjective(
            objective_id="a",
            weight=1.0,
            base_score=0.5,
            improvement_cap=0.3,
            efficiency=1.0,
        ),
        AllocatableObjective(
            objective_id="b",
            weight=1.0,
            base_score=0.5,
            improvement_cap=0.3,
            efficiency=1.0,
        ),
    )
    plan = allocate(objectives, 4)
    assert plan.assignments["a"] >= plan.assignments["b"]
    assert plan.assignments["a"] + plan.assignments["b"] == 4


def test_allocatable_objective_validation():
    with pytest.raises(ValueError):
        AllocatableObjective(
            objective_id="",
            weight=1.0,
            base_score=0.5,
            improvement_cap=0.3,
            efficiency=1.0,
        )
    with pytest.raises(ValueError):
        AllocatableObjective(
            objective_id="a",
            weight=0.0,
            base_score=0.5,
            improvement_cap=0.3,
            efficiency=1.0,
        )
    with pytest.raises(ValueError):
        AllocatableObjective(
            objective_id="a",
            weight=1.0,
            base_score=1.5,
            improvement_cap=0.3,
            efficiency=1.0,
        )
    with pytest.raises(ValueError):
        AllocatableObjective(
            objective_id="a",
            weight=1.0,
            base_score=0.5,
            improvement_cap=-0.1,
            efficiency=1.0,
        )
    with pytest.raises(ValueError):
        AllocatableObjective(
            objective_id="a",
            weight=1.0,
            base_score=0.5,
            improvement_cap=0.3,
            efficiency=-0.1,
        )


def test_allocate_validation():
    with pytest.raises(ValueError):
        allocate((), 3)
    with pytest.raises(ValueError):
        allocate(ALLOCATION_POOL, -1)
    with pytest.raises(ValueError):
        allocate((object(),), 3)  # type: ignore[arg-type]
