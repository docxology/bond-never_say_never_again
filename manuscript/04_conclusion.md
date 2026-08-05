# Conclusion

REMOUNT ({{MISSION_CODENAME}}) demonstrates a clean, deterministic answer to
the legacy-mission re-open: re-run the scenario, diff the outcomes, and migrate
the intel. For the canonical `THUNDERBALL-65` remount the evidence is
unequivocal — the remount improves the weighted command score from
{{ORIGINAL_COMMAND_SCORE}} to {{REMOUNT_COMMAND_SCORE}} (delta
{{COMMAND_DELTA}}, verdict *{{OVERALL_VERDICT}}*) and migrates
{{MIGRATED_ASSET_COUNT}} assets with verified fingerprints.

Three lessons carry forward to any remount battalion:

1. A remount improves outcome when intel reinforcement outpaces difficulty.
2. Op diffs must weight objectives by their relative importance, not treat
   them equally.
3. Legacy assets must be re-fingerprinted before remount consumption — you
   cannot trust a dossier you never re-verified.

The deepened models add three more. A remount is not free: the accumulated
detection hazard over {{RISK_EXPECTED_OPERATIONS}} expected operations
({{RISK_DETECTION_PROBABILITY}} at campaign length) makes the campaign expected
value {{RISK_CAMPAIGN_EV}} and *falling* as replays grow — so the remount must
be decisive, not serial. Scarce remastered assets should follow marginal gain
({{ALLOC_ASSETS_USED}} assets for {{ALLOC_GAIN_RATIO}} of the saturation
ceiling) rather than intuition. And rehearsal follows a diminishing-returns
learning curve toward {{LEARN_FINAL_SCORE}} (delta {{LEARN_DELTA}}, target at
iteration {{LEARN_TARGET_ITERATION}}), so the marginal replay eventually stops
paying.

The engine's determinism makes every one of these claims independently
auditable, and its purity (no `bond_api` imports in the domain core) keeps the
analysis reusable beyond the BOND suite.
