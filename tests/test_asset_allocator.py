"""Tests for the asset allocator module (asset_allocator.py).

Real deterministic math: concave improvement curves, diminishing marginal
gains, and the greedy (submodular) allocation with deterministic tie-breaking.
No mocks.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterator

import pytest

from never_say_never_again.asset_allocator import (
    ALLOCATION_BUDGET,
    ALLOCATION_CURVES,
    ALLOCATION_POOL,
    AllocatableObjective,
    AllocationPlan,
    allocate,
    build_allocation_pool,
    canonical_allocation,
    improvement_curve,
    marginal_gain,
)
from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    ObjectiveSpec,
    RemountConfig,
    ReplayEngine,
    Scenario,
)

TOL = 1e-9


def _weighted_total(
    pool: tuple[AllocatableObjective, ...], assignment: dict[str, int]
) -> float:
    """Weighted score of an arbitrary assignment (independent of ``allocate``)."""
    return sum(
        objective.weight
        * min(
            1.0,
            objective.base_score
            + improvement_curve(
                assignment[objective.objective_id],
                objective.improvement_cap,
                objective.efficiency,
            ),
        )
        for objective in pool
    )


def _compositions(total: int, parts: int) -> Iterator[tuple[int, ...]]:
    """Every way to split ``total`` identical assets across ``parts`` objectives."""
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _compositions(total - first, parts - 1):
            yield (first, *rest)


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


def test_realized_marginal_gains_are_non_increasing():
    """The submodularity claim the manuscript leans on, over the real plan.

    03_results.md states the greedy's realized gain sequence is non-increasing
    — the property that licenses the (1 - 1/e) guarantee. Assert it on the
    canonical plan rather than only on a single objective's curve.
    """
    plan = canonical_allocation()
    gains = plan.marginal_gains
    assert len(gains) == ALLOCATION_BUDGET
    assert all(later <= earlier + TOL for earlier, later in itertools.pairwise(gains))
    assert all(gain > 0.0 for gain in gains)


def test_greedy_is_at_least_a_naive_uniform_spread_on_the_canonical_pool():
    """A non-crippled comparator: uniform allocation is a legitimate baseline.

    Honest limitation: on the *current* canonical pool the greedy and the
    uniform spread land on the same assignment, so this test is a floor, not a
    discriminator. The discriminating gates are
    ``test_greedy_allocation_is_exactly_optimal_by_exhaustive_search`` and its
    negative control below.
    """
    plan = canonical_allocation()

    per_objective, remainder = divmod(ALLOCATION_BUDGET, len(ALLOCATION_POOL))
    uniform = {
        objective.objective_id: per_objective + (1 if idx < remainder else 0)
        for idx, objective in enumerate(ALLOCATION_POOL)
    }

    assert sum(uniform.values()) == sum(plan.assignments.values())
    assert plan.total_weighted_score >= _weighted_total(ALLOCATION_POOL, uniform) - TOL


def test_greedy_allocation_is_exactly_optimal_by_exhaustive_search():
    """The optimality claim, checked against every feasible allocation.

    The methodology claims more than the ``(1 - 1/e)`` submodular bound: for a
    weighted sum of per-objective concave curves, greedy incremental allocation
    is exactly optimal. That is checked here by enumerating all splits of the
    budget across the pool — no appeal to the citation.
    """
    plan = canonical_allocation()
    ids = tuple(objective.objective_id for objective in ALLOCATION_POOL)

    candidates = [
        _weighted_total(ALLOCATION_POOL, dict(zip(ids, composition, strict=True)))
        for composition in _compositions(ALLOCATION_BUDGET, len(ids))
    ]
    assert len(candidates) == math.comb(
        ALLOCATION_BUDGET + len(ids) - 1, len(ids) - 1
    )  # the whole feasible set, not a sample

    assert plan.total_weighted_score == pytest.approx(max(candidates))


def _greedy_on_unweighted_marginal(
    pool: tuple[AllocatableObjective, ...], budget: int
) -> dict[str, int]:
    """The rejected variant: select on the raw (unweighted) capped marginal."""
    assignment = {objective.objective_id: 0 for objective in pool}
    for _ in range(budget):
        best, best_gain = None, -1.0
        for objective in pool:
            assigned = assignment[objective.objective_id]
            gain = min(
                1.0,
                objective.base_score
                + improvement_curve(
                    assigned + 1, objective.improvement_cap, objective.efficiency
                ),
            ) - min(
                1.0,
                objective.base_score
                + improvement_curve(
                    assigned, objective.improvement_cap, objective.efficiency
                ),
            )
            if gain > best_gain:
                best, best_gain = objective, gain
        if best is None or best_gain <= 0.0:
            break
        assignment[best.objective_id] += 1
    return assignment


def test_unweighted_selection_fails_the_optimality_gate():
    """Negative control: the optimality gate above is not green by construction.

    Selecting on the unweighted marginal gain is the plausible wrong
    implementation (and the one this module actually shipped once). It produces
    a different, strictly worse allocation — so the gate discriminates.
    """
    plan = canonical_allocation()
    rejected = _greedy_on_unweighted_marginal(ALLOCATION_POOL, ALLOCATION_BUDGET)

    assert rejected != plan.assignments
    assert sum(rejected.values()) == ALLOCATION_BUDGET
    assert _weighted_total(ALLOCATION_POOL, rejected) < plan.total_weighted_score - TOL


def test_pool_ids_and_weights_are_derived_from_the_scenario():
    """The pool is not a second declaration of the objective set."""
    assert tuple(objective.objective_id for objective in ALLOCATION_POOL) == tuple(
        spec.objective_id for spec in LEGACY_SCENARIO.objectives
    )
    for objective, spec in zip(
        ALLOCATION_POOL, LEGACY_SCENARIO.objectives, strict=True
    ):
        assert objective.weight == spec.weight


def test_pool_base_scores_are_the_remount_replay_scores():
    """Allocation gains are in weighted-command-score units — bound, not asserted.

    The results section says the greedy recovers a quantity of *weighted command
    score*. That is only true if the pool's zero-asset baseline is the remount's
    command score. Both premises are pinned here: the weights sum to one (so the
    weighted sum the plan reports is the weighted mean the engine reports), and
    each base score is the objective's real remount replay score.
    """
    remount = ReplayEngine().replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    scores = {outcome.objective_id: outcome.score for outcome in remount.outcomes}

    assert sum(spec.weight for spec in LEGACY_SCENARIO.objectives) == pytest.approx(1.0)
    for objective in ALLOCATION_POOL:
        assert objective.base_score == pytest.approx(scores[objective.objective_id])

    plan = canonical_allocation()
    baseline = plan.total_weighted_score - plan.total_gain
    assert baseline == pytest.approx(remount.command_score)


def test_build_allocation_pool_rejects_an_objective_with_no_curve():
    """An objective added to the scenario without a curve fails loudly."""
    scenario = Scenario(
        name="EXTRA",
        objectives=(
            *LEGACY_SCENARIO.objectives,
            ObjectiveSpec(
                objective_id="unlisted_objective",
                weight=0.10,
                difficulty=0.5,
                baseline_intel=0.5,
            ),
        ),
    )
    with pytest.raises(ValueError, match="unlisted_objective"):
        build_allocation_pool(scenario)


def test_build_allocation_pool_tracks_the_config_it_is_given():
    """A different replay config moves the base scores — the pool is derived."""
    engine = ReplayEngine()
    identity_config = RemountConfig(intel_bonus=0.0)
    identity_pool = build_allocation_pool(
        LEGACY_SCENARIO, identity_config, engine=engine
    )
    identity = engine.replay(LEGACY_SCENARIO, identity_config)
    identity_scores = {o.objective_id: o.score for o in identity.outcomes}
    for objective in identity_pool:
        assert objective.base_score == pytest.approx(
            identity_scores[objective.objective_id]
        )
    # The remount pool is strictly better off than the un-reinforced one.
    for reinforced, plain in zip(ALLOCATION_POOL, identity_pool, strict=True):
        assert reinforced.base_score > plain.base_score
    # Curves are unaffected by the config.
    for objective in identity_pool:
        cap, efficiency = ALLOCATION_CURVES[objective.objective_id]
        assert (objective.improvement_cap, objective.efficiency) == (cap, efficiency)


def test_non_finite_inputs_are_rejected():
    """NaN / infinity in allocation parameters must not propagate.

    Regression for the guard class: `_require_non_negative` and the weight
    check accepted NaN because NaN compares False against `0.0`; a NaN cap or
    efficiency then produced NaN curves and a NaN-gain allocation plan.
    """
    non_finite = (float("nan"), float("inf"), float("-inf"))
    for bad in non_finite:
        with pytest.raises(ValueError, match="finite"):
            improvement_curve(2, bad, 1.0)
        with pytest.raises(ValueError, match="finite"):
            improvement_curve(2, 1.0, bad)
        with pytest.raises(ValueError, match="finite"):
            AllocatableObjective(
                objective_id="x",
                weight=bad,
                base_score=0.5,
                improvement_cap=0.1,
                efficiency=1.0,
            )
        with pytest.raises(ValueError, match="finite"):
            AllocatableObjective(
                objective_id="x",
                weight=1.0,
                base_score=0.5,
                improvement_cap=0.1,
                efficiency=bad,
            )
