#!/usr/bin/env python3
"""Thin orchestrator: hydrate manuscript {{TOKEN}}s and render REMOUNT figures.

Usage:
    uv run python scripts/z_generate_manuscript_variables.py [--allow-draft]

Strict by default: unresolved {{TOKEN}}s in a numbered prose section fail the
run. ``--allow-draft`` writes the resolved tree anyway (intentional early
drafts only). Writes ``output/data/manuscript_variables.json``, the resolved
tree under ``output/manuscript/``, and two deterministic figures under
``output/figures/``.
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

from never_say_never_again.figures import (
    render_asset_distribution_figure,
    render_op_diff_figure,
)
from never_say_never_again.legacy_assets import AssetCatalog, LegacyAsset
from never_say_never_again.manuscript_variables import (
    generate_variables,
    resolve_manuscript_tree,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="write even if tokens remain unresolved",
    )
    parser.add_argument("--config", default=None, help="path to manuscript/config.yaml")
    args = parser.parse_args()

    variables = generate_variables(config_path=args.config)
    output_root = ROOT / "output"

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
    catalog = AssetCatalog(
        [
            LegacyAsset(
                id="intel-TB-01",
                kind="intel",
                classification="TOP_SECRET",
                content="fleet registry",
            ),
            LegacyAsset(
                id="gadget-TB-02",
                kind="gadget",
                classification="CONFIDENTIAL",
                content="harpoon rig",
            ),
            LegacyAsset(
                id="intel-TB-03",
                kind="intel",
                classification="SECRET",
                content="blackmail ledger",
            ),
        ]
    )
    render_asset_distribution_figure(
        catalog.counts_by_kind(),
        path=output_root / "figures" / "asset_distribution.png",
    )

    print(f"Resolved {len(variables)} manuscript variables -> {variables_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
