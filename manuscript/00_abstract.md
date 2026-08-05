# Abstract

**{{PAPER_TITLE}}** ({{PAPER_SUBTITLE}}, version {{PACKAGE_VERSION}}) presents
REMOUNT, a deterministic engine for *legacy mission replay*. When an operation
is re-opened years after its original run, its scenario must be re-executed —
as a *remount* — with remastered intelligence, its outcomes compared against
the original, and its legacy assets migrated so they can be consumed safely
again.

Drawing on the 1983 film *Never Say Never Again* — itself a remount of the
1965 *Thunderball* operation ({{FILM_IDENTITY}}, mission codename
{{MISSION_CODENAME}}) — the engine models each of {{NUM_OBJECTIVES}} objectives
through a smooth success curve over effective intel versus difficulty. The
canonical replay yields an original command score of {{ORIGINAL_COMMAND_SCORE}}
and a remount command score of {{REMOUNT_COMMAND_SCORE}} (weighted delta
{{COMMAND_DELTA}}, overall verdict *{{OVERALL_VERDICT}}*). Per-objective, the
remount improves {{NUM_IMPROVED}} objectives, regresses {{NUM_REGRESSED}}, and
leaves {{NUM_UNCHANGED}} unchanged, lifting the count of fulfilled objectives from
{{ORIGINAL_FULFILLED}} to {{REMOUNT_FULFILLED}}. The engine migrates
{{MIGRATED_ASSET_COUNT}} legacy intelligence dossiers
({{MIGRATED_ASSET_KINDS}}), re-fingerprinting each (SHA-256) so the remount can
verify integrity before consumption (catalog fingerprint
{{ASSET_FINGERPRINT}}).

The remount is not costless. Replaying the op accumulates a detection hazard:
over a campaign of replay operations the probability of alerting the adversary
reaches {{RISK_DETECTION_PROBABILITY}} (expected {{RISK_EXPECTED_OPERATIONS}}
operations before alert), while the mission's block-structured reliability is
{{RISK_RELIABILITY}} — a campaign expected value of {{RISK_CAMPAIGN_EV}}. Scarce
remastered assets are therefore allocated by marginal gain
({{ALLOC_ASSETS_USED}} assets deployed, {{ALLOC_GAIN_RATIO}} of the saturation
ceiling), and repeated rehearsal pushes the command score along an exponential
learning curve toward {{LEARN_FINAL_SCORE}} (delta {{LEARN_DELTA}}, reaching
the target by iteration {{LEARN_TARGET_ITERATION}}).

Everything computes deterministically — no random draws, no external calls — so
the remount is reproducible to the byte on Python {{PYTHON_VERSION}} (generated
{{GENERATION_TIMESTAMP}}). Every quantity above is a token injected from the
running code; none is transcribed by hand. The models themselves are standard
and cited, not invented here: the contribution is their deterministic,
auditable composition into a single remount pipeline, evaluated at one
canonical parameter set rather than calibrated against operational data.
