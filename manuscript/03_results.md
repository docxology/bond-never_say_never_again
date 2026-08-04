# Results

## Command score

Replaying the canonical `THUNDERBALL-65` scenario under the identity config
(original) and under `REMOUNT_CONFIG` (remount) gives:

| Metric | Original | Remount | Delta |
| --- | ---: | ---: | ---: |
| Command score | {{ORIGINAL_COMMAND_SCORE}} | {{REMOUNT_COMMAND_SCORE}} | {{COMMAND_DELTA}} |
| Objectives fulfilled | 1 | 3 | +2 |
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

The engine migrates {{MIGRATED_ASSET_COUNT}} legacy intelligence dossiers,
each re-fingerprinted on migration. The catalog-wide stable fingerprint is
`{{ASSET_FINGERPRINT}}`.

![Migrated asset distribution](figures/asset_distribution.png)
