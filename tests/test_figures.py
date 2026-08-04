"""Tests for REMOUNT figure rendering (figures.py).

Figures must render deterministically (byte-identical on re-render) to
``output/figures/``. Uses tmp_path for isolation; real computation.
"""

from __future__ import annotations

from pathlib import Path

from never_say_never_again.figures import (
    render_asset_distribution_figure,
    render_op_diff_figure,
)
from never_say_never_again.legacy_assets import AssetCatalog, LegacyAsset


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
