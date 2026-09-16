# Packet 2A capture review — 14 September 2026

**Result: event capture works for the observed weapons. The full diagnostic checkpoint is still incomplete.** No logger changes are needed to gather the missing shotgun example. No native damage authority is enabled or validated.

The user supplied the installed `NVOCombatDiagnostics.log`. A byte-for-byte workspace copy is preserved in `captures/2026-09-14-eba863e72d.log`; parsed counts and locally resolved forms are in the adjacent JSON. SHA-256: `eba863e72d70536968c60b9fcefbaf15a931d19ad68403e85837255532e0b743`.

## Observed coverage

The log contains a single capture header and consecutive event numbers 1–243: 88 CREATE, 87 IMPACT, 61 HIT and 7 EXPLOSION rows. It ends below the configured 300-row allowance, so this capture does not demonstrate the automatic cutoff or reload behaviour.

Of the 61 HIT rows, 29 target the NPC from the player and 32 target the player. There is no NPC-to-NPC example. These are callback counts, not counts of distinct attacks or applications of damage.

Weapon identities were resolved read-only from the installed FalloutNV.esm. No matching overrides were found in the inspected NVO.esm; this does not rule out runtime changes from other components.

| Weapon | Form ID | HIT rows |
|---|---|---:|
| Laser Pistol | 00004335 | 10 |
| Service Rifle | 000E9C3B | 28 |
| Knife | 00004334 | 12 |
| Dynamite | 000BA0F3 | 11 |

The other actor resolves to Private Kowalski (base 0011A8D8, reference 0011A8D9). CREATE ammo snapshots resolve to energy cells for the laser pistol and 5.56mm rounds for the service rifle. Dynamite reports its weapon form as current ammo. No shotgun is represented. VATS use cannot be established by this logger, and there is no robot target.

Body-region readings include -1, 0, 1, 3, 5, 7, 10 and 14. These demonstrate varied raw region reporting, not internal-organ resolution. Unknown region -1 appears in melee/explosion records and must remain an explicit unknown.

## Findings relevant to native implementation

1. **Reference IDs are reused.** There are 88 CREATE records across only seven projectile reference IDs. For example, FF001988 describes the player's laser at rows 10–12 and the NPC's rifle bullet at rows 13–15. Track each creation/lifetime independently; do not use a reference ID alone as a session-wide shot identity. One fewer IMPACT than CREATE is not, by itself, evidence of a failed handler.

2. **HIT data can repeat around explosion events.** Row 203 repeats row 173's prior dynamite hit before a new explosion at 204. Rows 230/205 and 238/232 show similar repeated readings. Row 171 still reports the knife while current source ammo is dynamite, immediately before an explosion. These patterns are consistent with callbacks exposing older last-hit state; the log cannot distinguish that conclusively from other event behaviour. They do not prove damage was applied twice. The native checkpoint needs a verified current hit context and attack/lifetime association, rather than treating every JIP callback as a fresh hit or deduplicating on equal values.

3. **Distance readings are not complete flight measurements.** 74 of 87 IMPACT rows have distance_raw=0, including non-laser examples. A zero must not be interpreted as a measured point-blank shot. Native projectile flight will need its own validated position/distance tracking. Laser travel and ordinary projectile travel must retain distinct handling.

4. **Player damage readings change to zero.** The first five player-target HIT rows report hit_hp=1.006. From event 115 onward, the remaining 27 player-target rows report zero health, limb and base-weapon damage, despite positive projectile or explosion readings elsewhere. The user subsequently confirmed enabling god mode for infinite ammo. That is consistent with the zero incoming-damage readings; the exact toggle time is not logged. Treat the invulnerable portion as event-coverage evidence only, not a player-damage calibration or NVO damage bug. No HP settings need changing for this review.

5. **Impact and blast are separately visible.** Dynamite creates a projectile/impact record, then explosion callbacks report each affected actor. The engine armour flag varies on some dynamite HIT rows. This validates capture of those fields only; it does not validate NVO penetration logic, exact damage attribution or equal health loss across actors.

## Next small check

Request a short shotgun capture to observe pellet events, preferably with a normal outgoing bullet hit in the same capture. God mode can remain on for this outgoing pellet-observation check; ordinary incoming damage must eventually be checked with it off. No revised files or GECK changes are needed. Preserve each log before loading another save. Do not repeat the full playtest.

The user handles gameplay testing. This review only read/analyzed supplied data and plugin record identities and preserved evidence in the workspace. No game, GECK, compiler or automated tests were run. Native project/toolchain work, damage replacement, ballistics and injury implementation have not been started by this review. Ask before beginning the next implementation packet.
