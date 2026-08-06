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

What the package does *not* establish is equally worth stating. Every number
here is produced by the model at one canonical parameter set; none is a
measurement of a real operation. The success curve's sensitivity, the detection
rate, and the learning rate are chosen, not fitted — but the analysis in
`03_results.md` now reports over which sub-range of each the two headline
conclusions still hold, so the reader can see that the remount-improvement
result is robust to the logistic's steepness while the campaign-still-pays
result is conditional on the detection rate staying below about
{{SENS_DETECTION_RATE_ROBUST_HI}}. The conclusions are therefore claims about
this model's behaviour — reproducible to the byte, robust where the analysis
shows them to be, and open to being falsified by anyone who reruns it — rather
than claims about the world. The full list of bounds is in the scope section.
