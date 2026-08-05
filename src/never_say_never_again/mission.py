"""REMOUNT — the `Never Say Never Again` BOND film MissionProvider.

Implements the FROZEN ``bond_api`` mission protocol on top of the pure REMOUNT
domain core. Discovery contract: this is ``<slug>/mission.py`` exposing a
top-level ``MissionProvider`` class that satisfies the protocol and declares
``film = "never_say_never_again"``.

The provider replays the canonical legacy scenario (THUNDERBALL-65) as a
remount, diffs the original vs remount outcomes, migrates the legacy
intelligence assets, assesses the remount's detection risk and mission
reliability, allocates the scarce remastered assets by marginal gain, and
forecasts the replay learning curve — all deterministically. Gadgets (the
engine, the scenario, the remount config, and the three deepened reports) are
registered with a :class:`bond_api.GadgetRegistry` so orchestrators and tooling
can reach the film's working objects.

Public shape is stable across fleet consumers: ``GADGET_REGISTRY`` (module
level), ``film``, and the five protocol methods are unchanged; only the mission
internals deepen.
"""

from __future__ import annotations

import hashlib
import unicodedata

from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry

from never_say_never_again import __version__
from never_say_never_again.asset_allocator import (
    ALLOCATION_BUDGET,
    ALLOCATION_POOL,
    AllocationPlan,
    canonical_allocation,
)
from never_say_never_again.learning_curve import (
    LEARNING_ITERATIONS,
    LEARNING_RATE,
    LEARNING_TARGET_SCORE,
    LearningReplayForecast,
    canonical_learning_forecast,
)
from never_say_never_again.legacy_assets import (
    LEGACY_INDEX,
    MigrationBatch,
    canonical_catalog,
)
from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    MISSION_SEED,
    REMOUNT_CONFIG,
    RemountConfig,
    ReplayEngine,
)
from never_say_never_again.op_diff import diff_outcomes
from never_say_never_again.remount_risk import (
    DETECTION_RATE,
    REPLAY_CAMPAIGN_LENGTH,
    RemountRiskReport,
    canonical_risk_report,
)

__all__ = ["GADGET_REGISTRY", "MissionProvider"]

#: The film's gadget registry. Orchestrators reach the film's working objects
#: here (the replay engine, the canonical scenario, the remount config, and
#: the deepened risk/allocation/learning reports).
GADGET_REGISTRY = GadgetRegistry()

#: Deterministic seed recorded in provenance. Sourced from the pure core so the
#: mission, the manuscript tokens, and ``manuscript/config.yaml`` cannot drift
#: apart (the drift is asserted in ``tests/test_manuscript_variables.py``).
#: This mission performs no random draws, so the seed is provenance-only.
_SEED = MISSION_SEED

#: Identity config (no remount deltas) used as the original/legacy reference.
_IDENTITY_CONFIG = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)

#: Typed module-level references to the deepened canonical reports. The
#: provider methods use these directly (never reaching through the gadget
#: registry's opaque payloads), and they double as the gadget payloads.
_RISK_REPORT: RemountRiskReport = canonical_risk_report()
_ALLOCATION_PLAN: AllocationPlan = canonical_allocation()
_LEARNING_FORECAST: LearningReplayForecast = canonical_learning_forecast()


