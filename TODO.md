# never_say_never_again — TODO

Remaining work for the REMOUNT film package. Completed work is deliberately not
listed here; the git history and `docs/architecture.md` describe what exists.
This file is for what is *not* done.

## Open work

### Model depth

- [ ] **Sensitivity analysis.** Every result is produced at a single canonical
      parameter set, and `manuscript/07_scope_and_related_work.md` names this as
      a limitation. Add a sweep over the parameters that most affect the
      conclusions — success-model sensitivity `S`, `DETECTION_RATE`, and
      `LEARNING_RATE` — and report how far the "remount improves" and "keep the
      campaign short" conclusions hold. Acceptance: a tested `sensitivity.py`
      module, a figure, and tokenized bounds in the results section.
- [ ] **Optimal campaign length as a solver.** The risk model's expected value
      falls monotonically in replay count and crosses zero, but the crossing is
      currently located only by a test scanning integers. Expose
      `optimal_campaign_length()` so the recommendation is a computed output of
      the model rather than a property discovered in the suite.
- [ ] **Objective-set mismatch reporting.** `diff_outcomes` silently skips
      objectives present on only one side. Consider returning the unmatched ids
      alongside the diffs so a caller can detect a mismatch without comparing
      lengths. This changes `OpDiff`'s shape — confirm no fleet consumer reads
      it positionally first.
- [ ] **Scenario-aware weights.** `op_diff` recovers objective weights by
      scenario *name*, so a caller-built scenario reusing the canonical name
      would be diffed against canonical weights. The clean fix threads the
      `Scenario` through `diff_outcomes`, which changes a signature fleet code
      calls — needs coordination, not a unilateral edit.

### Declared integration points

Both are blocked on `bond-utilities` being reachable from this package. Neither
should be worked around in-package.

- [ ] **Provenance persistence.** Outcomes currently build their `Provenance`
      block in-package. Acceptance: delegate persistence to
      `bond_utilities.mission_io.record_provenance_outcome` while preserving
      `Provenance.input_hash` semantics exactly.
- [ ] **Signed asset chains.** `legacy_assets` is fingerprint-only: it detects
      tampering against a declared digest but models no chain of custody, and
      offers no protection against an attacker who rewrites content and digest
      together. Acceptance: layer a signed-chain / integrity-registry helper
      over `AssetCatalog` without changing its pure core.

### Documentation

- [ ] **Generate `docs/_generated/COUNTS.md` mechanically.** It is currently
      updated by hand from an observed run — the one manual transcription step
      left in a package that distrusts exactly that everywhere else. Acceptance:
      a script parsing real coverage output and rewriting the file, so the
      counts can be neither stale nor invented.

## Guardrails to preserve

Not tasks — invariants any future change must maintain.

1. Domain core stays `bond_api`- and `infrastructure`-free (six modules).
2. No mock framework — real data and real computation only.
3. Manuscript metrics stay `{{TOKEN}}`-injected, never hand-authored.
4. Deterministic: no RNG, no wall-clock in persisted artifacts.
5. `mission.py`'s public shape is frozen: `GADGET_REGISTRY`, `MissionProvider`,
   `film`, and the five protocol methods.
6. One canonical source per constant; `manuscript/config.yaml` mirrors them and
   the mirror is gate-checked.
7. Local-only tree — never push, there is no remote.
