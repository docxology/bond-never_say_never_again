"""Manuscript variable hydration for the REMOUNT manuscript.

Every ``{{TOKEN}}`` in ``manuscript/NN_*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
live REMOUNT domain surface. Metrics are never hand-authored in prose: they
flow through this module so the manuscript cannot drift from the code.

The consuming orchestrator is ``scripts/z_generate_manuscript_variables.py``
(thin wrapper); the live cross-reference gate lives in
``tests/test_manuscript_variables.py``.
"""

from __future__ import annotations

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from never_say_never_again import __version__
from never_say_never_again.asset_allocator import canonical_allocation
from never_say_never_again.learning_curve import canonical_learning_forecast
from never_say_never_again.legacy_assets import compute_integrity
from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    ReplayEngine,
)
from never_say_never_again.op_diff import diff_outcomes
from never_say_never_again.remount_risk import canonical_risk_report

__all__ = ["generate_variables", "load_manuscript_config", "resolve_manuscript_tree"]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

#: Canonical deterministic mission tokens derived from the domain surface.
FILM_IDENTITY = "Never Say Never Again"
MISSION_CODENAME = "REMOUNT"


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(
            f"manuscript config must be a top-level mapping, got {type(data).__name__}"
        )
    return data


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), verify the domain surface is
            non-empty — the strict-mode gate that replaces the exemplar's
            analysis-CSV requirement.
    """
    from never_say_never_again.mission_replay import RemountConfig

    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")

    identity_config = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)
    engine = ReplayEngine()
    if require_outputs and not LEGACY_SCENARIO.objectives:
        raise ValueError("REMOUNT domain surface is empty — no objectives to replay")

    original = engine.replay(LEGACY_SCENARIO, identity_config)
    remount = engine.replay(LEGACY_SCENARIO, REMOUNT_CONFIG)
    op_diff = diff_outcomes(original, remount)

    # Deepened canonical reports — same single-source factories as mission.py.
    risk = canonical_risk_report()
    allocation = canonical_allocation()
    learning = canonical_learning_forecast(engine)

    # Deterministic asset registry for the migration summary.
    asset_payload = "".join(
        f"{o.objective_id}:{o.baseline_intel:.4f}" for o in LEGACY_SCENARIO.objectives
    )
    asset_fingerprint = compute_integrity(asset_payload)[:12]

    return {
        "FILM_IDENTITY": FILM_IDENTITY,
        "MISSION_CODENAME": MISSION_CODENAME,
        "PACKAGE_VERSION": __version__,
        "PAPER_TITLE": str(paper.get("title", "")),
        "PAPER_SUBTITLE": str(paper.get("subtitle", "")),
        "NUM_OBJECTIVES": str(len(LEGACY_SCENARIO.objectives)),
        "ORIGINAL_COMMAND_SCORE": f"{original.command_score:.4f}",
        "REMOUNT_COMMAND_SCORE": f"{remount.command_score:.4f}",
        "COMMAND_DELTA": f"{op_diff.weighted_delta:+.4f}",
        "OVERALL_VERDICT": op_diff.overall,
        "NUM_IMPROVED": str(op_diff.improved),
        "NUM_REGRESSED": str(op_diff.regressed),
        "NUM_UNCHANGED": str(op_diff.unchanged),
        "MIGRATED_ASSET_COUNT": str(len(LEGACY_SCENARIO.objectives)),
        "ASSET_FINGERPRINT": asset_fingerprint,
        "RISK_DETECTION_PROBABILITY": f"{risk.detection_probability:.4f}",
        "RISK_EXPECTED_OPERATIONS": f"{risk.expected_operations:.2f}",
        "RISK_RELIABILITY": f"{risk.reliability:.4f}",
        "RISK_CAMPAIGN_EV": f"{risk.campaign_ev:+.2f}",
        "ALLOC_ASSETS_USED": str(sum(allocation.assignments.values())),
        "ALLOC_GAIN_RATIO": f"{allocation.gain_ratio:.4f}",
        "ALLOC_TOTAL_GAIN": f"{allocation.total_gain:+.4f}",
        "LEARN_ITERATIONS": str(learning.iterations),
        "LEARN_FINAL_SCORE": f"{learning.final_score:.4f}",
        "LEARN_DELTA": f"{learning.delta:+.4f}",
        "LEARN_TARGET_ITERATION": str(learning.target_iteration or "unreached"),
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ),
    }


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each manuscript section to ``output/manuscript/``, substituting tokens.

    Only ``NN_*.md`` section files are copied (not sidecars such as
    ``SYNTAX.md``). In strict mode any leftover ``{{TOKEN}}`` fails resolution
    so the manuscript can never render with raw braces.

    Returns the output directory and the sorted list of resolved file names.
    """
    manuscript_dir = (
        Path(manuscript_dir)
        if manuscript_dir is not None
        else PACKAGE_ROOT / "manuscript"
    )
    output_dir = (
        Path(output_dir)
        if output_dir is not None
        else PACKAGE_ROOT / "output" / "manuscript"
    )
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(
                f"unresolved manuscript tokens in {source.name}: {unresolved}"
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved
