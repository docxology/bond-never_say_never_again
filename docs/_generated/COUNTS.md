# COUNTS — never_say_never_again (REMOUNT)

Live measured counts, transcribed by ``scripts/z_generate_counts.py`` from a
real ``pytest --cov`` run. Never hand-edit these figures, and never quote them
without re-measuring — regenerate with:

```bash
uv run python scripts/z_generate_counts.py
```

## Test suite

- **Tests passed**: 171 passed, 0 failed, 0 skipped
- **Source coverage on `src/`**: **100.00 %** (line + branch, floor 90 %)

Command: `uv run pytest tests/ --cov=src --cov-fail-under=90`

## Module coverage (from the gate run)

| Module | Stmts | Branch | Cover |
| --- | ---: | ---: | ---: |
| `src/never_say_never_again/asset_allocator.py` | 91 | 28 | 100.00 % |
| `src/never_say_never_again/figures.py` | 111 | 6 | 100.00 % |
| `src/never_say_never_again/learning_curve.py` | 60 | 18 | 100.00 % |
| `src/never_say_never_again/legacy_assets.py` | 107 | 26 | 100.00 % |
| `src/never_say_never_again/manuscript_variables.py` | 82 | 20 | 100.00 % |
| `src/never_say_never_again/mission.py` | 53 | 0 | 100.00 % |
| `src/never_say_never_again/mission_replay.py` | 100 | 30 | 100.00 % |
| `src/never_say_never_again/op_diff.py` | 73 | 18 | 100.00 % |
| `src/never_say_never_again/remount_risk.py` | 87 | 28 | 100.00 % |
| `src/never_say_never_again/sensitivity.py` | 63 | 10 | 100.00 % |
| **TOTAL** | **827** | **184** | **100.00 %** |

## Caveat on 100 %

Full line and branch coverage means every statement and branch in `src/` was executed — not that every behaviour is correct. Two of the defects fixed in an earlier pass (the allocator optimizing an unweighted objective, and the manuscript's migrated-asset count) were inside code that was already fully covered. Coverage is a floor, not evidence.

_Regenerate with `uv run python scripts/z_generate_counts.py`._

