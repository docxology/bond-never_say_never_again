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

from never_say_never_again.asset_allocator import AllocationPlan
from never_say_never_again.learning_curve import LearningReplayForecast
from never_say_never_again.mission_replay import (
    LEGACY_SCENARIO,
    REMOUNT_CONFIG,
    RemountConfig,
    ReplayEngine,
    Scenario,
)
from never_say_never_again.sensitivity import SensitivityResult, sensitivity_summary

__all__ = [
    "render_allocation_figure",
    "render_asset_distribution_figure",
    "render_learning_curve_figure",
    "render_op_diff_figure",
    "render_sensitivity_figure",
]

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


def render_learning_curve_figure(
    forecast: LearningReplayForecast,
    *,
    path: str | Path | None = None,
) -> Path:
    """Render the replay learning curve (command score vs replay iteration).

    Plots the forecast scores with the initial score and the target score
    marked. Writes to ``output/figures/learning_curve.png``.
    """
    iterations = list(range(1, forecast.iterations + 1))
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.plot(
        iterations, forecast.scores, marker="o", color="#1e3a8a", label="command score"
    )
    ax.axhline(
        forecast.initial_score,
        color="#7c2d12",
        linestyle="--",
        label=f"initial {forecast.initial_score:.3f}",
    )
    if forecast.target_iteration is not None:
        ax.axvline(
            forecast.target_iteration,
            color="#15803d",
            linestyle=":",
            label=f"target at iteration {forecast.target_iteration}",
        )
    ax.set_xlabel("Replay iteration")
    ax.set_ylabel("Command score")
    ax.set_ylim(0.0, 1.0)
    ax.set_title("REMOUNT — replay learning curve")
    ax.legend()
    fig.tight_layout()

    out = (
        Path(path)
        if path is not None
        else _DEFAULT_OUTPUT / "figures" / "learning_curve.png"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out


def render_allocation_figure(
    plan: AllocationPlan,
    *,
    path: str | Path | None = None,
) -> Path:
    """Render the asset allocation (assets assigned per objective).

    Bars show assigned asset counts; a dashed line marks the allocated total.
    Writes to ``output/figures/asset_allocation.png``.
    """
    objective_ids = sorted(plan.assignments)
    values = [plan.assignments[objective_id] for objective_id in objective_ids]
    positions = list(range(len(objective_ids)))
    allocated_total = sum(plan.assignments.values())
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.bar(positions, values, color="#1e3a8a")
    ax.axhline(
        allocated_total,
        color="#7c2d12",
        linestyle="--",
        label=f"allocated {allocated_total} assets",
    )
    ax.set_xticks(positions)
    ax.set_xticklabels(objective_ids, rotation=15, ha="right")
    ax.set_ylabel("Assets assigned")
    ax.set_title(
        f"REMOUNT — marginal-gain allocation (gain ratio {plan.gain_ratio:.2f})"
    )
    ax.legend()
    fig.tight_layout()

    out = (
        Path(path)
        if path is not None
        else _DEFAULT_OUTPUT / "figures" / "asset_allocation.png"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out


def render_sensitivity_figure(
    summary: dict[str, SensitivityResult] | None = None,
    *,
    path: str | Path | None = None,
) -> Path:
    """Render a 1x3 panel of each swept parameter's robust sub-range.

    Each panel draws the parameter's declared sweep axis, marks the canonical
    value, and shades the robust sub-range over which both headline
    conclusions hold. A parameter whose range spans the whole axis (learning
    rate; sensitivity) is drawn with full shading — that insensitivity is the
    result, not whitespace. Writes to ``output/figures/sensitivity_sweep.png``.
    """
    summary = summary if summary is not None else sensitivity_summary()
    order = ("sensitivity", "detection_rate", "learning_rate")
    labels = {
        "sensitivity": "Sensitivity (doc) / per-replay",
        "detection_rate": "Detection rate / replay",
        "learning_rate": "Learning rate / replay",
    }
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4), sharey=True)
    for ax, name in zip(axes, order, strict=True):
        result = summary[name]
        ax.axvspan(result.lo, result.hi, color="#bfdbfe", alpha=0.7, label="robust")
        ax.axvline(result.canonical, color="#b91c1c", linestyle="--", label="canonical")
        ax.set_xlabel(labels[name])
        ax.set_ylim(0.0, 1.0)
        ax.set_yticks([])
        ax.set_title(name.replace("_", " "))
        ax.legend(loc="lower right", fontsize=7)
    fig.suptitle("REMOUNT — robust parameter sub-ranges (both conclusions hold)")
    fig.tight_layout()

    out = (
        Path(path)
        if path is not None
        else _DEFAULT_OUTPUT / "figures" / "sensitivity_sweep.png"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out
