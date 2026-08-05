# Style guide — REMOUNT

- **Formatter**: `ruff format` (88-column default), matching the BOND suite.
- **Type hints**: every public function is annotated; docstrings with
  `Args:` / `Returns:` and examples where useful.
- **Validation**: domain `__post_init__` checks raise `ValueError` with
  actionable messages (matching `bond-api`'s `_require` helpers); a separate
  `AssetIntegrityError(ValueError)` is used for integrity failures.
- **Imports**: standard library, third-party, then local, sorted by ruff.
- **Naming**: descriptive; `N801` class-name overrides on `MissionProvider`
  are documented (fixed by the discovery contract). Canonical constants are
  `UPPER_SNAKE` at module level; private helpers take a leading underscore.
- **`__all__`**: every module declares one, sorted, listing exactly its public
  names. `__init__.py` re-exports them and keeps its own `__all__` sorted.
- **Docstrings**: module docstrings explain the *concept* and its link to the
  film, not just the API. Where a subtlety exists (a boundary case, a fixed
  defect, an accepted trade-off), say so in the docstring rather than leaving
  it for the reader to rediscover.
- **Lineage**: never write the literal scaffold string that names the exemplar
  this package was forked from. It appears in prose only where the fork lineage
  is being explained, and always bracket-split (`template[_]code_project`) so a
  repository-wide grep stays clean. Verify with:

  ```bash
  rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'
  ```
