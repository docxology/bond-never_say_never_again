"""REMOUNT — the `Never Say Never Again` BOND film MissionProvider.

Implements the FROZEN ``bond_api`` mission protocol on top of the pure REMOUNT
domain core. Discovery contract: this is ``<slug>/mission.py`` exposing a
top-level ``MissionProvider`` class that satisfies the protocol and declares
``film = "never_say_never_again"``.

The provider replays the canonical legacy scenario (THUNDERBALL-65) as a
remount, diffs the original vs remount outcomes, and migrates the legacy
intelligence assets — all deterministically. Gadgets (the engine, the scenario
and the remount config) are registered with a :class:`bond_api.GadgetRegistry`
so orchestrators and tooling can reach the film's working objects.
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
from never_say_never_again.legacy_assets import (
    AssetCatalog,
    LegacyAsset,
    MigrationBatch,
)
from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    RemountConfig,
    ReplayEngine,
)
from never_say_never_again.op_diff import diff_outcomes

__all__ = ["GADGET_REGISTRY", "MissionProvider"]

#: The film's gadget registry. Orchestrators reach the film's working objects
#: here (the replay engine, the canonical scenario, the remount config).
GADGET_REGISTRY = GadgetRegistry()

#: Deterministic RNG seed for the mission (0 disables randomness entirely —
#: this mission performs no random draws, so the seed is provenance-only).
_SEED = 13

#: Identity config (no remount deltas) used as the original/legacy reference.
_IDENTITY_CONFIG = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)

#: Canonical legacy intel dossiers carried forward by the migration.
_LEGACY_INDEX = (
    LegacyAsset(
        id="intel-TB-01",
        kind="intel",
        classification="TOP_SECRET",
        content="Largo fleet registry; two warheads tracked to Palmyra.",
        version=1,
    ),
    LegacyAsset(
        id="gadget-TB-02",
        kind="gadget",
        classification="CONFIDENTIAL",
        content="Cigar-case harpoon rig; flutter valve timer.",
        version=1,
    ),
    LegacyAsset(
        id="intel-TB-03",
        kind="intel",
        classification="SECRET",
        content="Largo's blackmail ledger; funding chain via Spectre.",
        version=1,
    ),
)


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
            },
        )

    @property
    def engine(self) -> ReplayEngine:
        """The deterministic replay engine this provider drives."""
        return self._engine

    def brief(self) -> MissionBrief:
        """Declare the REMOUNT mission: legacy replay, op diff, asset migration."""
        return MissionBrief(
            film=self.film,
            codename="REMOUNT",
            objectives=(
                "replay the legacy operation as a remount",
                "diff the original vs remount outcomes",
                "migrate the legacy intelligence assets",
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
        """Survey the request, the canonical scenario, and the determinism constraint."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="scenario",
                    detail=f"{LEGACY_SCENARIO.name} with {len(LEGACY_SCENARIO.objectives)} objectives",
                ),
                Finding(
                    label="assets",
                    detail=f"{len(_LEGACY_INDEX)} legacy intel dossiers queued for migration",
                ),
                Finding(label="constraints", detail="deterministic execution required"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the four deterministic steps: replay, diff, migrate, verify."""
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
                    params={"records": len(_LEGACY_INDEX)},
                ),
                Step(name="verify", action="check_integrity", params={"success": True}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the replay → diff → migrate pipeline and return a deterministic outcome."""
        original = self._engine.replay(LEGACY_SCENARIO, _IDENTITY_CONFIG)
        remount = self._engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
        op_diff = diff_outcomes(original, remount)

        catalog = AssetCatalog(list(_LEGACY_INDEX))
        new_contents = {
            asset.id: asset.content + f" [remastered v{asset.version + 1}]"
            for asset in catalog.assets
        }
        batch: MigrationBatch = catalog.migrate(new_contents)

        success = op_diff.weighted_delta >= 0.0 and batch.verified

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
            ),
        )
