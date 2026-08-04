"""Figure generation for the REMOUNT mission.

Deterministic Matplotlib figures under ``output/figures/``. Rendering always
replays the canonical scenario with canonical configs, so the same inputs
produce byte-identical figures. Uses the Agg backend (no display).
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    RemountConfig,
    ReplayEngine,
    Scenario,
)

__all__ = ["render_asset_distribution_figure", "render_op_diff_figure"]

#: The identity config (no remount deltas) used as the ``original`` reference.
_IDENTITY_CONFIG = RemountConfig(intel_bonus=0.0, doctrine=1.0, realism_ceiling=1.0)

_DEFAULT_OUTPUT = Path("output")


def render_op_diff_figure(
    engine: ReplayEngine | None = None,
    *,
    scenario: Scenario | None = None,
    configs: tuple[RemountConfig, ...] | None = None,
    labels: tuple[str, ...] | None = None,
    path: str | Path | None = None,
) -> Path:
    """Render a grouped-bar figure of objective scores under each config.

    Defaults to the canonical :data:`~.mission_replay.LEGACY_SCENARIO` with the
    identity and :data:`~.mission_replay.REMOUNT_CONFIG` configs, labelled
    ``original`` and ``remount``. Writes to ``output/figures/op_diff_scores.png``.
    """
    engine = engine if engine is not None else ReplayEngine()
    scenario = scenario if scenario is not None else LEGACY_SCENARIO
    configs = configs if configs is not None else (_IDENTITY_CONFIG, REMOUNT_CONFIG)
    labels = labels if labels is not None else ("original", "remount")

    objectives = [objective.objective_id for objective in scenario.objectives]
    results = [engine.replay(scenario, config) for config in configs]

    positions = list(range(len(objectives)))
    width = 0.8 / len(configs)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for idx, config in enumerate(configs):
        scores = [
            next(
                o.score for o in results[idx].outcomes if o.objective_id == objective_id
            )
            for objective_id in objectives
        ]
        offsets = [pos + (idx - (len(configs) - 1) / 2) * width for pos in positions]
        ax.bar(
            offsets,
            scores,
            width=width,
            label=labels[idx] if idx < len(labels) else f"config-{idx}",
        )
    ax.set_xticks(positions)
    ax.set_xticklabels(objectives, rotation=15, ha="right")
    ax.set_ylabel("Objective score")
    ax.set_ylim(0.0, 1.0)
    ax.set_title(f"REMOUNT — {scenario.name} original vs remount")
    ax.legend()
    fig.tight_layout()

    out = (
        Path(path)
        if path is not None
        else _DEFAULT_OUTPUT / "figures" / "op_diff_scores.png"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out


def render_asset_distribution_figure(
    counts: dict[str, int],
    *,
    path: str | Path | None = None,
) -> Path:
    """Render a simple bar figure of asset counts per kind.

    ``counts`` is expected to come from
    :meth:`~.legacy_assets.AssetCatalog.counts_by_kind`. Writes to
    ``output/figures/asset_distribution.png``.
    """
    kinds = sorted(counts)
    values = [counts[kind] for kind in kinds]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(kinds, values, color="#1e3a8a")
    ax.set_ylabel("Asset count")
    ax.set_title("REMOUNT — migrated legacy asset distribution")
    fig.tight_layout()

    out = (
        Path(path)
        if path is not None
        else _DEFAULT_OUTPUT / "figures" / "asset_distribution.png"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out
