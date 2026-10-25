# Standalone note — REMOUNT

This package is a standalone BOND film package (codename REMOUNT). It:

- Lives in its own checkout — `docxology/Private/bond-never_say_never_again`
  under the GitVault tree, originally `projects/working/bond/never_say_never_again/`
  inside the PROJECT BOND monorepo. Its canonical upstream is the GitHub
  repository `docxology/bond-never_say_never_again`, branch `main`.
- Depends on the sibling `bond-api` package via a relative path in
  `pyproject.toml` (`[tool.uv.sources] bond-api = { path = "../bond-api" }`),
  i.e. a `bond-api` checkout next to this package. If that path is
  unavailable, the pure domain core (`mission_replay.py`, `op_diff.py`,
  `legacy_assets.py`) still imports standalone — only `mission.py` (the
  protocol adapter) needs `bond_api`.
- Ships no vendored infrastructure; the domain core is stdlib-only.
