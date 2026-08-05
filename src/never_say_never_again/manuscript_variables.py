"""Manuscript variable hydration for the REMOUNT manuscript.

Every ``{{TOKEN}}`` in ``manuscript/NN_*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
live REMOUNT domain surface. Metrics are never hand-authored in prose: they
flow through this module so the manuscript cannot drift from the code.

The consuming orchestrator is ``scripts/z_generate_manuscript_variables.py``
(thin wrapper); the live cross-reference gate lives in
``tests/test_manuscript_variables.py``.

No token in this module reads the wall clock. The document date is
``paper.date`` in ``manuscript/config.yaml`` — a committed, reviewable value —
so regenerating the manuscript is byte-identical, which is what
``manuscript/06_reproducibility.md`` claims and what
``tests/test_regeneration_determinism.py`` enforces.
"""

from __future__ import annotations

import platform
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from never_say_never_again import __version__
from never_say_never_again.asset_allocator import (
    ALLOCATION_BUDGET,
    ALLOCATION_POOL,
    canonical_allocation,
)
from never_say_never_again.learning_curve import (
    LEARNING_BONUS_CAP,
    LEARNING_RATE,
    LEARNING_TARGET_SCORE,
    canonical_learning_forecast,
)
from never_say_never_again.legacy_assets import canonical_catalog
from never_say_never_again.mission_replay import (
    DEFAULT_SENSITIVITY,
    DEFAULT_SUCCESS_THRESHOLD,
    LEGACY_SCENARIO,
    MISSION_SEED,
    REMOUNT_CONFIG,
    ReplayEngine,
)
from never_say_never_again.op_diff import diff_outcomes
from never_say_never_again.remount_risk import (
    CAMPAIGN_PENALTY,
    CAMPAIGN_REWARD,
    DETECTION_RATE,
    REMOUNT_RISK_BLOCKS,
    REPLAY_CAMPAIGN_LENGTH,
    canonical_risk_report,
)

__all__ = [
    "generate_variables",
    "load_manuscript_config",
    "manuscript_date",
    "resolve_manuscript_tree",
]

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


