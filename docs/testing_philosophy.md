# Testing philosophy — Never Say Never Again (REMOUNT)

## The rule

No mock framework. Not `unittest.mock`, not `MagicMock`, not `mocker.patch`,
not a hand-rolled stub standing in for a dependency. Every test in this package
runs the real code against real data.

This is affordable here because of a property of the design rather than
discipline alone: **the domain core is pure and deterministic**. It makes no
random draws, reads no clock, opens no socket, and touches no file. There is
nothing to isolate. `LEGACY_SCENARIO` replayed twice yields byte-identical
results, so the "fixture" is just the canonical constant and the oracle is the
mathematics.

The one permitted substitution is *environment* isolation, not dependency
mocking: `monkeypatch` is used in exactly one place, to swap the module-level
canonical scenario for an empty one so the `require_outputs` guard can be shown
to fire. That replaces a value, not a collaborator, and it is restored
automatically.

## What a good test looks like here

Coverage is necessary and nowhere near sufficient. A test in this package
should do at least one of the following.

**Bind prose to code.** The manuscript claims the campaign expected value
strictly decreases in the replay count. `test_remount_risk.py` evaluates the
real model over 40 replay counts and asserts the decrease, then finds the
sign-change point and asserts it lies beyond the canonical campaign length.
Without that, the claim is just an assertion in a paragraph.

**Carry a positive control.** A guard that rejects bad input proves nothing
unless it also accepts good input — otherwise a guard that rejects everything
would pass. `test_scenario_accepts_a_valid_timeline` exists precisely to make
the neighbouring rejection tests meaningful. Likewise
`test_config_mirror_gate_actually_fails_on_drift` demonstrates the config gate
*can* fail; a gate never shown to fail is decoration.

**Use an honest comparator.** `test_greedy_beats_a_naive_uniform_spread`
compares the allocator against uniform spreading — the policy an operator would
actually reach for — not a deliberately crippled baseline. That comparison is
what caught the allocator selecting on the wrong objective function.

**Pin a fixed defect with its counterexample.** When a bug is fixed, the test
states what the old behaviour was and demonstrates it was wrong.
`test_iterations_to_target_asymptote_equal_to_target_is_unreachable` asserts
the corrected `None`, then shows the score is strictly below target at every
iteration in the useful range — including the iteration the buggy version used
to return. It also records the honest bound: in float64 the curve does
eventually round up to its asymptote, far outside any useful replay count.

**Prefer derived expectations to frozen literals.** Asserting
`allocation_best_objective == "neutralize_cell"` breaks noisily and
uninformatively when the policy legitimately changes. Recomputing the expected
value from the canonical plan turns the same test into a check that the mission
and the model agree — which is the property actually worth defending.

## What tests must not do

- Assert only that a call returns without raising, or that a container is
  non-empty, when the value is checkable.
- Re-implement the function under test as the expected value. Use a closed
  form, an independent derivation, or a known-good constant.
- Hard-code a metric that the manuscript also hard-codes; both should read the
  same source.
- Suppress an error to keep the suite green.

## Structural gates in the suite

Beyond ordinary unit tests, several tests exist purely to keep the package
honest:

| Gate | Test | Prevents |
| --- | --- | --- |
| Domain purity | `test_domain_core_has_no_bond_api_imports` reads the six core module files and asserts `bond_api` never appears | The layer contract eroding one import at a time |
| Protocol conformance | `isinstance(provider, Protocol)` against the real frozen `bond_api` contract, plus discovery by slug | Silently breaking fleet consumers |
| Token resolution | Every `{{TOKEN}}` in `manuscript/[0-9][0-9]_*.md` must exist in `generate_variables()`, and the resolved tree must be brace-clean | Raw braces reaching the PDF; tokens referencing nothing |
| No hand-authored metrics | The results section is scanned for bare decimals outside code spans and tokens | Prose numbers drifting from the code |
| Config mirror | Every value in the `config.yaml` `remount:` block is asserted equal to the constant the code runs on | Documentation describing a model nobody runs |
| Migration agreement | The catalog, the mission outcome, and the manuscript token must report the same asset count and fingerprint | Exactly the drift that produced the migrated-asset count defect |

## Determinism and figures

Figures render with the Agg backend to explicit paths and are byte-stable for
the same inputs. Script smoke tests run the real CLIs through `subprocess` with
`sys.executable`, assert exit codes and stdout, and check the artifacts that
land under `output/` — which is git-ignored, so a full test run leaves
`git status` clean.

## The gates

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90   # floor 90% line+branch on src/
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

The coverage floor is 90%; the suite runs above it. See
[`_generated/COUNTS.md`](_generated/COUNTS.md) for the measured figure — and
re-measure rather than quoting it from memory. A number in prose that nobody
re-derives is the exact failure mode this package is built to prevent.
