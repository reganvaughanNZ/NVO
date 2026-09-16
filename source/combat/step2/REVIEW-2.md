# Packet 2A follow-up capture — 14 September 2026

**Result: accept Step 2A for initial event coverage.** This capture supplies outgoing ordinary bullets and individually represented shotgun pellets. Combined with the first capture's melee and explosion examples, there is enough evidence to prepare the native observer. Step 2 as a whole is not complete; native hooks and damage authority remain unimplemented/unverified.

Archived capture: `captures/2026-09-14-2802886d34.log`. SHA-256: `2802886d345a835d80b6a0ccc2452d44668a0c16b505a6f1cb6469ec37734537`. Counts and locally resolved record identities are in the adjacent JSON. The installed log was read and copied into the workspace; no installed files were changed.

## Confirmed in this capture

- **300 consecutive event rows:** 120 CREATE, 119 IMPACT, 59 HIT and 2 EXPLOSION. The `END record limit reached` footer confirms the configured cutoff was reached. The last row is a HIT, so a subsequent impact may be outside the capture; the unequal total CREATE/IMPACT counts are not evidence of a missing hook.
- **Outgoing ordinary bullets:** the player fires weapon IDs 07000813 and 0700084E, with 5.56mm and 12.7mm current-ammo snapshots respectively. Each has CREATE, HIT and IMPACT examples. For instance, rows 54–56 track a bullet striking an NPC; rows 217–219 provide another example with a nonzero distance reading. Their weapon names were not resolved by the literal FormID lookup in FalloutNV.esm/NVO.esm. Do not guess their owning plugin without load-order mapping.
- **Shotgun pellet references:** the vanilla Single Shotgun (000E393B) produces 42 CREATE and 42 IMPACT rows using Buckshot (0003BF07) and 20 Gauge Round snapshots (000E86F2). Rows 66–72 show seven distinct projectile references created together, with their seven individual impacts at rows 79–85. Later rows 247, 249, 251 and 253 report hits from four distinct pellet references.
- **Shotgun direction:** all captured shotgun events originate from NPC 000E5A6A. Eight shotgun HIT rows target the player. This establishes incoming pellet-event coverage, not a player-fired shotgun damage test. The previously confirmed god-mode use makes the zero incoming damage readings unsuitable for damage calibration.
- **More actor contexts:** player hits include multiple human NPCs and Snuffles, a creature record. There are 32 player-to-other and 27 other-to-player HIT rows. No NPC-to-NPC HIT or robot example is present.
- **Fresh initialization output:** the new capture has one header and numbering begins at 1. This is consistent with a fresh initialization; it does not by itself establish duplicate-free handler registration across every reload scenario.

## Carry forward to native diagnostics

Keep the issues recorded in REVIEW-1: recycled reference IDs, possible stale last-hit readings near explosions, incomplete distance reporting and ammo snapshots that may differ from the actual shot's ammo. Distinct projectile references demonstrate separate pellet events, not independently verified applications of damage. Do not sum callback damage fields or assume similar rows can safely be discarded.

The next implementation should first establish the native build/load prerequisite, then obtain current hit context and distinguish each projectile lifetime. It must retain observation-only behaviour. NPC-to-NPC, robots, VATS, non-invulnerable incoming damage and exact damage-once behaviour remain checks for native validation before any damage replacement is enabled. These outstanding cases do not require repeating the same script capture now.

No further Step 2A source or GECK changes are needed. Ask the user before preparing Step 2B. This review performed data analysis and read-only plugin lookup; the assistant ran no game, compiler or automated tests.
