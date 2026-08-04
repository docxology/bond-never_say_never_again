#!/usr/bin/env python3
"""Thin orchestrator: verify the REMOUNT environment.

Usage:
    uv run python scripts/00_preflight.py

Exits 0 when the domain core imports and the mission provider satisfies the
BOND-API protocol.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bond_api.protocol import MissionProvider as _Protocol

from never_say_never_again import __version__
from never_say_never_again.mission import MissionProvider


def main() -> int:
    print(f"never_say_never_again {__version__} — REMOUNT")
    print(f"Python {platform.python_version()} on {platform.platform()}")
    provider = MissionProvider()
    if not isinstance(provider, _Protocol):
        print(
            "ERROR: MissionProvider does not satisfy the BOND-API protocol",
            file=sys.stderr,
        )
        return 1
    print(f"Protocol surface OK: film={provider.film}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
