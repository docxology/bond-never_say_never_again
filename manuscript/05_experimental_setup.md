# Experimental setup

## Canonical dataset

The `{{SCENARIO_NAME}}` scenario (`src/never_say_never_again/mission_replay.py`)
is the sole canonical dataset, declared as module-level deterministic
constants. It contains {{NUM_OBJECTIVES}} objectives with fixed weights,
difficulties, and baseline intel, plus an identity config
(`intel_bonus = 0`) and the `REMOUNT_CONFIG` used for the remount. The
migration consumes a second canonical constant, `LEGACY_INDEX`:
{{MIGRATED_ASSET_COUNT}} legacy dossiers ({{MIGRATED_ASSET_KINDS}}).

## Parameters

Every value below is a generated token read straight from the constant the code
runs on — this list cannot drift from the implementation.

- Success-model sensitivity `S = {{MODEL_SENSITIVITY}}`, success threshold
  `{{MODEL_SUCCESS_THRESHOLD}}`.
- Remount intel bonus `{{REMOUNT_INTEL_BONUS}}`, doctrine
  `{{REMOUNT_DOCTRINE}}`, realism ceiling `{{REMOUNT_REALISM_CEILING}}`.
- Deterministic seed `{{MISSION_SEED}}` (provenance-only: the mission makes no
  random draws).
- SHA-256 fingerprints over NFC-normalized UTF-8 content.
- Risk: detection rate `{{RISK_DETECTION_RATE}}`/replay, campaign length
  `{{RISK_CAMPAIGN_LENGTH}}`, reward `{{RISK_CAMPAIGN_REWARD}}`, penalty
  `{{RISK_CAMPAIGN_PENALTY}}`, reliability blocks with
  `{{RISK_BLOCK_STRUCTURE}}` redundant paths respectively (intel acquisition,
  insertion, extraction).
- Allocation: budget `{{ALLOC_BUDGET}}` assets over
  `{{ALLOC_OBJECTIVE_COUNT}}` objectives (concave curves).
- Learning: rate `{{LEARN_RATE}}`, `{{LEARN_ITERATIONS}}` iterations, bonus cap
  `{{LEARN_BONUS_CAP}}`, target `{{LEARN_TARGET_SCORE}}`.
- Sensitivity sweep ranges: `{{SENS_SWEEP_SENSITIVITY}}` (success sensitivity),
  `{{SENS_SWEEP_DETECTION_RATE}}` (detection rate), and
  `{{SENS_SWEEP_LEARNING_RATE}}` (learning rate), each sampled at
  `{{SENS_SWEEP_STEPS}}` evenly spaced points.

All canonical numeric constants live in the domain modules
(`mission_replay.py`, `legacy_assets.py`, `remount_risk.py`,
`asset_allocator.py`, `learning_curve.py`, `sensitivity.py`), shared by the
mission adapter, the manuscript tokens, and the figures — no duplicated
numbers.
`manuscript/config.yaml` mirrors the same values for human readers, and
`tests/test_manuscript_variables.py` asserts the mirror matches the code, so a
constant changed in one place and not the other fails the suite.

## Fixtures and isolation

Tests use real data and computation only (no mock framework), with fixed inputs
so every outcome is deterministic. Figures render with the Agg backend and are
byte-identical across runs. Manuscript variables are injected — they are never
hand-authored in prose.
