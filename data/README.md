# data/ — the claim ledger

This directory holds one file: [`claim_ledger.yaml`](claim_ledger.yaml), a registry of the sourced
numeric claims the package makes. Each entry carries an `id`, the `statement` in words, the `source`
expression that computes it, the `token` that carries it into the manuscript, and a `determinism` flag
that says the value is reproducible rather than measured once.

## What is verified, and what is not

The tokens are real. `src/never_say_never_again/manuscript_variables.py` generates them from the
deterministic domain core, and the manuscript embeds them — `{{ORIGINAL_COMMAND_SCORE}}`,
`{{MIGRATED_ASSET_COUNT}}` and the rest are computed, not typed.

What is **not** verified is the ledger itself. Measured on 2026-11-03 at `f2b1940`: nothing else in
the repository names `claim_ledger.yaml` — no module, test, script or document reads it, and a search
by that filename inside and outside the package returns the file's own header only. The value of an
edit here is therefore documentary: it changes what a reader can trace, not what any gate decides.

Its header states the purpose it was written for: "for evidence-registry validation". That consumer is
not bound yet, which makes this file the integration point the root guide's rule covers — when a
dependency is needed but not yet bound, declare it rather than stall. Until then, treat the ledger as
the record of where each claim comes from, and treat `docs/_generated/COUNTS.md` and the manuscript as
the places where a current figure actually lives.

## What is not here

No datasets, no fixtures, no output. The canonical scenario lives in the domain core
(`src/never_say_never_again/mission_replay.py` and the modules that derive from it), generated
artifacts are written under the ignored `output/`, and live counts are regenerated into
[`docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md). Package-wide rules are in
[the root guide](../AGENTS.md); the layer contract is in
[`docs/architecture.md`](../docs/architecture.md).
