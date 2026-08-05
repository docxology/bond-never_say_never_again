# Methodology

## Scenario model

A scenario is an ordered set of {{NUM_OBJECTIVES}} objectives, each a tuple of
`objective_id`, a positive `weight`, a `difficulty` in [0, 1], and a
`baseline_intel` in [0, 1]. The canonical dataset, `THUNDERBALL-65` (see
`mission_replay.py`), reopens the 1965 operation.

## Remount configuration

A remount applies three deltas (`RemountConfig`):

- `intel_bonus` — extra effective intel added to every objective (reinforced
  intelligence).
- `doctrine` — a multiplicative factor on effective intel (doctrine/doctrine
  adjustments).
- `realism_ceiling` — a cap on effective intel so optimistic assumptions
  cannot overwhelm the model.

The effective intel for an objective is `clamp((baseline + bonus) * doctrine,
0, realism_ceiling)`.

## Success model

For each objective the engine computes a deterministic success score with a
logistic curve:

$$\text{score}(\Delta) = \frac{1}{1 + e^{-S\,\Delta}}, \qquad \Delta =
\text{eff\_intel} - \text{difficulty}$$

where `S` is the sensitivity (default 6.0). A score at or above the
`success_threshold` (default 0.5) counts the objective as *achieved*. The
command score is the weight-weighted mean of per-objective scores.

## Op diff

Given the original and remount replays, `diff_outcomes` aligns objectives by id
(in the original's order) and computes each objective's `delta` and a verdict:
`improved` when `delta > epsilon`, `regressed` when `delta < -epsilon`, else
`unchanged`. The aggregate `weighted_delta` reuses the original scenario's
objective weights, and the overall verdict follows the sign of
`weighted_delta`.

## Remount risk (escalation hazard and reliability)

`remount_risk.py` models the price of a replay. Detection follows a memoryless
exponential (Poisson) hazard — `P(alert within N replays) = 1 - exp(-rate * N)`
with expected operations before alert `1 / rate` — so repeated replays
monotonically raise the chance of alerting the adversary. Mission success is
modeled as a reliability block diagram: a *series* of *parallel* blocks, where
each block (intel acquisition, insertion, extraction) succeeds if any of its
redundant paths succeeds [@barlow1975reliability]. The campaign expected value
`P(success) * reward - P(detected) * penalty` then prices the whole replay
campaign.

## Asset allocation (marginal gain)

`asset_allocator.py` spends scarce remastered assets. Each objective has a
concave improvement curve `cap * (1 - exp(-e * k))` in the number `k` of
assigned assets — strictly diminishing returns, hence submodular. A
deterministic greedy allocates each of the `budget` assets to the objective
with the largest capped marginal gain (ties broken by objective order),
achieving the canonical `(1 - 1/e)` approximation of
Nemhauser–Wolsey–Fisher [@nemhauser1978submodular].

## Replay learning curve

`learning_curve.py` forecasts how rehearsal improves the remount. The command
score follows an exponential learning curve
`final - (final - initial) * exp(-rate * n)` from the baseline replay
(`initial`) toward a fully-reinforced replay asymptote (`final`) [@wright1936learning];
the solver
returns the first iteration reaching a target score, or marks the target
unreachable when the asymptote falls short.

## Legacy asset migration

Each legacy dossier is a `LegacyAsset` carrying a declared SHA-256 integrity
fingerprint. `verify` recomputes the fingerprint over NFC-normalized UTF-8
content and compares it to the declared one (`None` = un-scanned, treated as
self-consistent). `remaster` migrates a source into `version + 1` with fresh
content, optionally reclassifying/re-typing it, and recomputes the fingerprint.
An `AssetCatalog` aggregates assets, verifies them wholesale, and migrates a
subset in a single deterministic batch.
