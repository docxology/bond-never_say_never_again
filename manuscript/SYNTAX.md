# Manuscript syntax guide — REMOUNT

This guide documents the citation and cross-reference syntax used by Pandoc
when rendering this manuscript. It is a reference sidecar, NOT a rendered
section, so the literal token placeholders it illustrates are excluded from the
strict cross-reference gate.

## Manuscript variables

The manuscript is hydrated from `manuscript/config.yaml` plus the live domain
surface via `scripts/z_generate_manuscript_variables.py`. Use the
`{{TOKEN}}`-substitution form (e.g. `{{ORIGINAL_COMMAND_SCORE}}`) for any
number that must stay in lockstep with the code. Strict generation fails if any
token remains unresolved in a numbered prose section (`[0-9][0-9]_*.md`).

The generated tokens are:

- `FILM_IDENTITY`, `MISSION_CODENAME`, `PACKAGE_VERSION`,
  `PAPER_TITLE`, `PAPER_SUBTITLE`
- `NUM_OBJECTIVES`, `ORIGINAL_COMMAND_SCORE`, `REMOUNT_COMMAND_SCORE`,
  `COMMAND_DELTA`, `OVERALL_VERDICT`
- `NUM_IMPROVED`, `NUM_REGRESSED`, `NUM_UNCHANGED`
- `MIGRATED_ASSET_COUNT`, `ASSET_FINGERPRINT`
- `RISK_DETECTION_PROBABILITY`, `RISK_EXPECTED_OPERATIONS`,
  `RISK_RELIABILITY`, `RISK_CAMPAIGN_EV`
- `ALLOC_ASSETS_USED`, `ALLOC_GAIN_RATIO`, `ALLOC_TOTAL_GAIN`
- `LEARN_ITERATIONS`, `LEARN_FINAL_SCORE`, `LEARN_DELTA`,
  `LEARN_TARGET_ITERATION`
- `PYTHON_VERSION`, `MANUSCRIPT_DATE`

`MANUSCRIPT_DATE` is `paper.date` from `manuscript/config.yaml` — a committed
value, not a wall-clock read. No token may be derived from the clock: the
manuscript claims byte-level reproducibility, and
`tests/test_regeneration_determinism.py` enforces it by regenerating twice.

## Citations

Use Pandoc-style citations `[@key]` referencing `manuscript/references.bib`.

## Figures

Reference figures by their rendered path, e.g.
`![Op diff — original vs remount](figures/op_diff_scores.png)`.

## Rules

- Never hand-author a computed metric in prose; inject it as a `{{TOKEN}}`.
- Keep literal `{{...}}` placeholders out of numbered prose sections; this
  guide and the AGENTS/README sidecars may illustrate them.
