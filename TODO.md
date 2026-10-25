# TODO — never_say_never_again (REMOUNT)

`never_say_never_again` is the PROJECT BOND film package for mission codename
**REMOUNT**: a pure, deterministic domain core (seven stdlib-only modules —
replay, op diff, asset migration, escalation risk, marginal-gain allocation,
replay learning, sensitivity) behind three adapters (`mission.py` implementing the frozen
`bond_api.MissionProvider`, `manuscript_variables.py`, `figures.py`). Verified
state as of this file's commit, measured by a real run in this session:
**140 tests collected, 140 passed, 0 failed, 0 skipped; 100.00 % line+branch
coverage on `src/`** (700 statements, 158 branches, floor 90 %), with
`ruff check`, `ruff format --check` (37 files), and `mypy src/ scripts/`
(19 files) all clean. The seven adversarial-verifier findings recorded in
`../output/verify/never_say_never_again.json` were all remediated in `c8f6d3a`;
this file carries only what remains, plus the three items the remediation pass
disclosed as unresolved.

Every item below was re-checked against the tree at the commit this file lands
in. Nothing is listed because it sounds like diligence.

## Open work

### Correctness

Nothing in `src/` is currently known to compute a wrong answer. The four items
here are model/API shape defects — behaviour that is documented and tested as-is
but that a caller can reasonably be surprised by. All four are also written down
as limitations in `manuscript/07_scope_and_related_work.md`, so shipping them is
honest; fixing them would let those limitation bullets be deleted.

| # | Item |
| --- | --- |
| C1 | **`diff_outcomes` silently drops one-sided objectives.** `src/never_say_never_again/op_diff.py:128-131` — `other = remount_by_id.get(...)`, `if other is None: continue`. An objective present in only one replay produces no `ObjectiveDiff` and contributes to none of the counts or means, so a caller comparing two different objective sets silently gets the intersection. The only signal is `len(diff.diffs)` being short of both outcome counts (documented at `op_diff.py:107-112`, limitation at `manuscript/07_scope_and_related_work.md:41-44`). **Done when:** `OpDiff` carries the unmatched ids (e.g. `only_original: tuple[str, ...]`, `only_remount: tuple[str, ...]`), a test asserts both are populated for a deliberately mismatched pair and empty for the canonical pair, and the `manuscript/07` bullet is deleted. `OpDiff` is a frozen dataclass consumed by `mission.py` and the manuscript hydrator — confirm no fleet consumer unpacks it positionally before changing its shape (`rg -n "OpDiff\(" ..` across the suite). **Demonstrate:** `uv run pytest tests/test_op_diff.py -v` plus `uv run python scripts/execute.py` still writing a well-formed `output/data/remount_outcome.json`. |
| C2 | **Objective weights are recovered by scenario *name*.** `src/never_say_never_again/op_diff.py:168-191` — `_objective_specs` returns `LEGACY_SCENARIO.objectives` when `result.scenario == LEGACY_SCENARIO.name` (line 186) and unity weights otherwise. A caller-built `Scenario` reusing the string `THUNDERBALL-65` with different weights is diffed against the canonical weights, producing a `weighted_delta` for a model nobody ran. Limitation stated at `manuscript/07_scope_and_related_work.md:45-47`. **Done when:** `diff_outcomes` takes the originating `Scenario` (keyword-only with a default, so existing calls keep working) and uses its weights directly, with a test that builds a same-named scenario carrying different weights and asserts the `weighted_delta` follows the passed scenario, not the module constant. This changes a signature fleet code calls — coordinate with `bond-cli` / `bond-coordinator` / `bond-orchestrator` first; do not edit unilaterally. **Demonstrate:** `uv run pytest tests/test_op_diff.py -v` and `uv run python scripts/00_preflight.py`. |
| C3 | **No `optimal_campaign_length()` in the risk model.** `src/never_say_never_again/remount_risk.py` exports eleven names (`__all__`, lines 29-44) and none of them locate the campaign length at which expected value crosses zero. The crossing is found only by a test scanning integers — `tests/test_remount_risk.py:217`, `crossing = next(n for n in range(1, 200) if ev(n) <= 0.0)` — so the manuscript's "keep the campaign short" recommendation is a property discovered in the suite rather than an output of the model. **Done when:** `optimal_campaign_length(*, rate, blocks, reward, penalty) -> int` exists, is exported, and `tests/test_remount_risk.py:198-224` asserts against the function instead of re-deriving the scan (keeping the scan as an independent oracle in the same test is the right shape). **Demonstrate:** `uv run pytest tests/test_remount_risk.py -v`. |
| C4 | **The canonical `MISSION_SEED` is inert but not obviously so.** `src/never_say_never_again/mission_replay.py:47` defines `MISSION_SEED = 13`; nothing samples, so changing it cannot change a result (`AGENTS.md` "Determinism" says exactly this, and the config mirror gate pins the value). It is provenance-only by design and this is *not* a bug — but there is no test that would notice if a future contributor wired it into a code path that does branch on it. **Done when:** a test replays the canonical scenario under two different `MISSION_SEED` values (monkeypatching the module constant, the one permitted environment substitution per `docs/testing_philosophy.md`) and asserts byte-identical `ReplayResult`s. **Demonstrate:** `uv run pytest tests/test_mission_replay.py -v`. |

