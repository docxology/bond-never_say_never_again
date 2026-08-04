#!/usr/bin/env python3
"""Thin orchestrator: print the REMOUNT mission plan (phase: plan).

Usage:
    uv run python scripts/plan.py
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
    plan = provider.plan(provider.brief())
    print(f"Plan steps ({len(plan.steps)}):")
    for step in plan.steps:
        print(f"  - {step.action} :: {step.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
