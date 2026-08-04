#!/usr/bin/env python3
"""Thin orchestrator: run the full REMOUNT mission (brief→recon→plan→execute→debrief).

Usage:
    uv run python scripts/run_mission.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bond_api.protocol import ReconRequest, run_mission

from never_say_never_again.mission import MissionProvider


def main() -> int:
    provider = MissionProvider()
    debrief = run_mission(
        provider, ReconRequest(goal="execute the legacy remount end to end")
    )
    outcome = debrief.outcome
    print(f"Film: {provider.film} ({provider.brief().codename})")
    print(f"Success: {outcome.success}")
    print(f"Overall verdict: {outcome.results['overall_verdict']}")
    print(
        f"Command score: {outcome.results['original_command_score']:.4f} -> "
        f"{outcome.results['remount_command_score']:.4f}"
    )
    print(f"Lessons: {len(debrief.lessons)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
