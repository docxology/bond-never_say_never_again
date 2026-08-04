# Style guide — REMOUNT

- **Formatter**: `ruff format` (88-column default), matching the BOND suite.
- **Type hints**: every public function is annotated; docstrings with
  `Args:` / `Returns:` and examples where useful.
- **Validation**: domain `__post_init__` checks raise `ValueError` with
  actionable messages (matching `bond-api`'s `_require` helpers); a separate
  `AssetIntegrityError(ValueError)` is used for integrity failures.
- **Imports**: standard library, third-party, then local, sorted by ruff.
- **Naming**: descriptive; `N801` class-name overrides on `MissionProvider`
  are documented (fixed by the discovery contract).
- **Lineage**: never write the literal scaffold string `template[_]code_project`
  (bracket-split in docs);
