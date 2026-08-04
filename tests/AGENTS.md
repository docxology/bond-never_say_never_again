# tests/ — REMOUNT

Real-data, computation-only tests. **No mock framework.** Every test uses the
deterministic domain core with fixed inputs, so outcomes are byte-identical by
construction.

| Test file | Covers |
| --- | --- |
| `test_mission_replay.py` | Scenario replay: determinism, remount improvement, saturation, symmetry, validation |
| `test_op_diff.py` | Original vs remount: verdicts, no-change, regression, unmatched objectives, weighting |
| `test_legacy_assets.py` | Fingerprinting, tamper detection, remaster, catalog, migration batch |
| `test_mission_provider.py` | Protocol conformance, discovery, gadget registry, determinism, purity gates |
| `test_figures.py` | Deterministic figure rendering |
| `test_manuscript_variables.py` | Token hydration + live cross-reference gate over numbered prose |
| `test_scripts_smoke.py` | Subprocess smoke of every thin CLI (exit 0 + artifact assertions) |

`conftest.py` pins `MPLBACKEND=Agg` and adds `src/` to `sys.path`. The
`test_manuscript_variables.py` gate scans `manuscript/[0-9][0-9]_*.md` only.
