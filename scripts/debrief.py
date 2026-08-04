#!/usr/bin/env python3
"""Thin orchestrator: run the REMOUNT debrief (phase: debrief).

Usage:
    uv run python scripts/debrief.py
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
    outcome = provider.execute(provider.plan(provider.brief()))
    debrief = provider.debrief(outcome)
    print(f"Outcome success: {outcome.success}")
    print(f"Lessons ({len(debrief.lessons)}):")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