def _mission_input_hash(brief: MissionBrief) -> str:
    """Stable SHA-256 fingerprint of a mission brief (for provenance)."""
    payload = "|".join(
        [
            brief.film,
            brief.codename,
            ",".join(brief.objectives),
            ",".join(a.name for a in brief.assets),
        ]
    )
    normalized = unicodedata.normalize("NFC", payload)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class MissionProvider:
    """Deterministic REMOUNT mission provider implementing the BOND-API contract."""

    film = "never_say_never_again"

    def __init__(self) -> None:
        self._engine = ReplayEngine()
        # Register the film's working gadgets once per provider.
        GADGET_REGISTRY.register(
            self.film,
            {
                "engine": self._engine,
                "legacy_scenario": LEGACY_SCENARIO,
                "remount_config": REMOUNT_CONFIG,
                "remount_risk_report": _RISK_REPORT,
                "allocation_plan": _ALLOCATION_PLAN,
                "learning_forecast": _LEARNING_FORECAST,
            },
        )

    @property
    def engine(self) -> ReplayEngine:
        """The deterministic replay engine this provider drives."""
        return self._engine

    def brief(self) -> MissionBrief:
        """Declare the REMOUNT mission: replay, diff, migrate, risk, allocate, learn."""
        return MissionBrief(
            film=self.film,
            codename="REMOUNT",
            objectives=(
                "replay the legacy operation as a remount",
                "diff the original vs remount outcomes",
                "migrate the legacy intelligence assets",
                "assess remount detection risk and mission reliability",
                "allocate remastered assets by marginal gain",
                "forecast the replay learning curve",
            ),
            assets=(
                Asset(
                    kind="scenario",
                    name="legacy",
                    payload={"scenario": LEGACY_SCENARIO.name},
                ),
                Asset(
                    kind="config",
                    name="remount",
                    payload={"intel_bonus": REMOUNT_CONFIG.intel_bonus},
                ),
                Asset(
                    kind="model",
                    name="risk",
                    payload={
                        "detection_rate": DETECTION_RATE,
                        "replays": REPLAY_CAMPAIGN_LENGTH,
                    },
                ),
            ),
            constraints=(
                Constraint(
                    kind="determinism",
                    detail="fixed seed, no random draws, no external calls",
                ),
                Constraint(kind="purity", detail="domain core has no bond_api imports"),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request, scenario, assets, risk, and determinism constraints."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="scenario",
                    detail=f"{LEGACY_SCENARIO.name} with {len(LEGACY_SCENARIO.objectives)} objectives",
                ),
                Finding(
                    label="assets",
                    detail=f"{len(LEGACY_INDEX)} legacy intel dossiers queued for migration",
                ),
                Finding(
                    label="risk",
                    detail=f"detection hazard {DETECTION_RATE}/replay over {REPLAY_CAMPAIGN_LENGTH} replays",
                ),
                Finding(
                    label="allocation",
                    detail=f"{ALLOCATION_BUDGET} remastered assets across {len(ALLOCATION_POOL)} objectives",
                ),
                Finding(
                    label="learning",
                    detail=f"learning rate {LEARNING_RATE} over {LEARNING_ITERATIONS} iterations to target {LEARNING_TARGET_SCORE}",
                ),
                Finding(label="constraints", detail="deterministic execution required"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the seven deterministic steps: replay, diff, migrate, risk, allocate, learn, verify."""
        return MissionPlan(
            steps=(
                Step(
                    name="replay",
                    action="run_remount",
                    params={"objectives": len(LEGACY_SCENARIO.objectives)},
                ),
                Step(name="diff", action="compare_outcomes", params={"overall": True}),
                Step(
                    name="migrate",
                    action="remaster_assets",
                    params={"records": len(LEGACY_INDEX)},
                ),
                Step(
                    name="assess_risk",
                    action="escalation_hazard",
                    params={"rate": DETECTION_RATE, "replays": REPLAY_CAMPAIGN_LENGTH},
                ),
                Step(
                    name="allocate",
                    action="marginal_gain",
                    params={"budget": ALLOCATION_BUDGET},
                ),
                Step(
                    name="forecast",
                    action="learning_curve",
                    params={"iterations": LEARNING_ITERATIONS},
                ),
                Step(name="verify", action="check_integrity", params={"success": True}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the replay → diff → migrate → risk → allocate → learn pipeline."""
        original = self._engine.replay(LEGACY_SCENARIO, _IDENTITY_CONFIG)
        remount = self._engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
        op_diff = diff_outcomes(original, remount)

        catalog = canonical_catalog()
        new_contents = {
            asset.id: asset.content + f" [remastered v{asset.version + 1}]"
            for asset in catalog.assets
        }
        batch: MigrationBatch = catalog.migrate(new_contents)

        risk = _RISK_REPORT
        allocation = _ALLOCATION_PLAN
        learning = _LEARNING_FORECAST

        best_objective = max(
            allocation.assignments,
            key=lambda objective_id: (
                allocation.assignments[objective_id],
                objective_id,
            ),
        )
        success = (
            op_diff.weighted_delta >= 0.0
            and batch.verified
            and risk.campaign_ev >= 0.0
            and learning.delta >= 0.0
        )

        results = {
            "steps_completed": len(plan.steps),
            "objectives": tuple(o.objective_id for o in remount.outcomes),
            "original_command_score": original.command_score,
            "remount_command_score": remount.command_score,
            "command_delta": op_diff.weighted_delta,
            "overall_verdict": op_diff.overall,
            "num_improved": op_diff.improved,
            "num_regressed": op_diff.regressed,
            "num_unchanged": op_diff.unchanged,
            "migrated_assets": len(batch.assets),
            "migration_verified": batch.verified,
            "asset_fingerprint": catalog.stable_integrity(),
            "risk_detection_probability": risk.detection_probability,
            "risk_expected_operations": risk.expected_operations,
            "mission_reliability": risk.reliability,
            "campaign_ev": risk.campaign_ev,
            "allocated_assets": sum(allocation.assignments.values()),
            "allocation_gain_ratio": allocation.gain_ratio,
            "allocation_total_gain": allocation.total_gain,
            "allocation_best_objective": best_objective,
            "learning_final_score": learning.final_score,
            "learning_delta": learning.delta,
            "learning_target_iteration": learning.target_iteration,
        }

        return MissionOutcome(
            success=success,
            results=results,
            provenance=Provenance(
                package_version=__version__,
                seed=_SEED,
                input_hash=_mission_input_hash(self.brief()),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission and record the remount's standing lessons."""
        return Debrief(
            outcome=outcome,
            lessons=(
                "a remount improves outcome when intel reinforcement outpaces difficulty",
                "op diffs must weight objectives by their relative importance",
                "legacy assets must be re-fingerprinted before remount consumption",
                "replay detection hazard accumulates — keep the remount campaign short",
                "scarce remastered assets should follow marginal gain, not intuition",
                "replay learning follows a diminishing-returns curve toward an asymptote",
            ),
        )
