# 3F3 review: failed-terrain correction exercised and accepted

The second tracked shot reproduced the failed-terrain condition during a long miss. The engine reported 653 corrections followed by 653 successful independent movement-accounting checks, with no displacement mismatches. The first 16 correction/verification pairs are individually logged and checked. This satisfies the previously pending 3F2 terrain-correction checkpoint for the observed private Hunting Rifle projectile. The 3F3 range diagnostics also functioned without optional-read or log failures.

The user reported many VATS hits and early misses. Exact aiming mode for each shot was not supplied; the log does not directly label it. No additional reproduction test is requested.

## Evidence

- Capture: `captures/2026-09-15-3F3-3130ae056efd/NVOCombatCore.log`
- SHA256: `3130ae056efdf379d4720fb6b2837447fa9d8e600255860107fbe28c2c50ac0c`
- Size: 535,838 bytes / 2,262 lines
- Last write: 2026-09-15T21:23:37.881110+12:00
- Native version 314 / 0.3.14 / phase 3F3
- Supporting files: capture.json, audit.json and review-data.json in the capture directory

The archived log was stable across two reads and ends with normal exit. `tools/audit_flight_capture.py` validates its hash and correlates shot/range/hit identities, detailed flight comparisons and correction pairs. The helper now distinguishes live projectiles at a reload boundary from unexplained open lifetimes at exit; the boundary evidence remains explicit for review.

## Shot and reload accounting

There were nine ordinary Hunting Rifle shots, all standard .308: weapon 00004333, ammo 0006B53C, private projectile 0C000807. Selection, creation and range observations agree for all nine. There were two loaded sessions and one reload.

| Lifetime | Result |
|---|---|
| 1 | Still flying at reload after 145 verified edited steps; no pending movement/controller update |
| 2 | Long miss, no impact callback; 967 edited steps verified, including all 653 corrected steps |
| 3, 6, 9 | Impact reference 00104FB0 |
| 4, 5, 7 | Impact reference 001070C1, previously identified as a mobile-home trailer |
| 8 | Linked actor hit on FF001978, body region 0; actual final health application remains unverified |

Seven impact callbacks and eight destructions were recorded. The first shot's missing destruction is explained by reloading while it remained active. The pre-load summaries report one open lifetime consistently across observer/physics/timing/preview, no pending updates or unmatched accounting. The source's suspend path clears those tables; the second session starts fresh and ends with zero open lifetimes, no stale-identity or reuse failures. This is a successful transient-state reset, not an observed exit leak.

Do not equate seven impacts with seven verified live-actor wounds: only lifetime 8 has a full linked HIT_CONTEXT. This does not invalidate the flight/terrain checkpoint, but it is not a multi-hit damage validation.

## Terrain correction and movement

Across both sessions: 1,143 eligible terrain queries, 1,087 failed queries, 653 corrections and 653 verified corrected movements. Failed queries are corrected only when the guarded conditions require preventing the invalid height raise. There were zero correction collisions excluded, zero correction log failures and no PHYSICS_REJECT or PHYSICS_DISABLED rows.

All corrections occurred on lifetime 2 in session 2. The first detailed pair at step 315 reports:

- Query failed and returned the default height -2048.
- Calculated candidate Z: -2166.50317; the prevented rise was 118.503174 engine units.
- Candidate/movement vector error: 0.00755687332 against tolerance 0.0710064977.
- Post-movement actual Z: -2166.50317; position error zero.
- Only the stack height result was changed; query return preserved, no direct position write.

The remaining 15 logged pairs, steps 316-330, also retain the candidate height and pass both error bounds. The summary's 653 verified corrections is incremented only after fresh displacement/position reads and the existing matching check; collisions and failed comparisons cannot increment it. Details after the first 16 are capped, so those later 637 pairs cannot be independently reconstructed from individual log rows.

Overall, 1,152 movement/accounting observations balance as nine baselines, 1,136 verified edited movements and seven collision exclusions. Detailed ordinary rows independently support nine baselines and 150 edited vectors; the remaining 986 edited vectors are represented by aggregate counters, with the separate 16 correction-pair rows providing additional evidence. No displacement, identity, overflow, invalid-context/timing or accounting failures were found.

## Range result

All nine launch observations record a base range of 53,000 and an instance firing range of 265,000 engine units: a ratio of five for these shots. All available ending observations retain the same instance range. All 24 range rows have full validity masks; both range summaries report zero optional-read and log failures.

Lifetime 2 was destroyed at engine age 16.9785633 seconds after travelling 265,104.75 units, just beyond its observed 265,000 limit. No impact was observed. This strongly supports range expiry for this shot, while the exact destruction cause remains explicitly unverified by the current instrumentation.

The observed five-times range corroborates the longer-flight explanation and the choice of Projectile +0xD4 for telemetry. It is not proof of a universal VATS multiplier: saved source identifies a conditional aiming-related range multiplier, and this run contains no separately confirmed one-times hip-fire control. No such control repeat is necessary to accept the terrain correction.

## Decision and next boundary

Accept the failed-terrain correction and the range-observation checkpoint within this test's scope. Keep native 314 and current records/configuration. No game/native code/configuration/save was changed during this review and no assistant gameplay occurred. Do not request another miss reproduction, build the declined fixture or repeat the ammo cycle.

The next proposed packet is read-only impact-speed diagnostics: establish the projectile's speed at the actual impact, with explicit treatment of the first unchanged movement and collision timing, before armour calculations use it. Inspect existing impact callbacks and timing ownership first; do not silently substitute last free-flight speed for exact contact speed. Cartridge mass, physical unit calibration, ammo-specific flight tuning, energy, penetration and damage authority remain subsequent work or explicit dependencies. Ask the user before preparing that packet. RD master removal and HP selection persistence remain separate follow-ups.
