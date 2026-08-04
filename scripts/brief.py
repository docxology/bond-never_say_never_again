#!/usr/bin/env python3
"""Thin orchestrator: print the REMOUNT mission brief (phase: brief).

Usage:
    uv run python scripts/brief.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from never_say_never_again.mission import MissionProvider


def main() -> int:
    provider = MissionProvider()
    brief = provider.brief()
    print(f"Film: {brief.film}")
    print(f"Codename: {brief.codename}")
    print("Objectives:")
    for objective in brief.objectives:
        print(f"  - {objective}")
    print(f"Assets: {len(brief.assets)}")
    print(f"Constraints: {len(brief.constraints)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
