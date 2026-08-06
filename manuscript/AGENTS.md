# manuscript/ — agent instructions (REMOUNT)

Rules for editing the Never Say Never Again (REMOUNT) manuscript. The single
rule that matters most: **you may not type a number into prose.**

## Section set

The canonical sections, all present and all rendered in this order:

| File | Holds |
| --- | --- |
| `00_abstract.md` | The whole result in one page, tokens only |
| `01_introduction.md` | The film's remount premise and the six capabilities |
| `02_methodology.md` | Each model, its equation, and its citation |
| `03_results.md` | Measured outputs, tables, and the five figures |
| `04_conclusion.md` | What the evidence supports and what it does not |
| `05_experimental_setup.md` | The canonical dataset and every parameter |
| `06_reproducibility.md` | Determinism, provenance, verification commands |
| `07_scope_and_related_work.md` | Scope, related work, and honest limitations |
| `99_references.md` | Human-readable mirror of `references.bib` |

Sidecars, not rendered as sections: `preamble.md` (LaTeX commands),
`config.yaml` (metadata + parameter mirror), `config.yaml.example`,
`references.bib`, `layer_contract.yaml`, `SYNTAX.md`, `README.md`, and this
file. Only files matching `[0-9][0-9]_*.md` are resolved and copied.

## Metrics are tokens, never text

Every quantity is a `{{TOKEN}}` resolved by
`src/never_say_never_again/manuscript_variables.py`. To state a new number:

1. Compute it in a domain module (never in the manuscript layer).
2. Add the token to `generate_variables()`, formatted at a fixed precision.
3. Reference `{{YOUR_TOKEN}}` in the prose.
4. If it introduces a new canonical constant, mirror it into the `remount:`
   block of `config.yaml` — the mirror is asserted against the code.

Two gates enforce this. Every `{{TOKEN}}` in a numbered section must resolve or
the suite fails, and strict resolution refuses to write a tree containing a
leftover brace. A third scans `03_results.md` for bare decimals outside code
spans and fails on any it finds.

## Citations

`references.bib` may contain only real, checkable sources: real authors, real
titles, real years, and a DOI where one exists. Do not invent an entry, and do
not cite a model this package does not implement. If you are not confident a
reference exists, remove it rather than ship it. The two BOND-suite entries are
unpublished local working trees and are deliberately typed `@misc` with an
explicit "no remote, no DOI" note rather than dressed up as journal articles.

Cite with pandoc-crossref syntax, `[@key]` — see `SYNTAX.md`.

## Claims

- State only what the code computed. Every result here comes from one canonical
  parameter set; none is a measurement of a real operation.
- Keep the limitations in `07_scope_and_related_work.md` current. They are load
  bearing, not decoration — if you add a model, add its bounds.
- If prose makes a mathematical claim (monotonicity, a bound, a crossing
  point), assert it in a test and say so in the sentence. Several already do.

## Regenerating

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

Writes `output/data/manuscript_variables.json`, the resolved tree under
`output/manuscript/`, and the five figures under `output/figures/`. All of
`output/` is git-ignored. Add `--allow-draft` only for a deliberate
work-in-progress; it disables the strict token gate.
