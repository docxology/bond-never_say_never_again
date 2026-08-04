# Testing philosophy — REMOUNT

## Determinism replaces mocks

This suite forbids the mock framework (`MagicMock`, `mocker.patch`,
`unittest.mock`). Instead, correctness is established with **real data and real
computation** whose outcome is fixed by construction:

- The domain core makes no random draws, so replaying `LEGACY_SCENARIO` twice
  yields identical results — determinism is the test.
- Protocol conformance is asserted structurally (`isinstance(provider,
  MissionProvider)`) against the real frozen `bond_api` contract.
- `AssetCatalog` tamper detection uses a real forged `LegacyAsset` with a
  mismatched SHA-256 fingerprint.
- CLI scripts are exercised via `subprocess` with `sys.executable` and real
  artifact assertions (the `execute.py` outcome JSON, rendered figures).

## The two hard gates

1. **Coverage**: `uv run pytest tests/ --cov=src --cov-fail-under=90` — the
   suite runs well above 90% on `src/`.
2. **Manuscript cross-reference**: `tests/test_manuscript_variables.py` scans
   `manuscript/[0-9][0-9]_*.md` and asserts every `{{TOKEN}}` resolves through
   `generate_variables()`; `resolve_manuscript_tree` must leave no raw braces.

## Quality bars

- Deterministic, branch-covering tests including error paths (validation
  `ValueError`s, `AssetIntegrityError`, `KeyError`s).
- `ruff check` + `ruff format` and `mypy src/ scripts/` clean.
