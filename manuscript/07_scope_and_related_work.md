# Scope and related work

## Scope

This package is strictly a BOND suite film package. Its scope is exactly its
own directory; it implements the frozen `bond_api` mission protocol as a thin
adapter (`mission.py`) on top of a pure, infrastructure-free domain core
(`mission_replay.py`, `op_diff.py`, `legacy_assets.py`). It does not attempt
to be a general simulation framework or a full intelligence management system.

## Related work

The BOND suite provides Layer 0 (`bond-utilities`, codenames, ciphers, clock,
mission provenance) and Layer 1 (`bond-api`, the frozen `MissionProvider`
protocol). This film implements the Layer-1 contract with a deterministic
domain core, following the same pattern as the reference film `sable`. The
domain core deliberately imports neither `bond_api` nor `bond-utilities`, so it
remains reusable if either dependency is replaced.

## Limitations

- The success model is a single Logistic curve; it is illustrative, not a
  calibrated forecast.
- `diff_outcomes` aligns objectives by id; objectives appearing on only one
  side are not diffed.
- The migration is fingerprint-only; it does not model cryptographic
  provenance like signed chains (an integration point for `bond-utilities`
  once its `mission_io` helper is bound).
