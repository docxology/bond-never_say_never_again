# data/ — agent guidance

The reader's view is [README.md](README.md); the package-wide rules are in [the root guide](../AGENTS.md);
the operational detail is [`docs/agent_instructions.md`](../docs/agent_instructions.md) and
[`docs/style_guide.md`](../docs/style_guide.md).

## The file here

`claim_ledger.yaml` registers sourced claims: `id`, `statement`, `source`, `token`, `determinism`.
Keep those five in agreement:

- the `source` expression must be a real path into the deterministic core, not a paraphrase of one;
- the `token` must be one `manuscript_variables.py` actually generates — token hydration and its
  cross-reference are covered by `tests/test_manuscript_variables.py`;
- `determinism: true` is a claim about byte-identical regeneration, and
  `tests/test_regeneration_determinism.py` is what makes it true rather than aspirational;
- a claim added here without a computation behind it is the exact defect the manuscript protocol
  exists to prevent.

## The thing to know before editing

**Nothing in this repository reads this file** (measured 2026-11-03 at `f2b1940`: no module, test,
script or document names it; the only match is the file's own header). So a ledger edit cannot make a
failing test pass, and cannot make a passing test meaningful either. It exists for an
evidence-registry consumer that is not bound yet — the root guide's rule for that situation is to
declare the integration point rather than leave it implicit. Write the ledger for the reader who will
trace a number back, and do not mistake it for a gate.

## What does not belong here

Test counts and coverage percentages: those are regenerated into
[`docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md), and the root guide's layer contract says
plainly not to hardcode them in prose. Datasets and scenario inputs belong in the domain core; produced
artifacts belong under the ignored `output/`.