### Verification

| # | Item |
| --- | --- |
| V1 | **No sensitivity analysis binds the two headline conclusions.** Every result is produced at one canonical parameter set; `manuscript/07_scope_and_related_work.md:54-55` and `manuscript/04_conclusion.md:34-40` both say so in plain terms. The three parameters the conclusions actually rest on are `DEFAULT_SENSITIVITY = 6.0` (`src/never_say_never_again/mission_replay.py:50`), `DETECTION_RATE = 0.25` (`src/never_say_never_again/remount_risk.py:47`), and `LEARNING_RATE = 0.4` (`src/never_say_never_again/learning_curve.py:45`). **Done when:** a pure `src/never_say_never_again/sensitivity.py` sweeps each parameter over a declared range and reports the sub-range over which (a) `OpDiff.overall == "improved"` and (b) the campaign-EV zero crossing stays above `REPLAY_CAMPAIGN_LENGTH = 6`; a test asserts the reported bounds; a fifth figure renders the sweep; and `manuscript/03_results.md` carries the bounds as `{{TOKEN}}`s so the limitation bullet at `07:54-55` can be narrowed rather than deleted wholesale. Keep the module stdlib-only — it belongs in the pure core, and `tests/test_mission_provider.py`'s domain-purity gate reads the core module list, which must be updated to seven. **Demonstrate:** `uv run pytest tests/ --cov=src --cov-fail-under=90` and `uv run python scripts/z_generate_manuscript_variables.py`. |
| V2 | **The allocation-ceiling branch is no longer exercised by real data.** `_score_with` (`src/never_say_never_again/asset_allocator.py:131-137`) clamps at `1.0`. Since the pool moved to replay-derived base scores (`build_allocation_pool`, `asset_allocator.py:274-316`), every canonical objective's `base + cap` sits below 1.0, so the clamp is reached only by synthetic-objective tests, never by the shipped pool. Coverage still shows 100 % because those synthetic tests execute it — coverage is not the question here. This was disclosed by the remediation pass rather than hidden. **Done when:** either a canonical objective legitimately saturates (making the clamp load-bearing again), or a test explicitly asserts the invariant "no canonical objective's `base_score + improvement_cap` exceeds 1.0" so that a future curve change that *does* cross the ceiling has to be a deliberate, visible edit. **Demonstrate:** `uv run pytest tests/test_asset_allocator.py -v`. |
| V3 | **The uniform-spread comparator no longer discriminates.** `tests/test_asset_allocator.py:255-273` compares the greedy against a naive uniform spread; on the current replay-derived pool the two land on the same assignment, so the test is a floor, not evidence. It is honestly labelled as such in its own docstring and in `docs/testing_philosophy.md`, and the discriminating work moved to `test_greedy_allocation_is_exactly_optimal_by_exhaustive_search` (line 276) with `test_unweighted_selection_fails_the_optimality_gate` (line 328) as its negative control. Nothing is currently overclaimed. **Done when:** the uniform comparator is either evaluated on a pool where it *does* differ (proving it can fail) or deleted as redundant with the exhaustive gate — a comparator that cannot distinguish the two policies buys nothing. **Demonstrate:** `uv run pytest tests/test_asset_allocator.py -v`. |

