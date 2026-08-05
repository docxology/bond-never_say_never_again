# Architecture — Never Say Never Again (REMOUNT)

Nine modules in `src/never_say_never_again/`, in two tiers: a pure domain core
of six, and three modules that adapt that core to the outside world (the BOND
protocol, the manuscript, and Matplotlib). Nothing in the core knows any of
those three exist.

## Tier map

```
scripts/                     thin orchestrators — argv, I/O, printing only
  |  import
src/never_say_never_again/
  ├── mission.py              ADAPTER → bond_api.MissionProvider + GadgetRegistry
  ├── manuscript_variables.py ADAPTER → {{TOKEN}} hydration from config + core
  ├── figures.py              ADAPTER → deterministic Matplotlib (Agg) → PNG
  │
  ├── mission_replay.py       CORE  scenario replay (the engine)
  ├── op_diff.py              CORE  original vs remount comparison
  ├── legacy_assets.py        CORE  intel migration + integrity
  ├── remount_risk.py         CORE  detection hazard, reliability, campaign EV
  ├── asset_allocator.py      CORE  marginal-gain allocation
  └── learning_curve.py       CORE  replay-learning forecast
```

Dependency direction is strictly downward. Core modules import stdlib and, in
two cases, each other (`op_diff` and `learning_curve` both import
`mission_replay`); adapters import core; scripts import adapters. Nothing
imports upward.

## The pure domain core

### `mission_replay.py` — the engine

The centre of the package. Defines `ObjectiveSpec` (id, positive weight,
difficulty and baseline intel both in [0, 1]), `Scenario` (an ordered tuple of
objectives plus a timeline), and `RemountConfig` (the three remount deltas:
`intel_bonus`, `doctrine` multiplier, `realism_ceiling` cap).

`ReplayEngine.replay(scenario, config)` computes, per objective, an effective
intel `clamp((baseline + bonus) * doctrine, 0, ceiling)`, converts the margin
over difficulty into a score through a numerically stable logistic
`1 / (1 + exp(-S · Δ))`, marks the objective achieved at or above the success
threshold, and returns a frozen `ReplayResult` carrying every per-objective
`ObjectiveOutcome`, the weight-weighted `command_score`, and the count of
fulfilled objectives.

Also owns the package-wide constants the rest of the tree reads rather than
redeclares: `LEGACY_SCENARIO` (the canonical `THUNDERBALL-65` dataset),
`REMOUNT_CONFIG`, `DEFAULT_SENSITIVITY`, `DEFAULT_SUCCESS_THRESHOLD`, and
`MISSION_SEED`.

### `op_diff.py` — the comparison

`diff_outcomes(original, remount)` aligns two `ReplayResult`s by objective id in
the original's order, producing an `ObjectiveDiff` per objective (both scores,
the signed delta, and an `improved`/`regressed`/`unchanged` verdict against an
epsilon) and an aggregate `OpDiff` with the mean delta, the weight-weighted
delta, the three counts, and an overall verdict.

Two behaviours worth knowing before you call it. Objectives present on only one
side are **skipped entirely** — no diff row, no count, no contribution to
either average; the only signal is that `len(diff.diffs)` is short. And because
a `ReplayResult` records the scenario *name* rather than its weights, weights
are recovered by name: the canonical scenario gets its real weights, anything
else gets unity weights so the weighted delta degrades to the plain mean rather
than failing.

### `legacy_assets.py` — migration and integrity

`LegacyAsset` is a frozen intel record whose `integrity` field is the SHA-256
fingerprint *claimed* for its content. `verify` recomputes the fingerprint over
NFC-normalized UTF-8 and compares; a `None` fingerprint means un-scanned and is
treated as self-consistent by design. `remaster` migrates a source to
`version + 1` with fresh content and a freshly computed fingerprint, refusing
by default to migrate a source that fails its own check
(`AssetIntegrityError`). `AssetCatalog` is an ordered registry with duplicate
rejection, per-kind counts, whole-catalog verification, batch `migrate`, and
`stable_integrity()` — a catalog-wide digest over sorted
`(id, kind, content-digest)` rows.

