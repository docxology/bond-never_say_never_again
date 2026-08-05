# Experimental setup

## Canonical dataset

The `THUNDERBALL-65` scenario (`src/never_say_never_again/mission_replay.py`)
is the sole canonical dataset, declared as module-level deterministic
constants. It contains {{NUM_OBJECTIVES}} objectives with fixed weights,
difficulties, and baseline intel, plus an identity config
(`intel_bonus = 0.0`) and the `REMOUNT_CONFIG` used for the remount.

## Parameters

- Success-model sensitivity `S = 6.0`, success threshold `0.5`.
- Remount intel bonus `0.15`, doctrine `1.0`, realism ceiling `1.0`.
- Deterministic seed `13` (provenance-only: the mission makes no random draws).
- SHA-256 fingerprints over NFC-normalized UTF-8 content.
- Risk: detection rate `0.25`/replay, campaign length `6`, reward `100`,
  penalty `100`, reliability blocks (intel 2 paths, insertion 1, extraction 3).
- Allocation: budget `6` assets over 4 objectives (concave curves).
- Learning: rate `0.4`, `8` iterations, bonus cap `0.30`, target `0.55`.

All canonical numeric constants live in the domain modules
(`remount_risk.py`, `asset_allocator.py`, `learning_curve.py`), shared by the
mission adapter, the manuscript tokens, and the figures — no duplicated
numbers.

## Fixtures and isolation

Tests use real data and computation only (no mock framework), with fixed inputs
so every outcome is deterministic. Figures render with the Agg backend and are
byte-identical across runs. Manuscript variables are injected — they are never
hand-authored in prose.
