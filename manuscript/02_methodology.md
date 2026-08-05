# Methodology

## Scenario model

A scenario is an ordered set of {{NUM_OBJECTIVES}} objectives, each a tuple of
`objective_id`, a positive `weight`, a `difficulty` in [0, 1], and a
`baseline_intel` in [0, 1]. The canonical dataset, `{{SCENARIO_NAME}}` (see
`mission_replay.py`), reopens the 1965 operation. Weights need not sum to one;
they are normalized when the command score is formed.

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

For each objective the engine computes a deterministic success score with the
logistic (Verhulst) curve [@verhulst1838notice]:

$$\text{score}(\Delta) = \frac{1}{1 + e^{-S\,\Delta}}, \qquad \Delta =
\text{eff\_intel} - \text{difficulty}$$

where `S` is the sensitivity (default {{MODEL_SENSITIVITY}}). A score at or
above the `success_threshold` (default {{MODEL_SUCCESS_THRESHOLD}}) counts the
objective as *achieved*. The command score is the weight-weighted mean of
per-objective scores. The implementation evaluates the curve in its
numerically stable branched form (`exp(z) / (1 + exp(z))` for negative `z`) so
that a large negative margin cannot overflow.

The choice of `S` is a modelling choice, not a fitted parameter: it sets how
sharply an intel surplus converts into success, and no operational data is used
to calibrate it.

## Op diff

Given the original and remount replays, `diff_outcomes` aligns objectives by id
(in the original's order) and computes each objective's `delta` and a verdict:
`improved` when `delta > epsilon`, `regressed` when `delta < -epsilon`, else
`unchanged`. The aggregate `weighted_delta` reuses the original scenario's
objective weights, and the overall verdict follows the sign of
`weighted_delta`.

## Remount risk (escalation hazard and reliability)

`remount_risk.py` models the price of a replay. Detection follows a memoryless
exponential (Poisson) hazard [@ross2019probability] —
`P(alert within N replays) = 1 - exp(-rate * N)` with expected operations
before alert `1 / rate` — so repeated replays monotonically raise the chance of
alerting the adversary. Mission success is
modeled as a reliability block diagram: a *series* of *parallel* blocks, where
each block (intel acquisition, insertion, extraction) succeeds if any of its
redundant paths succeeds [@barlow1975reliability]. The campaign expected value
`P(success) * reward - P(detected) * penalty` then prices the whole replay
campaign.

## Asset allocation (marginal gain)

`asset_allocator.py` spends scarce remastered assets. The allocatable
objectives are *derived*, not re-declared: each takes its `objective_id` and
`weight` from the canonical scenario and its `base_score` from that objective's
real score in the remount replay. Only two numbers per objective are stipulated
model inputs — the improvement `cap` an asset can ultimately buy and the
efficiency `e` at which returns diminish — and no operational data calibrates
them. Because the base scores are replay scores and the scenario's weights sum
to one, the plan's weighted total is the replay's command score, and the gains
below are in command-score units rather than in a unit of their own.

Each objective has a concave improvement curve `cap * (1 - exp(-e * k))` in the
number `k` of assigned assets — strictly diminishing returns. A deterministic
greedy allocates each of the `budget` assets to the objective with the largest
**weight-scaled** capped marginal gain — the marginal increase in the weighted
score the plan actually reports — with ties broken by objective order.
Selecting on the unweighted gain instead maximizes a different function than
the one reported; that was a real defect in this module, and the test suite now
carries the wrong variant as a negative control.

The guarantee: the objective is a weighted sum of per-objective concave curves
in that objective's own asset count, which is the separable-concave special
case of monotone submodular maximization. There greedy incremental allocation
is not merely within the `(1 - 1/e)` factor that Nemhauser–Wolsey–Fisher
[@nemhauser1978submodular] guarantee in general — it is *exactly optimal*.
`tests/test_asset_allocator.py` verifies that on the canonical pool by
enumerating every way to split the budget across the objectives and comparing
against the maximum, and shows the unweighted variant failing the same check.

## Replay learning curve

`learning_curve.py` forecasts how rehearsal improves the remount. The command
score follows an exponential learning curve
`final - (final - initial) * exp(-rate * n)` from the baseline replay
(`initial`) toward a fully-reinforced replay asymptote (`final`)
[@wright1936learning]. Both endpoints are *computed*: each is a real replay of
the scenario through the same engine, under the identity config and under the
capped-bonus config respectively.

Inverting the curve gives the first iteration `n` reaching a target score,
`n = ceil(-ln((final - target) / (final - initial)) / rate)`. The solver returns
`None` — target unreachable — whenever the asymptote is at *or below* the
target, since the curve approaches its asymptote without ever attaining it, and
whenever the rate is non-positive.

## Legacy asset migration

Each legacy dossier is a `LegacyAsset` carrying a declared SHA-256
[@nist2015fips180] integrity fingerprint. `verify` recomputes the fingerprint
over NFC-normalized [@unicode2023uax15] UTF-8 content and compares it to the
declared one (`None` = un-scanned, treated as self-consistent). Normalizing
before hashing is what makes the fingerprint a property of the *text* rather
than of one particular encoding of it. `remaster` migrates a source into
`version + 1` with fresh content, optionally reclassifying/re-typing it, and
recomputes the fingerprint; by default it refuses to migrate a source that
fails its own integrity check, raising `AssetIntegrityError` rather than
propagating a suspect dossier. An `AssetCatalog` aggregates assets, verifies
them wholesale, and migrates a subset in a single deterministic batch. The
canonical index the remount actually consumes is `LEGACY_INDEX`, exposed
through `canonical_catalog()` so the mission, the manuscript, and the figures
share one definition of the migration.
