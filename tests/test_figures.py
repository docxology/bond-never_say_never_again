"""Tests for REMOUNT figure rendering (figures.py).

Figures must render deterministically (byte-identical on re-render) to
``output/figures/``. Uses tmp_path for isolation; real computation.
"""

from __future__ import annotations

from pathlib import Path

from never_say_never_again.asset_allocator import canonical_allocation
from never_say_never_again.figures import (
    render_allocation_figure,
    render_asset_distribution_figure,
    render_learning_curve_figure,
    render_op_diff_figure,
    render_sensitivity_figure,
)
from never_say_never_again.learning_curve import canonical_learning_forecast
from never_say_never_again.legacy_assets import AssetCatalog, LegacyAsset
from never_say_never_again.sensitivity import sensitivity_summary


def _fixture_catalog() -> AssetCatalog:
    return AssetCatalog(
        [
            LegacyAsset(id="i1", kind="intel", classification="C", content="x"),
            LegacyAsset(id="i2", kind="intel", classification="C", content="y"),
            LegacyAsset(id="g1", kind="gadget", classification="C", content="z"),
        ]
    )


def test_render_op_diff_figure_deterministic(tmp_path: Path):
    first = render_op_diff_figure(path=tmp_path / "a.png")
    second = render_op_diff_figure(path=tmp_path / "b.png")
    assert first.is_file()
    assert second.is_file()
    assert first.stat().st_size > 0
    assert first.read_bytes() == second.read_bytes()


def test_render_op_diff_default_path_is_output_figures():
    out = render_op_diff_figure()
    assert out.exists()
    assert out.stat().st_size > 0


def test_render_asset_distribution_figure(tmp_path: Path):
    catalog = _fixture_catalog()
    out = render_asset_distribution_figure(
        catalog.counts_by_kind(), path=tmp_path / "dist.png"
    )
    assert out.is_file()
    assert out.stat().st_size > 0


def test_render_learning_curve_figure_deterministic(tmp_path: Path):
    first = render_learning_curve_figure(
        canonical_learning_forecast(), path=tmp_path / "a.png"
    )
    second = render_learning_curve_figure(
        canonical_learning_forecast(), path=tmp_path / "b.png"
    )
    assert first.is_file()
    assert second.is_file()
    assert first.stat().st_size > 0
    assert first.read_bytes() == second.read_bytes()


def test_render_learning_curve_default_path():
    out = render_learning_curve_figure(canonical_learning_forecast())
    assert out.exists()
    assert out.stat().st_size > 0


def test_render_learning_curve_unreached_target(tmp_path: Path):
    # A forecast whose target is unreached must still render (no target line).
    from never_say_never_again.learning_curve import LearningReplayForecast

    forecast = LearningReplayForecast(
        scores=(0.3, 0.31, 0.32),
        iterations=3,
        initial_score=0.3,
        final_score=0.32,
        delta=0.02,
        target_iteration=None,
    )
    out = render_learning_curve_figure(forecast, path=tmp_path / "lc.png")
    assert out.is_file()
    assert out.stat().st_size > 0


def test_render_allocation_figure_deterministic(tmp_path: Path):
    plan = canonical_allocation()
    first = render_allocation_figure(plan, path=tmp_path / "alloc_a.png")
    second = render_allocation_figure(plan, path=tmp_path / "alloc_b.png")
    assert first.is_file()
    assert second.is_file()
    assert first.stat().st_size > 0
    assert first.read_bytes() == second.read_bytes()


def test_render_sensitivity_figure_deterministic(tmp_path: Path):
    first = render_sensitivity_figure(sensitivity_summary(), path=tmp_path / "s_a.png")
    second = render_sensitivity_figure(sensitivity_summary(), path=tmp_path / "s_b.png")
    assert first.is_file()
    assert second.is_file()
    assert first.stat().st_size > 0
    assert first.read_bytes() == second.read_bytes()


def test_render_sensitivity_figure_default_path():
    out = render_sensitivity_figure()
    assert out.exists()
    assert out.stat().st_size > 0
