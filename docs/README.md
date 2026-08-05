# docs/ — Never Say Never Again (REMOUNT)

Documentation for the `never_say_never_again` film package of PROJECT BOND,
mission codename **REMOUNT**. This directory holds the *operational* docs — how
the package is built, tested, and safely modified. The *scientific* write-up
(what the models are and what they produced) lives in `../manuscript/`, and the
package overview lives in `../README.md`.

## What is in here

| Doc | Read it when |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | You are an agent about to work in this package. Start here — it is the entry point and routes to everything below. |
| [`agent_instructions.md`](agent_instructions.md) | You need the concrete operational rules: scope, purity, protocol stability, the gate commands, and the specific traps this package has already hit. |
| [`architecture.md`](architecture.md) | You are about to add, move, or change a module. Explains all nine `src/` modules individually, how they compose, and exactly how `mission.py` satisfies the frozen `bond_api` `MissionProvider`. |
| [`testing_philosophy.md`](testing_philosophy.md) | You are about to write or change a test. Explains why there are no mocks, what makes a test here meaningful rather than merely green, and the standing gates. |
| [`style_guide.md`](style_guide.md) | You need the typing, docstring, validation, and formatting conventions. |
| [`_generated/COUNTS.md`](_generated/COUNTS.md) | You want the measured test count and coverage. Regenerated from a real run — never hand-edited, and never quoted from memory. |

## The one-paragraph version

*Never Say Never Again* (1983) is a remount of *Thunderball* (1965): the same
operation, re-staged with new equipment. This package makes that literal. A
canonical legacy scenario (`THUNDERBALL-65`) is replayed under a remount
configuration, the two runs are diffed objective by objective, the legacy
intelligence dossiers are re-fingerprinted and migrated, and three further
models price the re-op: how detection risk accumulates across replays, how a
scarce budget of remastered assets should be spent, and how far rehearsal can
push the command score before it stops paying. Everything is deterministic —
no random draws, no wall-clock reads — so any number in the manuscript can be
re-derived by rerunning the code.

## Where numbers come from

No metric in this package is written by hand. Domain modules hold the canonical
constants, `src/never_say_never_again/manuscript_variables.py` reads them and
emits `{{TOKEN}}` values, and the manuscript prose contains only tokens. The
`manuscript/config.yaml` `remount:` block mirrors those constants for human
readers, and the mirror is asserted against the code in
`tests/test_manuscript_variables.py`, so it cannot drift silently. If you find
yourself typing a number into prose, add a variable instead.