`LEGACY_INDEX` and `canonical_catalog()` are the single definition of what the
remount actually migrates. The mission provider, the manuscript tokens, and the
asset-distribution figure all read them, which is why none of the three can
disagree about the migration.

### `remount_risk.py` — what a replay costs

Closed-form, no simulation. `detection_probability(rate, replays)` is the
Poisson hazard `1 - exp(-rate · N)`; `expected_operations_before_alert` is
`1 / rate`. Mission success is a reliability block diagram:
`series_reliability` (all must hold), `parallel_reliability` (any suffices),
and `block_reliability` composing a series of parallel blocks.
`campaign_expected_value` prices the campaign as
`P(success) · reward − P(detected) · penalty`. `assess_campaign` combines them
into a validated `RemountRiskReport`, and `canonical_risk_report()` fixes the
canonical parameter set.

### `asset_allocator.py` — spending scarce assets

Each objective has a concave improvement curve `cap · (1 − exp(−e·k))` in the
number of assets `k`, so gains diminish and the objective is submodular.
`allocate` runs a deterministic greedy: each round gives one asset to the
objective with the largest **weight-scaled** capped marginal gain, ties going
to the earlier objective, stopping early once everything saturates.

`build_allocation_pool` derives the allocatable objectives instead of declaring
them: ids and weights come from the scenario, base scores from a real replay of
it, and only the `(cap, efficiency)` pair per objective is stipulated in
`ALLOCATION_CURVES`. That is what makes the plan's weighted totals command-score
units. Before this, the pool re-declared the ids and weights alongside the
scenario's own copies with nothing binding the two, and the manuscript's
"weighted command score" wording described a quantity the allocator never
computed.

The weight scaling is the subtle part, and getting it wrong was a real defect
found in review: the plan reports a weight-weighted score, so a greedy
selecting on the raw score gain maximizes a different function than the one it
reports. The tests now assert the greedy hits the exhaustive optimum over every
feasible split of the budget — the separable-concave case is exactly solvable,
so this is a stronger check than the `(1 − 1/e)` bound — and carry the
unweighted variant as the negative control that fails it.

### `learning_curve.py` — how far rehearsal gets you

`exponential_learning` is the Wright-family curve
`final − (final − initial)·exp(−rate·n)`. `forecast_curve` walks it over
`n = 1..iterations`. `iterations_to_target` inverts it for the first iteration
reaching a target, returning `None` when unreachable — which includes the case
where the asymptote *equals* the target, since the curve approaches without
attaining (an earlier version wrongly returned 1 here).

`forecast_replay` is what makes this more than an equation: both endpoints are
real replays through the engine — the identity config gives the initial value,
the capped-bonus config gives the asymptote — so the forecast is anchored to
computed scores rather than posited ones.

## The adapters

### `mission.py` — how the frozen protocol is implemented

`bond_api.protocol.MissionProvider` is a `@runtime_checkable` structural
`Protocol`. This module satisfies it *structurally* — it subclasses nothing.
Discovery (`bond_api.discovery.load_provider`) finds this package by locating
`<slug>/mission.py` and reading a top-level class named `MissionProvider` whose
`film` attribute matches the slug. That is the whole contract, and it is why
those names must not move.

The five stages map onto the core like this:

| Stage | Returns | What it does |
| --- | --- | --- |
| `brief()` | `MissionBrief` | Declares the six objectives, three `Asset`s (scenario, config, risk model), and the determinism and purity `Constraint`s. Pure declaration — no computation. |
| `recon(request)` | `ReconReport` | Seven `Finding`s surveying the goal, scenario size, queued dossiers, detection hazard, allocation budget, learning parameters, and constraints. |
| `plan(brief)` | `MissionPlan` | Seven `Step`s: replay → diff → migrate → assess_risk → allocate → forecast → verify. |
| `execute(plan)` | `MissionOutcome` | The real pipeline. Replays under identity and remount configs, diffs them, migrates `canonical_catalog()`, reads the three canonical reports, and derives `success` from four conditions that must **all** hold: non-negative weighted delta, verified migration, non-negative campaign EV, non-negative learning delta. Attaches `Provenance` (version, `MISSION_SEED`, brief input hash, `wall_time_s = 0.0`). |
| `debrief(outcome)` | `Debrief` | Wraps the outcome with six standing lessons, one per model. |

