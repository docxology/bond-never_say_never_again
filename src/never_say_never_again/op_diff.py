"""Op diff — original vs remount outcome comparison for REMOUNT.

REMOUNT's second concept is *op diff*: after the legacy mission is replayed as
a remount, the two outcomes are compared per objective and in aggregate. The
diff is fully deterministic:

* :class:`ObjectiveDiff` — per-objective original/remount scores, signed delta
  and a verdict (``improved`` / ``regressed`` / ``unchanged``).
* :func:`diff_outcomes` — align two :class:`~.mission_replay.ReplayResult`s by
  objective id and produce the aggregate :class:`OpDiff`.
* :class:`OpDiff` — per-objective diffs plus mean delta, weight-weighted delta
  and an overall verdict.

The module is pure (stdlib only).
"""

from __future__ import annotations

from dataclasses import dataclass

from never_say_never_again.mission_replay import ReplayResult

__all__ = ["OBJECTIVE_DIFF_ORDER", "ObjectiveDiff", "OpDiff", "diff_outcomes"]

#: Canonical verdict ordering used for stable reports.
OBJECTIVE_DIFF_ORDER = ("improved", "regressed", "unchanged")


@dataclass(frozen=True)
class ObjectiveDiff:
    """Per-objective comparison of an original vs a remount outcome.

    Attributes:
        objective_id: The objective being compared.
        original_score: Score achieved by the original (legacy) operation.
        remount_score: Score achieved by the remount.
        delta: ``remount_score - original_score``.
        verdict: ``improved`` when ``delta > epsilon``, ``regressed`` when
            ``delta < -epsilon``, else ``unchanged``.
    """

    objective_id: str
    original_score: float
    remount_score: float
    delta: float
    verdict: str


def _verdict(delta: float, epsilon: float) -> str:
    if delta > epsilon:
        return "improved"
    if delta < -epsilon:
        return "regressed"
    return "unchanged"


@dataclass(frozen=True)
class OpDiff:
    """Aggregate comparison of an original operation against its remount.

    Attributes:
        diffs: Per-objective diffs, in the original scenario's order.
        mean_delta: Arithmetic mean of per-objective deltas.
        weighted_delta: Weight-weighted mean of per-objective deltas (uses the
            original scenario's objective weights).
        improved: Count of improved objectives.
        regressed: Count of regressed objectives.
        unchanged: Count of unchanged objectives.
        overall: Overall verdict derived from ``weighted_delta``.
    """

    diffs: tuple[ObjectiveDiff, ...]
    mean_delta: float
    weighted_delta: float
    improved: int
    regressed: int
    unchanged: int
    overall: str


def diff_outcomes(
    original: ReplayResult,
    remount: ReplayResult,
    *,
    epsilon: float = 1e-9,
) -> OpDiff:
    """Compare the original and remount replays into an :class:`OpDiff`.

    Objectives are aligned by id, in the *original* result's order. Scores for
    the remount are looked up by id; the aggregate weight uses the original
    scenario's objective weights. Objectives present on only one side are
    ignored for the per-objective diff but reported via the ``diff`` ordering.
    """
    if not isinstance(original, ReplayResult) or not isinstance(remount, ReplayResult):
        raise ValueError("diff_outcomes requires two ReplayResult instances")

    remount_by_id = {outcome.objective_id: outcome for outcome in remount.outcomes}

    diffs: list[ObjectiveDiff] = []
    improved = 0
    regressed = 0
    unchanged = 0
    weight_map = {spec.objective_id: spec.weight for spec in _objective_specs(original)}
    delta_sum = 0.0
    weighted_sum = 0.0
    weight_total = 0.0

    for outcome in original.outcomes:
        other = remount_by_id.get(outcome.objective_id)
        if other is None:
            continue
        delta = other.score - outcome.score
        verdict = _verdict(delta, epsilon)
        diffs.append(
            ObjectiveDiff(
                objective_id=outcome.objective_id,
                original_score=outcome.score,
                remount_score=other.score,
                delta=delta,
                verdict=verdict,
            )
        )
        if verdict == "improved":
            improved += 1
        elif verdict == "regressed":
            regressed += 1
        else:
            unchanged += 1
        delta_sum += delta
        weight = weight_map.get(outcome.objective_id, 1.0)
        weight_total += weight
        weighted_sum += weight * delta

    n = len(diffs)
    mean_delta = delta_sum / n if n else 0.0
    weighted_delta = weighted_sum / weight_total if weight_total > 0.0 else 0.0
    return OpDiff(
        diffs=tuple(diffs),
        mean_delta=mean_delta,
        weighted_delta=weighted_delta,
        improved=improved,
        regressed=regressed,
        unchanged=unchanged,
        overall=_verdict(weighted_delta, epsilon),
    )


def _objective_specs(result: ReplayResult):
    """Reconstruct the original objective weights from a replay result.

    We read weights back from the canonical scenario injected by the engine via
    the scenario name lookup — a lightweight registry so ``diff_outcomes`` does
    not need the scenario object itself. Falls back to unity weight per
    objective when the scenario is unknown.
    """
    # The engine records command_score from the scenario's own weights; for the
    # aggregate diff we rebuild weights from the canonical scenario constants.
    from never_say_never_again.mission_replay import LEGACY_SCENARIO

    if result.scenario == LEGACY_SCENARIO.name:
        return list(LEGACY_SCENARIO.objectives)
    # Unknown scenario: infer unity weights so diffs stay well-defined.
    return [
        _UnityObjective(objective_id=outcome.objective_id)
        for outcome in result.outcomes
    ]


class _UnityObjective:
    """Minimal weight carrier for objectives from unknown/unregistered scenarios."""

    def __init__(self, objective_id: str, weight: float = 1.0) -> None:
        self.objective_id = objective_id
        self.weight = weight