def manuscript_date(config: dict[str, Any]) -> str:
    """Return the committed document date (``paper.date``) as ``YYYY-MM-DD``.

    This is the manuscript's *date of record*, not a generation timestamp. It
    is read from the committed config and never from the wall clock, so two
    regenerations at the same commit produce byte-identical artifacts. A
    wall-clock stamp here would silently falsify the byte-level reproducibility
    claim in ``manuscript/06_reproducibility.md``.
    """
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")
    raw = paper.get("date")
    if isinstance(raw, date):  # PyYAML parses an unquoted date as datetime.date
        return raw.isoformat()
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(
            "manuscript config 'paper.date' must be a YYYY-MM-DD string: it is "
            "the committed document date and the manuscript reads no wall clock"
        )
    try:
        return date.fromisoformat(raw.strip()).isoformat()
    except ValueError as exc:
        raise ValueError(
            f"manuscript config 'paper.date' is not an ISO date: {raw!r}"
        ) from exc


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

    # The migration summary reads the *same* canonical catalog the mission
    # provider migrates, so MIGRATED_ASSET_COUNT and ASSET_FINGERPRINT describe
    # the real migration rather than a parallel derivation. (Before this was
    # fixed the count was taken from the scenario's objective count, which
    # over-reported the migration by one asset.)
    catalog = canonical_catalog()
    asset_fingerprint = catalog.stable_integrity()[:12]
    asset_kinds = catalog.counts_by_kind()

    return {
        "FILM_IDENTITY": FILM_IDENTITY,
        "MISSION_CODENAME": MISSION_CODENAME,
        "PACKAGE_VERSION": __version__,
        "PAPER_TITLE": str(paper.get("title", "")),
        "PAPER_SUBTITLE": str(paper.get("subtitle", "")),
        "NUM_OBJECTIVES": str(len(LEGACY_SCENARIO.objectives)),
        "SCENARIO_NAME": LEGACY_SCENARIO.name,
        "ORIGINAL_COMMAND_SCORE": f"{original.command_score:.4f}",
        "REMOUNT_COMMAND_SCORE": f"{remount.command_score:.4f}",
        "COMMAND_DELTA": f"{op_diff.weighted_delta:+.4f}",
        "OVERALL_VERDICT": op_diff.overall,
        "NUM_IMPROVED": str(op_diff.improved),
        "NUM_REGRESSED": str(op_diff.regressed),
        "NUM_UNCHANGED": str(op_diff.unchanged),
        "ORIGINAL_FULFILLED": str(original.objectives_fulfilled),
        "REMOUNT_FULFILLED": str(remount.objectives_fulfilled),
        "FULFILLED_DELTA": (
            f"{remount.objectives_fulfilled - original.objectives_fulfilled:+d}"
        ),
        "MIGRATED_ASSET_COUNT": str(len(catalog)),
        "MIGRATED_ASSET_KINDS": ", ".join(
            f"{count} {kind}" for kind, count in asset_kinds.items()
        ),
        "ASSET_FINGERPRINT": asset_fingerprint,
        # Model parameters — tokenized so the setup section cannot drift from
        # the constants the code actually runs on.
        "MODEL_SENSITIVITY": f"{DEFAULT_SENSITIVITY:g}",
        "MODEL_SUCCESS_THRESHOLD": f"{DEFAULT_SUCCESS_THRESHOLD:g}",
        "REMOUNT_INTEL_BONUS": f"{REMOUNT_CONFIG.intel_bonus:g}",
        "REMOUNT_DOCTRINE": f"{REMOUNT_CONFIG.doctrine:g}",
        "REMOUNT_REALISM_CEILING": f"{REMOUNT_CONFIG.realism_ceiling:g}",
        "MISSION_SEED": str(MISSION_SEED),
        "RISK_DETECTION_RATE": f"{DETECTION_RATE:g}",
        "RISK_CAMPAIGN_LENGTH": str(REPLAY_CAMPAIGN_LENGTH),
        "RISK_CAMPAIGN_REWARD": f"{CAMPAIGN_REWARD:g}",
        "RISK_CAMPAIGN_PENALTY": f"{CAMPAIGN_PENALTY:g}",
        "RISK_BLOCK_STRUCTURE": ", ".join(
            f"{len(block)}" for block in REMOUNT_RISK_BLOCKS
        ),
        "RISK_DETECTION_PROBABILITY": f"{risk.detection_probability:.4f}",
        "RISK_EXPECTED_OPERATIONS": f"{risk.expected_operations:.2f}",
        "RISK_RELIABILITY": f"{risk.reliability:.4f}",
        "RISK_CAMPAIGN_EV": f"{risk.campaign_ev:+.2f}",
        "ALLOC_BUDGET": str(ALLOCATION_BUDGET),
        "ALLOC_OBJECTIVE_COUNT": str(len(ALLOCATION_POOL)),
        "ALLOC_ASSETS_USED": str(sum(allocation.assignments.values())),
        "ALLOC_GAIN_RATIO": f"{allocation.gain_ratio:.4f}",
        "ALLOC_TOTAL_GAIN": f"{allocation.total_gain:+.4f}",
        "LEARN_RATE": f"{LEARNING_RATE:g}",
        "LEARN_BONUS_CAP": f"{LEARNING_BONUS_CAP:g}",
        "LEARN_TARGET_SCORE": f"{LEARNING_TARGET_SCORE:g}",
        "LEARN_ITERATIONS": str(learning.iterations),
        "LEARN_INITIAL_SCORE": f"{learning.initial_score:.4f}",
        "LEARN_FINAL_SCORE": f"{learning.final_score:.4f}",
        "LEARN_DELTA": f"{learning.delta:+.4f}",
        "LEARN_TARGET_ITERATION": (
            "unreached"
            if learning.target_iteration is None
            else str(learning.target_iteration)
        ),
        "PYTHON_VERSION": platform.python_version(),
        "MANUSCRIPT_DATE": manuscript_date(config),
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
