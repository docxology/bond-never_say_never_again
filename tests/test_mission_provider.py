"""Tests for the REMOUNT MissionProvider against the FROZEN bond_api protocol.

Covers the five-stage mission lifecycle, gadget registration, slug discovery,
determinism, and the pure-domain (no bond_api) isolation gate. Real computation
only — no mocks.
"""

from __future__ import annotations

from pathlib import Path

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

from never_say_never_again.mission import GADGET_REGISTRY, MissionProvider

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
    assert len(plan.steps) == 4
    assert [s.action for s in plan.steps] == [
        "run_remount",
        "compare_outcomes",
        "remaster_assets",
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


def test_debrief_records_lessons():
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    debrief = provider.debrief(outcome)
    assert len(debrief.lessons) == 3
    assert any("remount improves outcome" in lesson for lesson in debrief.lessons)


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
    ]
    for module_name in modules:
        module_path = Path(SRC) / (module_name.replace(".", "/") + ".py")
        text = module_path.read_text(encoding="utf-8")
        assert "bond_api" not in text, f"{module_name} must not import bond_api"


def test_purity_domain_core_pyc_importable_standalone():
    """Import the three domain modules outside the mission adapter."""
    import never_say_never_again.legacy_assets
    import never_say_never_again.mission_replay
    import never_say_never_again.op_diff  # noqa: F401