### Documentation

| # | Item |
| --- | --- |
| D1 | **`docs/_generated/COUNTS.md` is transcribed by hand.** The file's own header admits it: "transcribed from a real `pytest --cov` run whose output was read". It is the one manual transcription step left in a package whose entire testing philosophy is that hand-copied numbers drift. It is accurate today (140 / 100.00 % — re-measured this session), which is exactly when it is cheapest to automate. **Done when:** `scripts/z_generate_counts.py` parses real `pytest --cov` output (or `coverage json`) and rewrites the file, and a test asserts the committed file matches a freshly generated one. **Demonstrate:** `uv run python scripts/z_generate_counts.py && git diff --exit-code docs/_generated/COUNTS.md`. |
| D2 | **`scripts/AGENTS.md` row descriptions are unverified against their scripts.** The remediation pass could not confirm what verifier finding 7(b) ("two stale script descriptions") referred to — the finding's summary is truncated mid-sentence in `../output/verify/never_say_never_again.json`. Every row of the table in `scripts/AGENTS.md` was audited by hand against its script and only `execute.py`'s pipeline description was found stale (fixed in `c8f6d3a`). If 7(b) meant a different row, it is still open and nobody knows which. **Done when:** a test reads each script's module docstring and asserts the `scripts/AGENTS.md` table row for that script is consistent with it — turning a hand audit into a gate, which is the only way this closes permanently. **Demonstrate:** `uv run pytest tests/test_scripts_smoke.py -v`. |

### Extension

Both items below are declared integration points against Layer 0
(`bond-utilities`). Neither should be worked around in-package.

| # | Item |
| --- | --- |
| E1 | **Provenance persistence should delegate to `bond-utilities`.** `src/never_say_never_again/mission.py:304-309` builds its `Provenance` block in-package, hashing via the local `_mission_input_hash` (`mission.py:100`). The sibling package now ships the intended helper: `bond_utilities.mission_io.record_provenance_outcome` at `../bond-utilities/src/bond_utilities/mission_io.py:153`, exported from `bond_utilities/__init__.py:82`. The only thing blocking adoption is that `pyproject.toml` declares `bond-api` and nothing else (`dependencies`, lines 17-22; `[tool.uv.sources]`, line 36) — this is no longer blocked upstream. **Watch out:** `record_provenance_outcome` defaults `started_at` to `datetime.now(timezone.utc)`, which would break this package's determinism invariant ("no wall-clock reads in persisted artifacts", `AGENTS.md`) unless `started_at`/`now` are passed explicitly. That invariant is now enforced rather than asserted — `tests/test_regeneration_determinism.py` regenerates the artifact set twice across a clock-second boundary — but its lexical backstop only scans this package's `src/`, so a clock read reached through `bond_utilities` would slip past it; the two-run comparison is what would catch it, and only if `execute.py` output is in the compared set. **Done when:** `bond-utilities` is declared as a path dependency, `mission.py` delegates persistence to the helper while `Provenance.input_hash` keeps byte-identical semantics (pin the pre-change hash as a literal in a test first, then assert the post-change hash equals it), and two consecutive `scripts/execute.py` runs still produce byte-identical JSON. **Demonstrate:** `uv run pytest tests/ --cov=src --cov-fail-under=90` and `uv run python scripts/execute.py --out /tmp/a.json && uv run python scripts/execute.py --out /tmp/b.json && diff /tmp/a.json /tmp/b.json`. |
| E2 | **Signed asset chains — genuinely blocked upstream.** `src/never_say_never_again/legacy_assets.py` is fingerprint-only: `AssetCatalog` (line 191) over `LEGACY_INDEX` (line 282) detects tampering against a declared SHA-256 digest but models no chain of custody, and offers nothing against an attacker who rewrites content and digest together. `manuscript/07_scope_and_related_work.md:48-53` states this scope honestly, including that an unscanned asset (`integrity is None`) is treated as self-consistent by design. Unlike E1 this is still blocked: `rg "def .*chain\|def .*sign" ../bond-utilities/src/bond_utilities/` returns nothing — no signing or integrity-registry helper exists to delegate to. **Done when:** `bond-utilities` ships a signed-chain / integrity-registry helper and a thin adapter layers it over `AssetCatalog` **without** changing the pure core's shape or its stdlib-only import list. **Demonstrate:** `uv run pytest tests/test_legacy_assets.py -v` plus the domain-purity gate in `tests/test_mission_provider.py` still passing. |

