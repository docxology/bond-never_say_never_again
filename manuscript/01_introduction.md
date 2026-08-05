# Introduction

## Never Say Never Again and the remount battalion

*Never Say Never Again* (1983) is a curious entry in the Bond canon: it is a
remake — a *remount* — of *Thunderball* (1965), produced without the Eon
series and starring a returning Bond. Rather than a new story it re-stages an
old one, modernized and re-equipped. This is precisely the operational meaning
of a **legacy mission remount**: keep the objective set, refresh the resources,
and re-run the scenario against the current threat model.

REMOUNT ({{MISSION_CODENAME}}, package {{PACKAGE_VERSION}}) operationalizes
that idea as software for {{FILM_IDENTITY}}. Its pure domain core provides six
capabilities, each a separate module:

1. **Legacy mission replay** (`mission_replay.py`) — deterministically re-run a
   prior operation's scenario under a remount configuration.
2. **Op diff** (`op_diff.py`) — compare the original outcome against the
   remount, per objective and in aggregate.
3. **Legacy asset migration** (`legacy_assets.py`) — carry forward,
   re-fingerprint, and verify the intelligence assets the remount consumes.
4. **Remount risk** (`remount_risk.py`) — price the re-op: the detection hazard
   that accumulates across replays, the block-structured mission reliability,
   and the resulting campaign expected value.
5. **Asset allocation** (`asset_allocator.py`) — spend a scarce budget of
   remastered assets across objectives by marginal gain.
6. **Replay learning** (`learning_curve.py`) — forecast how far repeated
   rehearsal can push the command score, and when it stops paying.

The first three answer the operative question of any re-op: *is the remount
actually an improvement, and can we trust the intel it relied on?* The last
three answer the question that follows immediately: *and is it worth running at
all, given what a replay costs and what rehearsal can still buy?* A remount
that improves the command score can still be a bad operation if the accumulated
detection hazard outweighs the gain — so the engine reports both halves rather
than only the flattering one.

## Why determinism

A remount is an audit as much as an operation. Every number produced —
command score, objective delta, asset fingerprint — must be reproducible by an
independent reviewer without re-running the whole suite. The engine therefore
makes **no random draws and no external calls**: its success model is a fixed
Logistic curve, its hashing is canonical SHA-256, and two runs under the same
inputs are byte-identical.
