#!/usr/bin/env python3
"""Thin orchestrator: execute the REMOUNT mission (phase: execute).

Runs the replay → diff → migrate pipeline and persists the deterministic
outcome to ``output/data/remount_outcome.json``.

Usage:
    uv run python scripts/execute.py [--out PATH]
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

from never_say_never_again.mission import MissionProvider


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=None,
        help="output JSON path (default: output/data/remount_outcome.json)",
    )
    args = parser.parse_args()

    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))

    out_path = (
        Path(args.out)
        if args.out
        else ROOT / "output" / "data" / "remount_outcome.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "success": outcome.success,
                "results": outcome.results,
                "seed": outcome.provenance.seed,
                "input_hash": outcome.provenance.input_hash,
            },
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Success: {outcome.success}")
    print(f"Verdict: {outcome.results['overall_verdict']}")
    print(
        f"Command score: original={outcome.results['original_command_score']:.4f} "
        f"remount={outcome.results['remount_command_score']:.4f}"
    )
    print(f"Wrote outcome -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