## Known limitations (not bugs)

Accepted, deliberate, and not to be re-litigated. Each is stated in the
manuscript's own limitations section, so the package does not claim more than
it delivers.

1. **The success model is illustrative, not calibrated.** A single logistic
   curve with a hand-chosen sensitivity (`DEFAULT_SENSITIVITY = 6.0`). No claim
   in the manuscript is an empirical claim about real operations
   (`manuscript/07_scope_and_related_work.md:38-40`).
2. **All parameters are chosen, not fitted.** Detection rate, learning rate,
   allocation caps and efficiencies, reward and penalty are stipulated model
   inputs; `ALLOCATION_CURVES` says so at `asset_allocator.py:255-258`. V1
   above would bound the conclusions' robustness, not make the numbers
   empirical.
3. **`MISSION_SEED` is provenance-only.** Nothing samples, so the seed cannot
   change a result. It is mirrored into `manuscript/config.yaml` and gate-checked
   purely so provenance records agree.
4. **`wall_time_s` is fixed at `0.0`.** Read it as "not recorded", not
   "instantaneous" — a wall-clock read would break determinism.
5. **An unscanned asset is treated as self-consistent.** Absence of a
   fingerprint is not evidence of integrity
   (`manuscript/07_scope_and_related_work.md:52-53`).
6. **100 % coverage is a floor, not evidence.** `docs/_generated/COUNTS.md`
   records the reason first-hand: two real defects and, later, a hollow negative
   control and a tautological assertion all lived *inside* a fully-covered
   suite. Do not read the number as correctness.
7. **The uniform-spread comparator currently proves only a floor** (see V3).
   This is disclosed rather than dressed up; the discriminating gate is the
   exhaustive-optimality search with its unweighted-selection negative control.
8. **Scope is exactly this directory.** The canonical upstream is the private
   GitHub repository `docxology/bond-never_say_never_again`; publish through
   the GitVault tool, never by an ad-hoc push.

## Guardrails to preserve

Invariants, not tasks. Any change above must keep all of these true.

1. The domain core stays `bond_api`- and `infrastructure`-free and stdlib-only
   (seven modules since V1 landed: `mission_replay.py`, `op_diff.py`,
   `legacy_assets.py`, `remount_risk.py`, `asset_allocator.py`,
   `learning_curve.py`, `sensitivity.py` — the list read by
   `tests/test_mission_provider.py`).
2. No mock framework. Real data, real computation; `monkeypatch` for
   environment isolation only.
3. Manuscript metrics stay `{{TOKEN}}`-injected, never hand-authored in prose.
4. Deterministic: no RNG, no wall-clock in persisted artifacts, no network.
5. `mission.py`'s public shape is frozen: `GADGET_REGISTRY`, `MissionProvider`,
   `film`, and the five protocol methods `brief`/`recon`/`plan`/`execute`/
   `debrief`. Adding a module-level name is safe; renaming or removing one
   breaks the fleet.
