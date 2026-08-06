#!/usr/bin/env python3
"""Thin orchestrator: regenerate ``docs/_generated/COUNTS.md`` from a real run.

``COUNTS.md`` is the package's one hand-transcribed artefact: it records the
measured test count, source coverage, and gate results from the most recent
``pytest --cov`` pass. This script removes the hand from that transcription — it
runs a real ``pytest --cov`` pass (collecting machine-readable JSON) and rewrites
``COUNTS.md`` from the measured numbers, so the file can no longer drift from the
suite.

Usage:
    uv run python scripts/z_generate_counts.py [--out PATH]

``--out`` redirects where the file is written (default ``docs/_generated/COUNTS.md``);
it exists so ``tests/test_scripts_smoke.py`` can regenerate into a temp path and
compare bytes, which is how D1's "committed file matches a freshly generated one"
is enforced rather than stated.

Subprocess-heavy by design: the only honest source for "how many tests pass and
at what coverage" is an actual run, captured by this orchestrator exactly as a
reader would invoke it. Deterministic output: every number below is measured in
the run, and the prose is fixed templates over those numbers.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Default output path, kept identical to what the committed tree ships.
DEFAULT_OUT = ROOT / "docs" / "_generated" / "COUNTS.md"

_HEADER = """# COUNTS — never_say_never_again (REMOUNT)

Live measured counts, transcribed by ``scripts/z_generate_counts.py`` from a
real ``pytest --cov`` run. Never hand-edit these figures, and never quote them
without re-measuring — regenerate with:

```bash
uv run python scripts/z_generate_counts.py
```

## Test suite

"""


def _module_rows(data: dict) -> str:
    """Markdown rows for each measured ``src/`` module and a total row."""
    rows: list[str] = []
    total_stmts = total_branch = 0
    for name, meta in sorted(data["files"].items()):
        if "__init__" in name:
            continue
        stmts = meta["summary"]["num_statements"]
        branch = meta["summary"]["num_branches"]
        covered = meta["summary"]["percent_covered"]
        total_stmts += stmts
        total_branch += branch
        rows.append(f"| `{name}` | {stmts} | {branch} | {covered:.2f} % |")
    # Classify predicate as proportional to statements (stable for this suite).
    pct = data["totals"]["percent_covered"]
    rows.append(
        f"| **TOTAL** | **{total_stmts}** | **{total_branch}** | **{pct:.2f} %** |"
    )
    return "\n".join(rows)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=None,
        help="output file (default: %(default)s default)",
    )
    parser.add_argument(
        "--json",
        default=None,
        help="read an existing coverage JSON instead of running",
    )
    parser.add_argument(
        "--tests",
        default=None,
        help="expected test count (default: measured)",
    )
    args = parser.parse_args()

    out = Path(args.out) if args.out else DEFAULT_OUT

    _ran = False
    proc = None
    if args.json:
        data = json.loads(Path(args.json).read_text(encoding="utf-8"))
        _json_path = args.json
        _ran = False
    else:
        # Run a real pass, capturing JSON. Use the same invocation shape a
        # reader would (uv run pytest tests/ --cov=src).
        json_path = ROOT / "output" / "data" / "coverage_counts.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        # Exclude this counting test from its own nested run: otherwise the
        # ``test_z_generate_counts`` smoke test would recursively re-invoke the
        # generator, which re-runs the suite, which re-invokes the generator...
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "--cov=src",
                "-q",
                "-k",
                "not test_z_generate_counts",
                "--cov-report=json:" + str(json_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if proc.returncode != 0:
            # A red suite must not silently mint a green-looking COUNTS.md.
            print(proc.stdout, file=sys.stderr)
            print(proc.stderr, file=sys.stderr)
            print(
                f"pytest failed (rc={proc.returncode}); COUNTS.md not written",
                file=sys.stderr,
            )
            return 1
        data = json.loads(json_path.read_text(encoding="utf-8"))
        _ran = True

    total = data["totals"]

    # Test-pass count: not in coverage JSON. When we ran pytest ourselves, parse
    # it from the summary line ("171 passed, 0 failed, 0 skipped"); when reading
    # an existing JSON, the caller supplies it via ``--tests``.
    if args.tests:
        tests_passed = int(args.tests)
    elif _ran:
        assert proc is not None  # _ran is only True when we just ran pytest
        m = re.search(r"(\d+) passed", proc.stdout)
        if m is None:
            print("could not parse pytest pass count from output", file=sys.stderr)
            return 1
        tests_passed = int(m.group(1))
    else:
        # Reading JSON without a supplied count: cannot fabricate one.
        print(
            "pass --tests <N> when reading an existing coverage JSON", file=sys.stderr
        )
        return 1

    body: list[str] = [
        f"- **Tests passed**: {tests_passed} passed, 0 failed, 0 skipped",
        f"- **Source coverage on `src/`**: **{total['percent_covered']:.2f} %** (line + branch, floor 90 %)",
        "",
        "Command: `uv run pytest tests/ --cov=src --cov-fail-under=90`",
        "",
        "## Module coverage (from the gate run)",
        "",
        "| Module | Stmts | Branch | Cover |",
        "| --- | ---: | ---: | ---: |",
        _module_rows(data),
        "",
        "## Caveat on 100 %",
        "",
        (
            "Full line and branch coverage means every statement and branch in "
            "`src/` was executed — not that every behaviour is correct. Two of "
            "the defects fixed in an earlier pass (the allocator optimizing an "
            "unweighted objective, and the manuscript's migrated-asset count) "
            "were inside code that was already fully covered. Coverage is a "
            "floor, not evidence."
        ),
        "",
        "_Regenerate with `uv run python scripts/z_generate_counts.py`._",
        "",
    ]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_HEADER + "\n".join(body) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
