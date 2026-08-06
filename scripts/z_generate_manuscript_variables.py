#!/usr/bin/env python3
"""Thin orchestrator: hydrate manuscript {{TOKEN}}s and render REMOUNT figures.

Usage:
    uv run python scripts/z_generate_manuscript_variables.py [--allow-draft]

Strict by default: unresolved {{TOKEN}}s in a numbered prose section fail the
run. ``--allow-draft`` writes the resolved tree anyway (intentional early
drafts only). Writes ``output/data/manuscript_variables.json``, the resolved
tree under ``output/manuscript/``, and five deterministic figures under
``output/figures/``: ``op_diff_scores.png``, ``learning_curve.png``,
``asset_allocation.png``, ``asset_distribution.png``, and ``sensitivity_sweep.png``.

``--output-root`` redirects the whole artifact set elsewhere. It exists so
``tests/test_regeneration_determinism.py`` can regenerate twice into two clean
roots and compare bytes, which is how the manuscript's byte-level
reproducibility claim is enforced rather than merely stated.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from never_say_never_again.asset_allocator import canonical_allocation
from never_say_never_again.figures import (
    render_allocation_figure,
    render_asset_distribution_figure,
    render_learning_curve_figure,
    render_op_diff_figure,
    render_sensitivity_figure,
)
from never_say_never_again.learning_curve import (
    canonical_learning_forecast,
)
from never_say_never_again.legacy_assets import canonical_catalog
from never_say_never_again.manuscript_variables import (
    generate_variables,
    resolve_manuscript_tree,
)
from never_say_never_again.sensitivity import sensitivity_summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="write even if tokens remain unresolved",
    )
    parser.add_argument("--config", default=None, help="path to manuscript/config.yaml")
    parser.add_argument(
        "--output-root",
        default=None,
        help="artifact root (default: <project>/output)",
    )
    args = parser.parse_args()

    variables = generate_variables(config_path=args.config)
    output_root = Path(args.output_root) if args.output_root else ROOT / "output"

    variables_path = output_root / "data" / "manuscript_variables.json"
    variables_path.parent.mkdir(parents=True, exist_ok=True)
    variables_path.write_text(
        json.dumps(variables, sort_keys=True, indent=2), encoding="utf-8"
    )

    resolve_manuscript_tree(
        variables,
        output_dir=output_root / "manuscript",
        strict=not args.allow_draft,
    )

    render_op_diff_figure(path=output_root / "figures" / "op_diff_scores.png")
    render_learning_curve_figure(
        canonical_learning_forecast(),
        path=output_root / "figures" / "learning_curve.png",
    )
    render_allocation_figure(
        canonical_allocation(), path=output_root / "figures" / "asset_allocation.png"
    )
    render_asset_distribution_figure(
        canonical_catalog().counts_by_kind(),
        path=output_root / "figures" / "asset_distribution.png",
    )
    render_sensitivity_figure(
        sensitivity_summary(), path=output_root / "figures" / "sensitivity_sweep.png"
    )

    print(f"Resolved {len(variables)} manuscript variables -> {variables_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