6. One canonical source per constant; `manuscript/config.yaml` mirrors them and
   the mirror is gate-checked by `assert_config_mirrors_the_code_constants`.

## Verification

Run from this directory. Read the output of each — an exit code alone is not
evidence. If `uv` reports `Failed to initialize cache`, that is a sandbox
restriction; rerun with the sandbox disabled.

```bash
uv sync --extra dev

uv run pytest tests/ --cov=src --cov-fail-under=90
# expect: 172 passed, 0 failed, 0 skipped; TOTAL 100.00 % on src/ (floor 90 %)
# On a network/external volume, point coverage at a local disk first
# (COVERAGE_FILE=/tmp/.coverage) — its SQLite store fails on some non-local FS.

uv run ruff check src/ scripts/ tests/          # expect: All checks passed!
uv run ruff format --check src/ scripts/ tests/ # expect: 41 files already formatted
uv run mypy src/ scripts/                       # expect: no issues in 21 source files

uv run python scripts/00_preflight.py           # protocol conformance
uv run python scripts/run_mission.py            # full five-stage flow
uv run python scripts/z_generate_manuscript_variables.py
# expect: 64 variables resolved (strict), five figures under output/figures/

rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'  # expect zero
git status --short   # expect clean — output/ is git-ignored
```


---

## Round-2 (2026-08-06)

Round 2 found and fixed a genuine edge-defect class plus two declared open
items, and deepened the manuscript and the sensitivity story. Gates stayed green
throughout: **172 tests collected, 172 passed, 0 failed, 0 skipped; 100.00 %
line+branch on `src/`** (10 modules, 827 statements, 184 branches), `ruff check`
+ `ruff format --check` (41 files) + `mypy src/ scripts/` (21 files) clean, and
the byte-level regeneration test green with the new fifth figure in the
compared set.

### Findings and fixes

