# Results

## Command score

Replaying the canonical `{{SCENARIO_NAME}}` scenario under the identity config
(original) and under `REMOUNT_CONFIG` (remount) gives:

| Metric | Original | Remount | Delta |
| --- | ---: | ---: | ---: |
| Command score | {{ORIGINAL_COMMAND_SCORE}} | {{REMOUNT_COMMAND_SCORE}} | {{COMMAND_DELTA}} |
| Objectives fulfilled | {{ORIGINAL_FULFILLED}} | {{REMOUNT_FULFILLED}} | {{FULFILLED_DELTA}} |
| Overall verdict | — | — | *{{OVERALL_VERDICT}}* |

The remount raises the weighted command score from {{ORIGINAL_COMMAND_SCORE}}
to {{REMOUNT_COMMAND_SCORE}}, a weighted delta of {{COMMAND_DELTA}}. Per
objective, {{NUM_IMPROVED}} improve, {{NUM_REGRESSED}} regress, and
{{NUM_UNCHANGED}} are unchanged.

## Figure: original vs remount

![Op diff — original vs remount objective scores](figures/op_diff_scores.png)

The grouped bar figure (rendered by `src/never_say_never_again/figures.py`
into `output/figures/op_diff_scores.png`) shows each objective's score under
the original and remount configs. The remount's reinforced intel pushes every
objective's score upward.

## Legacy asset migration

The engine migrates {{MIGRATED_ASSET_COUNT}} legacy intelligence dossiers
({{MIGRATED_ASSET_KINDS}}), each re-fingerprinted on migration. The
catalog-wide stable fingerprint — the SHA-256 over the sorted
`(id, kind, content-digest)` rows, truncated for display — is
`{{ASSET_FINGERPRINT}}`. Migration is refused outright when a source dossier's
declared fingerprint does not match its content, so a tampered legacy record
cannot silently enter the remount.

![Migrated asset distribution](figures/asset_distribution.png)

## Remount risk

Over a campaign of {{RISK_CAMPAIGN_LENGTH}} replay operations at a per-replay
hazard of {{RISK_DETECTION_RATE}}, the accumulated detection probability
reaches {{RISK_DETECTION_PROBABILITY}} (expected
{{RISK_EXPECTED_OPERATIONS}} operations before the first alert), whereas the
block-structured mission reliability is {{RISK_RELIABILITY}}. At the canonical
reward {{RISK_CAMPAIGN_REWARD}} and penalty {{RISK_CAMPAIGN_PENALTY}} the
campaign expected value is {{RISK_CAMPAIGN_EV}}.

The sign of that expected value is the whole argument. The model's own
crossing — the smallest replay count at which the expected value turns
non-positive — is {{RISK_EV_CROSSING}} for the canonical parameters; the
canonical campaign length of {{RISK_CAMPAIGN_LENGTH}} sits comfortably below
it, which is what "keep the remount short" means in numbers. Reliability is a
*constant* of the mission's block structure, while the detection term
`1 - exp(-rate * N)` rises monotonically in the replay count `N` toward 1. The
expected value is therefore strictly decreasing in `N`, and it crosses zero
once `reliability * reward` falls below `detection * penalty` — with the
canonical reward and penalty equal, simply once the accumulated hazard exceeds
the reliability. Past that crossing every additional replay is negative-value.
Both properties (strict decrease, and a crossing at the canonical parameters)
are asserted over the real model in `tests/test_remount_risk.py` rather than
argued in prose alone. This is the engine's central caveat to the remount
premise: *never say never again* — but do not keep saying it into a long
campaign.

## Asset allocation

Allocating the scarce remastered assets by marginal gain spends a budget of
{{ALLOC_BUDGET}} across {{ALLOC_OBJECTIVE_COUNT}} objectives. The greedy
deploys {{ALLOC_ASSETS_USED}} of them — it stops early if every objective
saturates — and recovers {{ALLOC_TOTAL_GAIN}} of weighted command score, i.e.
{{ALLOC_GAIN_RATIO}} of the full-saturation ceiling.

