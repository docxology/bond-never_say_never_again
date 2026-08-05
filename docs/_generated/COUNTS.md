# COUNTS — never_say_never_again (REMOUNT)

Live measured counts, transcribed from a real `pytest --cov` run whose output
was read. Never hand-edit these figures, and never quote them without
re-measuring — see the open item in `../../TODO.md` about generating this file
mechanically.

## Test suite (phase 6 — verifier remediation)

- **Tests collected**: 140
- **Result**: 140 passed, 0 failed, 0 skipped
- **Coverage on `src/`**: **100.00 %** (line + branch), floor 90 %

Command: `uv run pytest tests/ --cov=src --cov-fail-under=90`

## Module coverage (from the gate run)

| Module | Stmts | Branch | Cover |
| --- | ---: | ---: | ---: |
| `src/never_say_never_again/asset_allocator.py` | 91 | 28 | 100.00 % |
| `src/never_say_never_again/figures.py` | 89 | 4 | 100.00 % |
| `src/never_say_never_again/learning_curve.py` | 51 | 16 | 100.00 % |
| `src/never_say_never_again/legacy_assets.py` | 107 | 26 | 100.00 % |
| `src/never_say_never_again/manuscript_variables.py` | 64 | 14 | 100.00 % |
| `src/never_say_never_again/mission.py` | 53 | 0 | 100.00 % |
| `src/never_say_never_again/mission_replay.py` | 100 | 30 | 100.00 % |
| `src/never_say_never_again/op_diff.py` | 70 | 16 | 100.00 % |
| `src/never_say_never_again/remount_risk.py` | 75 | 24 | 100.00 % |
| **TOTAL** | **700** | **158** | **100.00 %** |

## Other gates (same pass)

| Gate | Command | Result |
| --- | --- | --- |
| Lint | `uv run ruff check src/ scripts/ tests/` | All checks passed |
| Format | `uv run ruff format --check src/ scripts/ tests/` | 37 files already formatted |
| Types | `uv run mypy src/ scripts/` | Success: no issues found in 19 source files |
| Manuscript tokens | `uv run python scripts/z_generate_manuscript_variables.py` | 50 variables resolved, strict mode |

## Caveat on 100 %

Full line and branch coverage means every statement and branch in `src/` was
executed — not that every behaviour is correct. Two of the defects fixed in an
earlier pass (the allocator optimizing an unweighted objective, and the
manuscript's migrated-asset count) were inside code that was already fully
covered at 98 %. The adversarial-verification pass then found a hollow negative
control and a tautological assertion *inside this 100 % suite*: both executed
every line they touched and neither could fail. Coverage is a floor, not
evidence.
