# Never Say Never Again: REMOUNT

A **PROJECT BOND** film package implementing the frozen `bond_api`
`MissionProvider` protocol for mission codename **REMOUNT**.

*Never Say Never Again* (1983) is itself a **remount** of *Thunderball* (1965):
a completed operation re-opened, modernized, and re-run. This package makes
that premise literal and deterministic. It replays a legacy mission under a
remount configuration, diffs the original against the remount objective by
objective, migrates and re-fingerprints the legacy intelligence — and then
prices the re-op, because a remount is never free: detection risk accumulates
with every replay, remastered assets are scarce, and rehearsal buys less each
time.

## Film concept → software

| Concept in the film | Model in the code |
| --- | --- |
| Re-staging a finished operation | Deterministic scenario replay under a remount config |
| "Is the remake actually better?" | Weighted per-objective op diff with a verdict |
| Old equipment brought back into service | SHA-256 re-fingerprinting and versioned asset migration |
| Spectre notices you are back | Poisson detection hazard accumulating over replays |
| Limited new kit from Q-branch | Marginal-gain allocation of a scarce asset budget |
| Bond is out of practice | Exponential replay-learning curve toward an asymptote |

## Modules

Pure domain core — stdlib only, no `bond_api`, no `infrastructure`:

| Module | What it computes |
| --- | --- |
| `src/never_say_never_again/mission_replay.py` | The engine. Replays a `Scenario` under a `RemountConfig` through a numerically stable logistic success curve over effective intel vs difficulty; returns per-objective outcomes and a weighted command score. Owns the canonical `THUNDERBALL-65` dataset and the shared model constants. |
| `src/never_say_never_again/op_diff.py` | Aligns original and remount replays by objective id; per-objective deltas and verdicts plus mean, weight-weighted, and overall aggregates. |
| `src/never_say_never_again/legacy_assets.py` | Asset integrity and migration: SHA-256 fingerprints over NFC-normalized content, tamper detection, versioned remastering, catalog aggregation, and the canonical `LEGACY_INDEX`. |
| `src/never_say_never_again/remount_risk.py` | The cost of replaying: Poisson detection hazard, expected operations before alert, series/parallel reliability block diagrams, and campaign expected value. |
| `src/never_say_never_again/asset_allocator.py` | Deterministic greedy allocation of scarce remastered assets by weight-scaled marginal gain over concave (submodular) improvement curves. |
| `src/never_say_never_again/learning_curve.py` | Wright-family exponential learning forecast between two *computed* replay scores, plus the iteration-to-target solver. |
| `src/never_say_never_again/sensitivity.py` | One-at-a-time sensitivity analysis bounding the sub-range of `Sensitivity`, `DETECTION_RATE`, and `LEARNING_RATE` over which both headline conclusions still hold. |

Adapters — the only modules that know about anything outside the core:

| Module | Role |
| --- | --- |
| `src/never_say_never_again/mission.py` | Implements the frozen `bond_api.MissionProvider` (`brief`/`recon`/`plan`/`execute`/`debrief`); publishes six gadgets on a module-level `GADGET_REGISTRY`. |
| `src/never_say_never_again/manuscript_variables.py` | Hydrates every manuscript `{{TOKEN}}` from `manuscript/config.yaml` plus the live domain surface. |
| `src/never_say_never_again/figures.py` | Four deterministic Matplotlib (Agg) figures into `output/figures/`. |

## The MissionProvider surface

Discovery locates this package by slug: `<slug>/mission.py` exposing a
top-level `MissionProvider` class whose `film` attribute is
`"never_say_never_again"`. It satisfies the protocol structurally — no
subclassing.

```python
from never_say_never_again.mission import GADGET_REGISTRY, MissionProvider

provider = MissionProvider()
provider.film                        # "never_say_never_again"
brief    = provider.brief()          # MissionBrief   — 6 objectives, 3 assets, 2 constraints
report   = provider.recon(request)   # ReconReport    — 7 findings
plan     = provider.plan(brief)      # MissionPlan    — 7 steps
outcome  = provider.execute(plan)    # MissionOutcome — results + Provenance
debrief  = provider.debrief(outcome) # Debrief        — 6 lessons

GADGET_REGISTRY.lookup("never_say_never_again", "engine")
# also: legacy_scenario, remount_config, remount_risk_report,
#       allocation_plan, learning_forecast
```

This shape is frozen across the fleet — `bond-cli`, the coordinator, and the
orchestrator all consume it. Deepen inside the package; never rename or remove
those names.

## Quick start

```bash
# From this package directory. bond-api resolves via the local path source
# `../bond-api` — a sibling bond-api checkout next to this package.
uv sync --extra dev

# Verify the environment and protocol conformance
uv run python scripts/00_preflight.py

# Run the full five-stage mission
uv run python scripts/run_mission.py

# Per-stage CLIs
uv run python scripts/brief.py
uv run python scripts/recon.py "survey the theater"
uv run python scripts/plan.py
uv run python scripts/execute.py            # --out PATH to redirect the JSON
uv run python scripts/debrief.py

# Hydrate manuscript tokens and render the five figures
uv run python scripts/z_generate_manuscript_variables.py
```

Everything writes under `output/`, which is git-ignored, so running the whole
set leaves `git status` clean.

## Results

The canonical remount improves on the legacy operation, and the risk model says
to keep the campaign short. Rather than restate the figures here — where they
would immediately begin to drift — every number lives in exactly one place and
flows outward from it:

- **Run it**: `scripts/execute.py` prints the command scores and verdict and
  writes the full outcome to `output/data/remount_outcome.json`.
- **Read it**: `scripts/z_generate_manuscript_variables.py` writes every
  manuscript token to `output/data/manuscript_variables.json`.
- **Narrative**: `manuscript/03_results.md`, where each quantity is a
  `{{TOKEN}}` injected from the code — never hand-authored in prose.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

The coverage gate is a 90% floor on `src/` (line + branch), with zero failures
and zero skips. The measured test count and coverage from the most recent real
run are recorded in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) —
re-measure rather than trusting a figure quoted in prose.

## Documentation

| Where | What |
| --- | --- |
| [`docs/`](docs/) | Operational docs — architecture, agent instructions, testing philosophy, style guide |
| [`manuscript/`](manuscript/) | The scientific write-up: abstract through references, every metric tokenized |
| [`AGENTS.md`](AGENTS.md) | Build/test/verify contract for agents |
| [`TODO.md`](TODO.md) | Remaining work and declared integration points |
| [`STANDALONE.md`](STANDALONE.md) | The fork contract this package was created under |

## Repository

Canonical upstream: [`docxology/bond-never_say_never_again`](https://github.com/docxology/bond-never_say_never_again)
(private, branch `main`). This is a PROJECT BOND working tree — publish through
the GitVault tool (`./_tools/vault --wait with-repo docxology/bond-never_say_never_again -- git push origin main`)
rather than by an ad-hoc push from the package directory, and never
force-push.
