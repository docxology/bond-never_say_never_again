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
leaves {{NUM_UNCHANGED}} unchanged. The engine migrates
{{MIGRATED_ASSET_COUNT}} legacy intelligence dossiers, re-fingerprinting each
(SHA-256) so the remount can verify integrity before consumption
(fingerprint {{ASSET_FINGERPRINT}}).

Everything computes deterministically — no random draws, no external calls — so
the remount is reproducible to the byte on Python {{PYTHON_VERSION}} (generated
{{GENERATION_TIMESTAMP}}).
