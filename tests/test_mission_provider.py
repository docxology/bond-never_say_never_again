"""Tests for the REMOUNT MissionProvider against the FROZEN bond_api protocol.

Covers the five-stage mission lifecycle, gadget registration, slug discovery,
determinism, and the pure-domain (no bond_api) isolation gate. Real computation
only — no mocks.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from bond_api.discovery import load_provider
from bond_api.protocol import (
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    run_mission,
)
from bond_api.protocol import (
    MissionProvider as Protocol,
)

from never_say_never_again.asset_allocator import (
    ALLOCATION_BUDGET,
    canonical_allocation,
)
from never_say_never_again.mission import GADGET_REGISTRY, MissionProvider
from never_say_never_again.mission_replay import LEGACY_SCENARIO, REMOUNT_CONFIG

SRC = Path(__file__).resolve().parents[1] / "src"


def test_provider_satisfies_protocol():
    provider = MissionProvider()
    assert provider.film == "never_say_never_again"
    assert isinstance(provider, Protocol)

    brief = provider.brief()
    assert isinstance(brief, MissionBrief)
    assert brief.codename == "REMOUNT"
    assert brief.objectives


def test_recon_returns_findings():
    provider = MissionProvider()
    report = provider.recon(ReconRequest(goal="survey the theater"))
    assert isinstance(report, ReconReport)
    assert report.findings
    assert any(f.label == "goal" for f in report.findings)


def test_plan_returns_steps():
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    assert isinstance(plan, MissionPlan)
    assert len(plan.steps) == 7
    assert [s.action for s in plan.steps] == [
        "run_remount",
        "compare_outcomes",
        "remaster_assets",
        "escalation_hazard",
        "marginal_gain",
        "learning_curve",
        "check_integrity",
    ]


def test_execute_is_deterministic_and_successful():
    provider = MissionProvider()
    outcome_a = provider.execute(provider.plan(provider.brief()))
    outcome_b = provider.execute(provider.plan(provider.brief()))
    assert isinstance(outcome_a, MissionOutcome)
    assert outcome_a.success is True
    assert outcome_a.results["overall_verdict"] == "improved"
    assert outcome_a.results["migrated_assets"] == 3
    assert outcome_a.results["migration_verified"] is True
    assert outcome_a.results == outcome_b.results
    assert outcome_a.provenance == outcome_b.provenance
    assert isinstance(outcome_a.provenance, Provenance)
    assert outcome_a.provenance.seed == 13
    assert len(outcome_a.provenance.input_hash) == 64
    assert outcome_a.provenance.wall_time_s == 0.0


def test_execute_reports_deepened_results():
    provider = MissionProvider()
    outcomes = provider.execute(provider.plan(provider.brief()))
    results = outcomes.results
    # Risk model (canonical: detection ~0.7769, reliability ~0.9578, EV ~18.1).
    assert 0.7 < results["risk_detection_probability"] < 0.9
    assert results["risk_expected_operations"] == pytest.approx(4.0)
    assert 0.9 < results["mission_reliability"] < 1.0
    assert results["campaign_ev"] > 0.0
    # Allocation. Bind to the canonical plan rather than to frozen literals, so
    # a change in the allocation policy is caught as a *disagreement between
    # the mission and the model*, not as a stale magic string in a test.
    plan = canonical_allocation()
    assert results["allocated_assets"] == sum(plan.assignments.values())
    assert results["allocated_assets"] <= ALLOCATION_BUDGET
    assert results["allocation_gain_ratio"] == pytest.approx(plan.gain_ratio)
    assert results["allocation_total_gain"] == pytest.approx(plan.total_gain)
    assert 0.0 < results["allocation_gain_ratio"] <= 1.0
    assert results["allocation_total_gain"] > 0.0
    # The reported "best" objective is the one holding the most assets, with
    # ids breaking ties — recompute it rather than asserting a literal.
    expected_best = max(plan.assignments, key=lambda oid: (plan.assignments[oid], oid))
    assert results["allocation_best_objective"] == expected_best
    # Learning curve (canonical: target iteration 3, positive delta).
    assert results["learning_final_score"] > 0.6
    assert results["learning_delta"] > 0.0
    assert results["learning_target_iteration"] == 3


def test_debrief_records_lessons():
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    debrief = provider.debrief(outcome)
    assert len(debrief.lessons) == 6
    assert any("remount improves outcome" in lesson for lesson in debrief.lessons)
    assert any("detection hazard" in lesson for lesson in debrief.lessons)
    assert any("marginal gain" in lesson for lesson in debrief.lessons)
    assert any("learning follows" in lesson for lesson in debrief.lessons)


def test_run_mission_full_flow():
    provider = MissionProvider()
    debrief = run_mission(provider, ReconRequest(goal="run the mission"))
    assert debrief.outcome.success is True
    assert len(debrief.lessons) >= 1


def test_gadget_registry_registration():
    provider = MissionProvider()
    assert GADGET_REGISTRY.contains(provider.film, "engine")
    assert GADGET_REGISTRY.contains(provider.film, "legacy_scenario")
    assert GADGET_REGISTRY.contains(provider.film, "remount_config")
    assert GADGET_REGISTRY.contains(provider.film, "remount_risk_report")
    assert GADGET_REGISTRY.contains(provider.film, "allocation_plan")
    assert GADGET_REGISTRY.contains(provider.film, "learning_forecast")
    engine = GADGET_REGISTRY.lookup(provider.film, "engine")
    assert isinstance(engine, object)  # opaque gadget payload


def test_discovery_loads_provider_by_slug():
    provider = load_provider("never_say_never_again", search_paths=[SRC])
    assert provider.film == "never_say_never_again"
    assert isinstance(provider, Protocol)


def test_domain_core_has_no_bond_api_imports():
    """The pure domain modules must remain importable without bond-api."""
    modules = [
        "never_say_never_again.mission_replay",
        "never_say_never_again.op_diff",
        "never_say_never_again.legacy_assets",
        "never_say_never_again.remount_risk",
        "never_say_never_again.asset_allocator",
        "never_say_never_again.learning_curve",
    ]
    for module_name in modules:
        module_path = Path(SRC) / (module_name.replace(".", "/") + ".py")
        text = module_path.read_text(encoding="utf-8")
        assert "bond_api" not in text, f"{module_name} must not import bond_api"


def test_purity_domain_core_pyc_importable_standalone():
    """Import the pure domain modules outside the mission adapter."""
    import never_say_never_again.asset_allocator
    import never_say_never_again.learning_curve
    import never_say_never_again.legacy_assets
    import never_say_never_again.mission_replay
    import never_say_never_again.op_diff
    import never_say_never_again.remount_risk  # noqa: F401


def test_engine_property_is_the_registered_gadget():
    """The public `engine` accessor and the "engine" gadget are one object.

    Two published routes to the replay engine exist — the provider property and
    the gadget registry. If they ever returned different engines, a consumer
    tuning one would silently not affect the other.
    """
    provider = MissionProvider()
    assert provider.engine is GADGET_REGISTRY.lookup(provider.film, "engine")
    # And it is a working engine, not just an identity match.
    assert provider.engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG).command_score > 0.0
