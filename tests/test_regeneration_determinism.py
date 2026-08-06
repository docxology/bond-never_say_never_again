"""The byte-level reproducibility claim, enforced by regenerating twice.

``manuscript/06_reproducibility.md`` claims REMOUNT's persisted artifacts are
byte-identical across runs. This module is that claim's binding: it runs the
real generator — the production entry point, as a subprocess, exactly as a
reader would — twice into two clean output roots, separated by more than one
clock-second, and compares the SHA-256 of every produced file.

The gap is load-bearing. The defect this test was written against was a
``GENERATION_TIMESTAMP`` token built from ``datetime.now(timezone.utc)`` at
second granularity: without a real elapsed second, two runs could coincide
inside the same second and the breach would pass unnoticed. A test that injects
a fixed ``now`` cannot detect this class of defect at all — it asserts only that
the formatter is a function of its argument, which was never in doubt.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py"

#: Enough to cross a second boundary for a wall clock at ``timespec="seconds"``.
_CLOCK_GAP_SECONDS = 1.2


def _generate_into(output_root: Path) -> dict[str, str]:
    """Run the real generator into ``output_root``; return relpath -> sha256."""
    proc = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--output-root",
            str(output_root),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    digests = {
        str(path.relative_to(output_root)): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(output_root.rglob("*"))
        if path.is_file()
    }
    assert digests, f"generator produced no artifacts under {output_root}"
    return digests


def test_two_regenerations_are_byte_identical(tmp_path: Path):
    """Regenerating the artifact set reproduces it byte-for-byte.

    Both roots are fresh, so this compares what the generator *produces*, not
    what happens to be left over in the working tree.
    """
    first = _generate_into(tmp_path / "run1")
    time.sleep(_CLOCK_GAP_SECONDS)
    second = _generate_into(tmp_path / "run2")

    assert sorted(first) == sorted(second), "the two runs produced different files"

    drifted = sorted(name for name in first if first[name] != second[name])
    assert drifted == [], (
        "regeneration is not byte-identical; these artifacts changed between "
        f"two runs of the same commit: {drifted}"
    )

    # The claim covers the whole persisted set, so assert the set is the one
    # the manuscript names — a shrunken artifact set would make the comparison
    # above true for uninteresting reasons.
    assert "data/manuscript_variables.json" in first
    assert "manuscript/06_reproducibility.md" in first
    for figure in (
        "op_diff_scores.png",
        "learning_curve.png",
        "asset_allocation.png",
        "asset_distribution.png",
        "sensitivity_sweep.png",
    ):
        assert f"figures/{figure}" in first


def test_generated_variables_are_stable_across_a_clock_second():
    """No generated token is a function of the wall clock.

    A narrower, faster companion to the file-level test above: it isolates the
    token layer, so a clock read reintroduced into ``generate_variables`` is
    reported as a named token rather than as an opaque file digest mismatch.
    """
    from never_say_never_again.manuscript_variables import generate_variables

    first = generate_variables()
    time.sleep(_CLOCK_GAP_SECONDS)
    second = generate_variables()

    unstable = sorted(key for key in first if first[key] != second[key])
    assert unstable == [], (
        f"these manuscript tokens changed between two calls: {unstable}"
    )


def test_manuscript_date_comes_from_the_committed_config(tmp_path: Path):
    """``MANUSCRIPT_DATE`` tracks ``paper.date``, not today.

    Positive control for the two tests above: they would also pass if the date
    token were hardcoded or dropped. This proves the token is genuinely wired
    to the committed config value by changing that value and observing the
    token follow it.
    """
    import yaml

    from never_say_never_again.manuscript_variables import (
        generate_variables,
        load_manuscript_config,
    )

    config = load_manuscript_config()
    assert generate_variables()["MANUSCRIPT_DATE"] == str(config["paper"]["date"])

    config["paper"]["date"] = "1983-10-07"  # the film's UK release
    edited = tmp_path / "config.yaml"
    edited.write_text(yaml.safe_dump(config), encoding="utf-8")
    assert generate_variables(config_path=edited)["MANUSCRIPT_DATE"] == "1983-10-07"


@pytest.mark.parametrize("bad_date", ["", "   ", "not-a-date", "2026-13-01", 20260805])
def test_manuscript_date_rejects_a_non_iso_committed_value(tmp_path: Path, bad_date):
    """A malformed or missing ``paper.date`` fails loudly, never silently."""
    import yaml

    from never_say_never_again.manuscript_variables import (
        load_manuscript_config,
        manuscript_date,
    )

    config = load_manuscript_config()
    config["paper"]["date"] = bad_date
    edited = tmp_path / "config.yaml"
    edited.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="paper.date"):
        manuscript_date(load_manuscript_config(edited))


def test_manuscript_date_accepts_an_unquoted_yaml_date(tmp_path: Path):
    """PyYAML parses an unquoted ``date:`` as ``datetime.date`` — still valid."""
    from never_say_never_again.manuscript_variables import (
        load_manuscript_config,
        manuscript_date,
    )

    edited = tmp_path / "config.yaml"
    edited.write_text("paper:\n  date: 1983-10-07\n", encoding="utf-8")
    assert manuscript_date(load_manuscript_config(edited)) == "1983-10-07"


def test_manuscript_date_rejects_a_non_mapping_paper_section(tmp_path: Path):
    """A malformed ``paper:`` section is an error, not an empty date."""
    from never_say_never_again.manuscript_variables import (
        load_manuscript_config,
        manuscript_date,
    )

    edited = tmp_path / "config.yaml"
    edited.write_text("paper:\n  - not\n  - a mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="'paper' section must be a mapping"):
        manuscript_date(load_manuscript_config(edited))


def test_no_source_module_reads_the_wall_clock():
    """Lexical backstop: no ``src/`` module may call a clock function.

    This does not replace the behavioural tests above — it catches a clock read
    added on a code path the generator does not currently exercise, which the
    two-run comparison would miss.
    """
    banned = ("datetime.now(", "datetime.utcnow(", "time.time(", "time.monotonic(")
    offenders: list[str] = []
    for module in sorted((PROJECT_ROOT / "src").rglob("*.py")):
        text = module.read_text(encoding="utf-8")
        for needle in banned:
            if needle in text:
                offenders.append(f"{module.relative_to(PROJECT_ROOT)}: {needle}")
    assert offenders == [], f"wall-clock reads in the domain source: {offenders}"