| Finding | Fix | Test evidence |
| --- | --- | --- |
| **NaN/inf propagation through the validation guards.** The `_require_in_unit` / `_require_probability` guards already reject NaN (a range comparison like `0 <= nan <= 1` is false), but every **non-negative and positive** guard — `objective.weight`, `RemountConfig.doctrine`, `ReplayEngine.sensitivity`, `detection_rate`, `campaign reward/penalty`, `improvement cap/efficiency`, learning `rate`, and `AllocatableObjective.weight` — compared `< 0.0` / `<= 0.0`, which NaN and ±inf silently pass (every NaN comparison is false). NaN weights/rates/caps therefore sailed into command scores, expected values, allocation plans, and learning curves, returning NaN artifacts instead of failing loudly. | Added `math.isfinite(float(v))` to every such guard across `mission_replay.py`, `remount_risk.py`, `asset_allocator.py`, `learning_curve.py`; added a `_require_finite` guard to `learning_curve` for initial/final/rate/target. Rate `<= 0` still deliberately returns `None` (unreachable) from `iterations_to_target` — only NaN/inf are now rejected. | `test_mission_replay.py::test_validation_rejects_non_finite_parameters`; `test_remount_risk.py::test_non_finite_inputs_are_rejected`; `test_asset_allocator.py::test_non_finite_inputs_are_rejected`; `test_learning_curve.py::test_non_finite_inputs_are_rejected` — 14 distinct NaN/±inf cases now raise `ValueError` with a "finite" message. |
| **Negative / NaN `epsilon` in `diff_outcomes` silently inverts verdicts.** `_verdict` uses `delta > epsilon` / `delta < -epsilon`; a negative `epsilon` makes even a zero delta classify as "improved" (verified: two identical replays diffed with `epsilon=-1.0` report `overall == "improved"`). | `diff_outcomes` now rejects any non-finite or negative `epsilon`. | `test_op_diff.py::test_negative_epsilon_is_rejected` — `-1.0`, `-1e-12`, NaN, ±inf all raise; `epsilon=0.0` still works. |
| **C3 — no `optimal_campaign_length()` in the risk model.** The "keep the campaign short" crossing lived only in a test scanning integers. | Added `optimal_campaign_length(*, rate, blocks, reward, penalty) -> int`, exported and `__all__`-listed; raises `ValueError` when the campaign never crosses non-positive (e.g. zero penalty). | `test_remount_risk.py::test_optimal_campaign_length_is_the_first_non_positive_crossing` binds it to an independent scan (canonical = 13) and checks `EV(n)<=0` / `EV(n-1)>0`; `..._raises_when_crossing_never_happens` covers the no-crossing raise. |
| **V1 — no sensitivity analysis bound the headline conclusions.** | New pure `src/never_say_never_again/sensitivity.py` (7th core module, stdlib-only) with `conclusions_hold` / `robust_range` / `sensitivity_summary`, sweeping each of `DEFAULT_SENSITIVITY`, `DETECTION_RATE`, `LEARNING_RATE` over a declared range and reporting the largest contiguous sub-range, containing the canonical value, over which **both** conclusions hold — including the EV zero-crossing via the new `optimal_campaign_length`. Live results: sensitivity robust over `[0.5, 20]`; detection-rate robust to `[0.05, 0.527]` (breaks at high rate); learning-rate insensitive by construction. | `tests/test_sensitivity.py` (9 tests), incl. the bounded detection-rate range, full-range sensitivity, learning-rate insensitivity, and an unknown-parameter negative control. Domain-purity gate in `test_mission_provider.py` updated 6→7 modules. |
| **V1 (figures) — no visual for the robustness story.** | Added `render_sensitivity_figure` (1×3 panels of each swept parameter's robust sub-range) → `output/figures/sensitivity_sweep.png`; wired into `z_generate_manuscript_variables.py` and into `test_regeneration_determinism.py`'s compared artifact set. | `test_figures.py::test_render_sensitivity_figure_*` (deterministic + default path). |
| **V1 (manuscript) — limitation bullet now narrowed, not deleted.** | `manuscript/03_results.md` gains a "Sensitivity and robustness" section with a live token table (`{{SENS_*}}`) and the fifth figure; `02_methodology.md` documents the OAT method; `04_conclusion.md` and `07_scope_and_related_work.md` updated. The `07` limitation now states the OAT (one-at-a-time) bound rather than "no sensitivity analysis". | `z_generate_manuscript_variables.py` resolves 64 variables strict; regenerated tree brace-clean. |
| **D1 — `COUNTS.md` was hand-transcribed.** | Added `scripts/z_generate_counts.py`, which runs a real `pytest --cov` pass (JSON) excluding its own meta-test and rewrites `docs/_generated/COUNTS.md` from measured numbers; caveat preserved. | `test_scripts_smoke.py::test_z_generate_counts_regenerates_identical_file` regenerates into a temp path and asserts byte-equality with the committed file. |

### Guardrails held

1. Domain core now **seven** stdlib-only modules; the purity gate in
   `test_mission_provider.py` reads the updated list.
2. Zero mocks; every new test is real-computation.
3. All new manuscript metrics are `{{TOKEN}}`s (64 variables resolve strict);
   the config mirror gate now also binds the `robustness:` sweep block.
4. Determinism intact: no RNG, no wall-clock; the two-run byte test passes with
   the fifth figure included.
5. `mission.py` public shape unchanged (`GADGET_REGISTRY`, `MissionProvider`,
   `film`, the five methods).

### Left for a future round

- C1 (one-sided objectives in `diff_outcomes`), C2 (weights-by-scenario-name),
  C4 (MISSION_SEED arg-invariance test), V2 (allocation-ceiling invariant),
  V3 (uniform-spread comparator), D2 (script/AGENTS row consistency test), E1
  (bond-utilities provenance), E2 (signed asset chains) — all unchanged and
  still as documented above.
- The sensitivity analysis is intentionally OAT; a joint/two-parameter sweep or
  Sobol-style global decomposition would extend it (would belong in
  `sensitivity.py`, keeping it stdlib-only).
