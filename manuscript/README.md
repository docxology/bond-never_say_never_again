# Manuscript — Never Say Never Again: REMOUNT

This directory holds the manuscript for the REMOUNT mission. Numbered prose
sections (`00_abstract.md` … `99_references.md`) are hydrated by
`scripts/z_generate_manuscript_variables.py`, which resolves every `{{TOKEN}}`
from `manuscript/config.yaml` plus the live domain surface.

Sidecars (not rendered):
- `SYNTAX.md` — citation and cross-reference syntax for Pandoc.
- `preamble.md` — LaTeX commands.
- `layer_contract.yaml` — the BOND suite layer contract for this package.
- `references.bib` — bibliography.
- `config.yaml.example` — richer copy-and-customize template.

Rule: computed metrics are injected as `{{TOKEN}}`s, never hand-authored in
prose. Rendering requires a local Pandoc pipeline; the strict token gate enforces
that no raw brace leaks into the PDF.
