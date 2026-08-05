# Scope and related work

## Scope

This package is strictly a BOND suite film package. Its scope is exactly its
own directory; it implements the frozen `bond_api` mission protocol as a thin
adapter (`mission.py`) on top of a pure, infrastructure-free domain core of six
modules (`mission_replay.py`, `op_diff.py`, `legacy_assets.py`,
`remount_risk.py`, `asset_allocator.py`, `learning_curve.py`). It does not
attempt to be a general simulation framework or a full intelligence management
system.

## Related work

Within the BOND suite this film sits at the film layer: it consumes Layer 1
(`bond-api`, the frozen `MissionProvider` protocol and `GadgetRegistry`) and
imports no sibling film package. Layer 0 (`bond-utilities`) is not yet bound
here; the integration points where it would replace in-package code are named
explicitly in `TODO.md` rather than assumed.

Outside the suite, the models are standard and cited rather than invented. The
allocation greedy is Nemhauser, Wolsey and Fisher's submodular maximization
result [@nemhauser1978submodular]; the rehearsal model is the Wright learning
curve [@wright1936learning]; the mission-success structure is a reliability
block diagram in the sense of Barlow and Proschan [@barlow1975reliability],
with detection as a homogeneous Poisson process [@ross2019probability]; the
per-objective success curve is the Verhulst logistic [@verhulst1838notice];
and integrity uses SHA-256 [@nist2015fips180] over NFC-normalized text
[@unicode2023uax15]. This package contributes their deterministic composition
into an auditable remount pipeline, not the models themselves.

## Limitations

These are real bounds on what the results support, not caveats-as-decoration.

- The success model is a single Logistic curve with a hand-chosen sensitivity;
  it is illustrative, not a forecast calibrated against operational data. No
  claim in this manuscript is an empirical claim about real operations.
- `diff_outcomes` aligns objectives by id and **skips** objectives present on
  only one side: they appear in no diff and in none of the counts. Comparing
  two scenarios with different objective sets therefore silently compares only
  the intersection.
- Objective weights are recovered by scenario *name*. A caller-built scenario
  that reuses the canonical name with different weights would be diffed against
  the canonical weights.
- The migration is fingerprint-only. It detects tampering against a declared
  digest but models no cryptographic provenance — no signatures, no chain of
  custody, and no protection against an attacker who rewrites content and
  digest together.
- An un-scanned asset (`integrity is None`) is treated as self-consistent by
  design, so absence of a fingerprint is not evidence of integrity.
- The risk, allocation, and learning models are evaluated at a single canonical
  parameter set. No sensitivity analysis over that parameter set is reported.
