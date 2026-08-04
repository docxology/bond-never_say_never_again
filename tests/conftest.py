"""Shared pytest fixtures for the REMOUNT test suite.

This project uses real data + computation only — no mock framework. The
conftest adds ``src/`` to ``sys.path`` (so project modules import under plain
pytest) and pins the matplotlib backend to Agg (no display windows).
Deterministic seeding is unnecessary here: the domain core makes no random
draws, so every test outcome is byte-identical by construction.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
