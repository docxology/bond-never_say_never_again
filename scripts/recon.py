#!/usr/bin/env python3
"""Thin orchestrator: run REMOUNT reconnaissance (phase: recon).

Usage:
    uv run python scripts/recon.py [GOAL]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bond_api.protocol import ReconRequest

from never_say_never_again.mission import MissionProvider


def main() -> int:
    goal = "survey legacy assets and remount constraints"
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
    provider = MissionProvider()
    report = provider.recon(ReconRequest(goal=goal))
    print(f"Recon findings ({len(report.findings)}):")
    for finding in report.findings:
        print(f"  - [{finding.label}] {finding.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
