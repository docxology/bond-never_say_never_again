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
