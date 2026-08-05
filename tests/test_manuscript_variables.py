"""Tests for manuscript variable hydration (manuscript_variables.py).

The core gate: every ``{{TOKEN}}`` used in numbered prose sections
(``manuscript/[0-9][0-9]_*.md``) must resolve through
:func:`generate_variables`, and the resolved tree must be brace-clean in
strict mode. Real config + real domain computation, no mocks.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from never_say_never_again.manuscript_variables import (
    PACKAGE_ROOT,
    generate_variables,
    load_manuscript_config,
    resolve_manuscript_tree,
)

_TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def test_generate_variables_returns_expected_tokens():
    variables = generate_variables(require_outputs=True)
    for token in (
        "FILM_IDENTITY",
        "MISSION_CODENAME",
        "PACKAGE_VERSION",
        "PAPER_TITLE",
        "ORIGINAL_COMMAND_SCORE",
        "REMOUNT_COMMAND_SCORE",
        "COMMAND_DELTA",
        "OVERALL_VERDICT",
        "NUM_OBJECTIVES",
        "MIGRATED_ASSET_COUNT",
        "ASSET_FINGERPRINT",
        "RISK_DETECTION_PROBABILITY",
        "RISK_EXPECTED_OPERATIONS",
        "RISK_RELIABILITY",
        "RISK_CAMPAIGN_EV",
        "ALLOC_ASSETS_USED",
        "ALLOC_GAIN_RATIO",
        "ALLOC_TOTAL_GAIN",
        "LEARN_ITERATIONS",
        "LEARN_FINAL_SCORE",
        "LEARN_DELTA",
        "LEARN_TARGET_ITERATION",
    ):
        assert token in variables, f"missing token {token}"
    assert variables["FILM_IDENTITY"] == "Never Say Never Again"
    assert variables["MISSION_CODENAME"] == "REMOUNT"
    assert variables["OVERALL_VERDICT"] == "improved"
    # Deepened tokens reflect the canonical deterministic reports.
    assert float(variables["RISK_DETECTION_PROBABILITY"]) > 0.7
    assert float(variables["RISK_CAMPAIGN_EV"]) > 0.0
    assert float(variables["ALLOC_GAIN_RATIO"]) > 0.5
    assert variables["LEARN_TARGET_ITERATION"] == "3"


def test_load_manuscript_config_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_manuscript_config(tmp_path / "nope.yaml")


def test_generate_variables_fails_on_empty_surface(tmp_path: Path):
    # A config whose 'paper' section is malformed should surface as an error.
    bad = tmp_path / "config.yaml"
    bad.write_text("paper:\n  - not\n  - a\n  - mapping\n", encoding="utf-8")
    with pytest.raises(ValueError):
        generate_variables(config_path=bad)


def test_resolve_manuscript_tree_is_brace_clean(tmp_path: Path):
    variables = generate_variables()
    output_dir = tmp_path / "resolved"
    resolved_dir, names = resolve_manuscript_tree(variables, output_dir=output_dir)
    assert names
    for name in names:
        text = (resolved_dir / name).read_text(encoding="utf-8")
        assert "{{" not in text, f"leftover token brace in {name}"


def test_resolve_strict_raises_on_unknown_token(tmp_path: Path):
    # Point at a synthetic manuscript dir with an unresolved token.
    ms_dir = tmp_path / "ms"
    ms_dir.mkdir()
    (ms_dir / "00_abstract.md").write_text(
        "value {{UNKNOWN_TOKEN}} here", encoding="utf-8"
    )
    with pytest.raises(ValueError):
        resolve_manuscript_tree(
            {"KNOWN": "x"}, manuscript_dir=ms_dir, output_dir=tmp_path / "out"
        )


def test_every_prose_token_resolves_from_live_manuscript():
    """The live cross-reference gate: every {{TOKEN}} in numbered prose
    sections must exist in generate_variables()."""
    variables = generate_variables()
    manuscript_dir = PACKAGE_ROOT / "manuscript"
    for section in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = section.read_text(encoding="utf-8")
        tokens = set(_TOKEN_RE.findall(text))
        for token in tokens:
            assert token in variables, (
                f"manuscript token {token!r} in {section.name} has no generated value"
            )


def assert_config_mirrors_the_code_constants(config: dict[str, object]) -> None:
    """The config-mirror gate itself, runnable against *any* loaded config.

    `manuscript/config.yaml` documents the parameters; the code constants are
    the source. Without this gate the mirror could drift silently and the setup
    section would describe a model nobody runs. Each assertion names the
    constant it binds to, so a mismatch says exactly which pair diverged.

    This is a function rather than a test body so the negative control below can
    run the *same* checks against a deliberately drifted config and prove they
    fail. (The previous negative control asserted only that a YAML round-trip
    preserved a value it had just changed — it never invoked the gate, so it
    established nothing about the gate.)
    """
    from never_say_never_again.asset_allocator import ALLOCATION_BUDGET, ALLOCATION_POOL
    from never_say_never_again.learning_curve import (
        LEARNING_BONUS_CAP,
        LEARNING_ITERATIONS,
        LEARNING_RATE,
        LEARNING_TARGET_SCORE,
    )
    from never_say_never_again.legacy_assets import LEGACY_INDEX
    from never_say_never_again.mission_replay import (
        DEFAULT_SENSITIVITY,
        DEFAULT_SUCCESS_THRESHOLD,
        LEGACY_SCENARIO,
        MISSION_SEED,
        REMOUNT_CONFIG,
    )
    from never_say_never_again.remount_risk import (
        CAMPAIGN_PENALTY,
        CAMPAIGN_REWARD,
        DETECTION_RATE,
        REPLAY_CAMPAIGN_LENGTH,
    )

    block = config["remount"]
    assert isinstance(block, dict)

    assert block["scenario"] == LEGACY_SCENARIO.name
    assert block["objectives"] == len(LEGACY_SCENARIO.objectives)
    assert block["legacy_assets"] == len(LEGACY_INDEX)
    assert block["sensitivity"] == pytest.approx(DEFAULT_SENSITIVITY)
    assert block["success_threshold"] == pytest.approx(DEFAULT_SUCCESS_THRESHOLD)
    assert block["seed"] == MISSION_SEED

    assert block["config"]["intel_bonus"] == pytest.approx(REMOUNT_CONFIG.intel_bonus)
    assert block["config"]["doctrine"] == pytest.approx(REMOUNT_CONFIG.doctrine)
    assert block["config"]["realism_ceiling"] == pytest.approx(
        REMOUNT_CONFIG.realism_ceiling
    )

    assert block["risk"]["detection_rate"] == pytest.approx(DETECTION_RATE)
    assert block["risk"]["replay_campaign_length"] == REPLAY_CAMPAIGN_LENGTH
    assert block["risk"]["campaign_reward"] == pytest.approx(CAMPAIGN_REWARD)
    assert block["risk"]["campaign_penalty"] == pytest.approx(CAMPAIGN_PENALTY)

    assert block["allocation"]["budget"] == ALLOCATION_BUDGET
    assert len(ALLOCATION_POOL) == len(LEGACY_SCENARIO.objectives)

    assert block["learning"]["rate"] == pytest.approx(LEARNING_RATE)
    assert block["learning"]["iterations"] == LEARNING_ITERATIONS
    assert block["learning"]["bonus_cap"] == pytest.approx(LEARNING_BONUS_CAP)
    assert block["learning"]["target_score"] == pytest.approx(LEARNING_TARGET_SCORE)


def test_config_yaml_mirrors_the_code_constants():
    """The live config must pass the mirror gate."""
    assert_config_mirrors_the_code_constants(load_manuscript_config())


#: (path into the ``remount:`` block, sentinel value) pairs. Every drifted
#: field must be caught by the gate.
_DRIFT_CASES = [
    (("seed",), 999),
    (("objectives",), 99),
    (("legacy_assets",), 99),
    (("scenario",), "NOT-THE-SCENARIO"),
    (("sensitivity",), 99.0),
    (("config", "intel_bonus"), 0.99),
    (("risk", "detection_rate"), 0.99),
    (("risk", "replay_campaign_length"), 999),
    (("allocation", "budget"), 999),
    (("learning", "rate"), 0.99),
    (("learning", "target_score"), 0.99),
]


@pytest.mark.parametrize(("path", "sentinel"), _DRIFT_CASES)
def test_config_mirror_gate_actually_fails_on_drift(
    tmp_path: Path, path: tuple[str, ...], sentinel: object
):
    """Negative control: the mirror gate is not green by construction.

    For each mirrored field, a config carrying a value that disagrees with the
    code must make the *gate itself* fail. The gate is invoked here, not
    approximated.
    """
    import yaml

    config = load_manuscript_config()
    block = config["remount"]
    for key in path[:-1]:
        block = block[key]
    assert block[path[-1]] != sentinel, "drift sentinel must differ from the real value"
    block[path[-1]] = sentinel

    drifted_path = tmp_path / "drifted.yaml"
    drifted_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    reloaded = load_manuscript_config(drifted_path)

    # Positive control: the undrifted config still passes, so the failure below
    # is caused by the drift and not by the gate rejecting everything.
    assert_config_mirrors_the_code_constants(load_manuscript_config())
    with pytest.raises(AssertionError):
        assert_config_mirrors_the_code_constants(reloaded)


def test_load_manuscript_config_rejects_non_mapping(tmp_path: Path):
    """A YAML list (not a mapping) at top level must raise, not be accepted."""
    bad = tmp_path / "list.yaml"
    bad.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ValueError, match="top-level mapping"):
        load_manuscript_config(bad)


def test_require_outputs_guard_rejects_an_empty_domain_surface(monkeypatch):
    """`require_outputs=True` must fail on an empty scenario, and pass otherwise.

    No mock framework: this replaces the module-level canonical scenario with a
    real ``Scenario``-shaped value carrying no objectives, via monkeypatch (an
    environment substitution, not a dependency mock), then restores it.
    """
    from never_say_never_again import manuscript_variables as mv

    class _EmptyScenario:
        name = "EMPTY"
        objectives: tuple[object, ...] = ()

    monkeypatch.setattr(mv, "LEGACY_SCENARIO", _EmptyScenario)
    with pytest.raises(ValueError, match="domain surface is empty"):
        mv.generate_variables(require_outputs=True)


def test_seed_token_matches_the_mission_provenance():
    """MISSION_SEED in the manuscript is the seed the mission actually records."""
    from never_say_never_again.mission import MissionProvider

    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    assert generate_variables()["MISSION_SEED"] == str(outcome.provenance.seed)


def test_fulfilled_tokens_match_a_live_replay():
    """The results table's fulfilled counts are bound to real replay output."""
    from never_say_never_again.mission_replay import (
        LEGACY_SCENARIO,
        REMOUNT_CONFIG,
        RemountConfig,
        ReplayEngine,
    )

    engine = ReplayEngine()
    original = engine.replay(LEGACY_SCENARIO, RemountConfig(intel_bonus=0.0))
    remount = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    variables = generate_variables()

    assert variables["ORIGINAL_FULFILLED"] == str(original.objectives_fulfilled)
    assert variables["REMOUNT_FULFILLED"] == str(remount.objectives_fulfilled)
    delta = remount.objectives_fulfilled - original.objectives_fulfilled
    assert variables["FULFILLED_DELTA"] == f"{delta:+d}"


def test_no_bare_metric_numerals_in_results_prose():
    """Results prose must not hand-author metrics — they must arrive as tokens.

    Scans the results section for decimal numerals outside code spans, image
    paths, and token braces. A hand-typed score like ``0.5161`` would trip this;
    a ``{{TOKEN}}`` would not.
    """
    text = (PACKAGE_ROOT / "manuscript" / "03_results.md").read_text(encoding="utf-8")
    stripped = _TOKEN_RE.sub("TOKEN", text)
    stripped = re.sub(r"`[^`]*`", "CODE", stripped)
    stripped = re.sub(r"!\[[^\]]*\]\([^)]*\)", "FIGURE", stripped)
    offenders = re.findall(r"\d+\.\d+", stripped)
    assert offenders == [], f"hand-authored decimals in results prose: {offenders}"
