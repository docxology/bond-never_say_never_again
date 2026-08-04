# Standalone note — REMOUNT

This package is a standalone BOND film package (codename REMOUNT). It:

- Is **local-only**: there is no remote and nothing is pushed. It lives under
  `projects/working/bond/never_say_never_again/` inside the PROJECT BOND
  working tree.
- Depends on the sibling `bond-api` package via a local path in
  `pyproject.toml` (`[tool.uv.sources] bond-api = ...`). If that path is
  unavailable, the pure domain core (`mission_replay.py`, `op_diff.py`,
  `legacy_assets.py`) still imports standalone — only `mission.py` (the
  protocol adapter) needs `bond_api`.
- Ships no vendored infrastructure; the domain core is stdlib-only.