Module-level `GADGET_REGISTRY` publishes six gadgets under the film slug —
`engine`, `legacy_scenario`, `remount_config`, `remount_risk_report`,
`allocation_plan`, `learning_forecast` — so an orchestrator can reach the
film's working objects without importing its internals. Registration happens in
`__init__`, and the provider methods use typed module-level references directly
rather than reading back through the registry's opaque payloads.

The three canonical reports are computed once at import (`_RISK_REPORT`,
`_ALLOCATION_PLAN`, `_LEARNING_FORECAST`) using the *same* factory functions
`manuscript_variables.py` calls. That shared-factory discipline is what makes it
impossible for the mission's results and the manuscript's tokens to disagree.

### `manuscript_variables.py` — token hydration

`generate_variables()` loads `manuscript/config.yaml`, runs the live domain
surface, and returns a flat `{TOKEN: str}` map: identity, replay and diff
results, migration counts and fingerprint, every model parameter, the
risk/allocation/learning outputs, and the environment stamp.
`resolve_manuscript_tree()` copies each `NN_*.md` section to
`output/manuscript/` with tokens substituted, raising in strict mode on any
leftover `{{...}}` so a raw brace can never reach the PDF.

### `figures.py` — deterministic rendering

Four Agg-backend figures, each taking an explicit output path and returning it:
`render_op_diff_figure` (grouped bars, original vs remount),
`render_asset_distribution_figure` (migrated assets per kind),
`render_learning_curve_figure` (forecast with initial and target marked), and
`render_allocation_figure` (assets per objective). Same inputs, same bytes.

## Data flow, end to end

```
LEGACY_SCENARIO ──┬─→ ReplayEngine.replay(identity) → original ─┐
                  └─→ ReplayEngine.replay(REMOUNT)  → remount  ─┴→ diff_outcomes → OpDiff
LEGACY_INDEX ─────→ canonical_catalog() → .migrate() ────────────→ MigrationBatch
                    canonical_risk_report() ─────────────────────→ RemountRiskReport
                    canonical_allocation() ──────────────────────→ AllocationPlan
                    canonical_learning_forecast() ───────────────→ LearningReplayForecast
                                             │
                  ┌──────────────────────────┴──────────────────────────┐
                  ↓                                                     ↓
      mission.execute() → MissionOutcome        generate_variables() → {{TOKEN}}s
                                                                     → figures/*.png
```

Both consumers on the bottom row read the same four canonical factories. There
is no second derivation path — that is the structural reason the manuscript
cannot drift from the mission, and why a fix in one automatically lands in the
other.

## Scripts

`scripts/` holds thin orchestrators only: they resolve `src/` onto `sys.path`,
parse argv, call one adapter, print, and write files. No business logic. The
set is `00_preflight.py` (protocol conformance), one script per mission stage
(`brief`, `recon`, `plan`, `execute`, `debrief`), `run_mission.py` (the full
five-stage flow via `bond_api.run_mission`), and
`z_generate_manuscript_variables.py` (tokens, resolved manuscript tree, and the
four figures). All writes go under `output/`, which is git-ignored, so running
them leaves the tree clean.

## Determinism

No RNG, no wall-clock, no network, and no filesystem reads outside
`manuscript/config.yaml`. `MISSION_SEED` is recorded in provenance but seeds
nothing, because nothing samples. `wall_time_s` is fixed at `0.0` deliberately:
a real elapsed time would make otherwise-identical outcomes differ between
runs. Read it as "not recorded", never as "instantaneous".
