# Packet 2B4 body-hit review - 15 September 2026

Result: body-hit observation, ITR event emission and incoming melee are supported by this capture. Successful reload and handler registration are recorded, but there are no hits afterward. Keep version 203 installed for one small follow-up check; no new implementation or installation is needed for it. Damage replacement remains disabled.

## Evidence

Archive: `captures/2026-09-15-2B4-625390c0d3ad/`. NVOCombatCore.log SHA256: `625390c0d3adbb40baaa8ced9576990c5d4c7edf5568e08a7a873c8005029384`. Original file timestamp: 15 September 2026, 08:13:08 local. The adjacent analysis.json records raw parsed streams, source metadata, the user's notes, form lookups and checks.

User reports one VATS use, anti-materiel rifle, assault carbine, Esther and dynamite, with all targets alive. God-mode status was not specified. Record VATS use as user evidence; this packet does not tag VATS, so individual rows cannot be assigned to it or used to certify VATS parity.

## Observations

- Version 203 loaded. JIP copy/ammo guards passed and both ITR handlers registered and emitted events.
- Session 1 has 600 consecutive provider rows, 87 valid copy-input contexts, 85 ITR hit-input rows and 83 ITR prehealth rows. Context/input sequences are also consecutive. No invalid contexts, invalid argument contracts or read failures were reported.
- Hit inputs comprise 56 player-to-actor, 25 actor-to-player and four self inputs. Body-part indices 0, 1, 3, 5, 7 and 10 occur, plus two Weapon-region 14 hits and 15 unspecified-region inputs. This is raw engine body-part evidence, not internal-organ localization.
- Two incoming sledgehammer hits from Chomps Lewis are present in both copy and ITR streams, with null carriers and no invented projectile/ammo link. This supplies a valid incoming melee example. Outgoing melee is not shown.
- Four creature inputs resolve to Snuffles. These support a biological creature example, not robot damage. There are no actor-to-actor inputs excluding the player.
- Sixty-eight contexts have projectile lifetime and ammo links, all agreeing with their creation ammo snapshots. Known examples include the anti-materiel rifle and assault carbine. Thrown dynamite has an unknown ammo snapshot; it is not silently assigned weapon-selected ammo.
- The independent streams continued after provider text reached its cap: another 48 copy contexts, 46 hit inputs and 45 prehealth inputs. At preload, projectile bookkeeping totals 221 creations, 212 impacts and 221 destructions, with no unmatched lifetimes, live-address reuse, overflow or outstanding lifetimes. The printed lifetime trace also matches independently.
- A second load succeeds. CAPTURE and DAMAGE_EVENTS_READY are emitted for session 2, with counters reset. All session-2 event/context/input totals remain zero before exit. The user subsequently confirmed no shots were fired after reload, explaining the empty second session. This establishes re-registration; post-reload hit delivery remains unexercised, not a demonstrated failure.

## Damage-stage information

Using an explicitly limited proximity rule (one health row before the next hit row, same source/target/session and at most 50 ms later), 83 hit inputs have a unique candidate health input. The two unpaired hit inputs are both Weapon-region hits.

For those candidate pairs, the absolute health-input magnitude is approximately 2 times the hit input for 54 outgoing player hits, and 0.5 times for 25 incoming hits and four self hits. This shows why these observation stages must not be treated as interchangeable. Existing difficulty/settings or other processing may account for the scaling; the capture does not identify its owner. No NVO damage multiplier is applied by this diagnostic build. Do not sum the streams, call this duplicate damage, infer final HP loss, or change game settings during log review.

The original copy observer now reports normal body and melee contexts as well as the added ITR stream. The prior capture's lack of those contexts alone was not proof that the copy observer was broken.

## Minimal remaining user check

Use the existing 203 build. Load a test save, then choose Pause -> Load to load it again in the same running game. Wait about three seconds. With god mode off, make one shotgun hit and one fist/knife hit on living targets (use another target if one dies). Exit and send the game-root NVOCombatCore.log before launching again. This targets post-reload emission, shotgun context and outgoing melee without repeating the rifle/explosive session.

Broader items such as robot damage, NPC-to-NPC, identified VATS paths, pellet completeness and exactly-once committed damage remain later validation work before damage authority. No new packet was prepared or installed during this review. Only workspace documentation and archived evidence changed; no game, GECK or build was run by the assistant.