That figure is in genuine command-score units: the allocatable objectives carry
the scenario's own ids and weights, and each one's zero-asset base score *is*
its score in the remount replay reported above, so the plan's zero-asset
baseline is the remount command score {{REMOUNT_COMMAND_SCORE}} — displayed
here rounded, asserted at full precision in `tests/test_asset_allocator.py`
rather than left to the reader. What the allocation model stipulates, and what
no data here calibrates, is the pair of curve parameters per objective — how
much an asset can ultimately buy and how fast the returns diminish.

Because each objective's improvement curve is concave, the sequence of realized
marginal gains is non-increasing: the greedy spends its first asset where the
slope is steepest and each later asset buys strictly less. For this
separable-concave objective that makes the greedy exactly optimal, not merely
within the `(1 - 1/e)` factor of the general submodular bound — checked in
`tests/test_asset_allocator.py` against the maximum over every feasible split
of the budget, with the unweighted-selection variant failing the same check.

![Marginal-gain asset allocation](figures/asset_allocation.png)

## Replay learning curve

Forecasting repeated rehearsal at learning rate {{LEARN_RATE}} over
{{LEARN_ITERATIONS}} iterations raises the command score from
{{LEARN_INITIAL_SCORE}} toward {{LEARN_FINAL_SCORE}} (delta {{LEARN_DELTA}}),
and the target score of {{LEARN_TARGET_SCORE}} is first met at iteration
{{LEARN_TARGET_ITERATION}}.

The asymptote is not an assumption: it is a second real replay of the same
scenario under a fully-reinforced config (intel bonus {{LEARN_BONUS_CAP}}), so
both ends of the curve are computed by the engine rather than posited. A target
at or above that asymptote is reported as unreachable rather than as met on the
first iteration — the curve approaches its asymptote but never attains it.

![Replay learning curve](figures/learning_curve.png)

## Sensitivity and robustness

The two headline conclusions above are each asserted at one sweep of a
parameter, not at a single point. `src/never_say_never_again/sensitivity.py`
sweeps each of the three parameters the conclusions rest on and reports the
largest contiguous sub-range containing the canonical value over which *both*
conclusions — remount improved [[`(a)`]] and campaign still pays [[`(b)`]] —
hold:

| Parameter | Sweep | Robust sub-range | Notes |
| --- | --- | ---: | --- |
| Success sensitivity `S` | {{SENS_SWEEP_SENSITIVITY}} | [{{SENS_SENSITIVITY_ROBUST_LO}}, {{SENS_SENSITIVITY_ROBUST_HI}}] | conclusion (a) holds across the whole declared sweep ({{SENS_SENSITIVITY_SPANS}} = spans) |
| Detection rate | {{SENS_SWEEP_DETECTION_RATE}} | [{{SENS_DETECTION_RATE_ROBUST_LO}}, {{SENS_DETECTION_RATE_ROBUST_HI}}] | conclusion (b) breaks at high rate ({{SENS_DETECTION_RATE_SPANS}} = spans) |
| Learning rate | {{SENS_SWEEP_LEARNING_RATE}} | [{{SENS_LEARNING_RATE_ROBUST_LO}}, {{SENS_LEARNING_RATE_ROBUST_HI}}] | affects neither (a) nor (b) ({{SENS_LEARNING_RATE_SPANS}} = spans) |

![Sensitivity sweep — robust parameter sub-ranges](figures/sensitivity_sweep.png)

Interpretation. The remount-improvement conclusion is *not* a knife-edge of the
logistic steepness: it holds across the entire declared sensitivity sweep,
because the remount config raises effective intel on every objective regardless
of `S`. The campaign-still-pays conclusion is genuinely conditional: beyond a
detection rate of about {{SENS_DETECTION_RATE_ROBUST_HI}} the accumulated
hazard crosses the mission reliability within the canonical campaign length,
and the expected value turns negative — so "keep the remount short" depends on
the adversary's per-replay acuity. The learning rate, by construction, fights
neither battle, and the analysis says so rather than pretending it does.

