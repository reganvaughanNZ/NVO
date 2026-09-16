# Repeated playtest: ordinary flight checks pass; terrain correction unexercised

The newest log contains 20 shots across five loaded sessions, four reloads and a normal exit. There are no displacement errors, but also no failed terrain queries or corrections. This run does not reproduce the original failure or validate the specific 3F2 correction.

The user declined the proposed fixed-position fixture and repeated the test instead. Respect that decision: no fixture was prepared, and no further blind aiming repeat is requested.

## Archived evidence

- Capture: `captures/2026-09-15-3F2-d456dd06d026/NVOCombatCore.log`
- SHA256: `d456dd06d0268787b49ea353949b3536283e855c62a496dd97f4891f7419c125`
- Size: 1,135,729 bytes / 4,808 lines
- Last write: 2026-09-15T20:34:09.684379+12:00
- Version: native 313 / 0.3.13 / phase 3F2
- Supporting files in the capture directory: `capture.json`, `audit.json` and `review-data.json`

`tools/audit_flight_capture.py` verifies the archived hash, corroborates shot identities, checks detailed movement vectors and collects lifecycle/error counters. This reusable offline helper replaces another capture-specific analysis script. Its output is evidence, not automatic acceptance of a gameplay checkpoint.

## Results

All 20 shots match at selection, preview and creation: ordinary Hunting Rifle `00004333`, standard .308 ammunition `0006B53C`, private projectile `0C000807`. There are 20 creations, 16 impact callbacks and 20 destructions, with no open lifetimes at exit. Five linked actor-hit lifetimes are 1, 6, 11, 12 and 14; all retain the creation ammunition and weapon identity.

| Logged checkpoint | Result |
|---|---:|
| Eligible terrain queries | 401 |
| Failed terrain queries | 0 |
| Terrain corrections | 0 |
| Verified corrected movements | 0 |
| Verified baselines | 20 |
| Reported verified edited movements | 385 |
| Edited movements independently checked from detailed rows | 324 |
| Displacement mismatches | 0 |

The routine detail cap omits 61 later edited comparisons. Aggregate counters report them as verified, but the archive cannot independently demonstrate those omitted vectors. All 20 baseline detail comparisons pass. The logged movement/accounting total is 421, consisting of 405 free-flight comparisons and 16 collision exclusions. No native rejection/disable rows, identity failures, invalid timing/context, unpaired accounting, overflow, read failures or open-lifetime failures were found in the audit.

## Why the final misses are still inconclusive

The final four projectiles had no impact callbacks. They survived about 1.35 seconds and travelled just beyond the logged base projectile range of 53,000 engine units:

| Lifetime | Age at destruction (seconds) | Travel (engine units) |
|---|---:|---:|
| 17 | 1.360 | 53,406.6 |
| 18 | 1.354 | 53,216.9 |
| 19 | 1.344 | 53,013.9 |
| 20 | 1.348 | 53,059.6 |

This is consistent with range expiry, but the log does not record the exact destruction reason or each projectile instance's range. In contrast, the original 3F1 VATS miss reached the displacement failure at about 5.846 seconds and was destroyed at about 8.023 seconds after travelling approximately 265,154 units. A VATS-related range difference is a hypothesis, not an established multiplier. The aiming mode of the final four shots is not explicitly recorded or supplied by the user.

The outside-VATS recheck instructions did not establish that the projectile could remain alive long enough to reach the original condition. That is a limitation of the requested check, not evidence that the user performed it incorrectly. See `RANGE-LIFETIME-FINDINGS.md` for the bounded source audit and unresolved question.

## Decision and next boundary

Ordinary flight and reload checks pass within the logged evidence. The failed-terrain correction remains **unexercised**, not accepted. Keep native 313 and the current records/configuration. No game, native source, DLL, plugin record, configuration, activation or save changed during this review; no assistant gameplay was performed. Damage authority remains off.

Do not repeat RECHECK-1 or request another ammo cycle. Do not prepare the declined fixture. The next useful packet would add narrowly scoped per-instance range/lifetime evidence at existing observation points, after verifying the field and relevant engine handling. Its purpose is to explain the shorter flight before defining another user test. Ask before preparing that packet. Do not extend projectile range, weaken tolerances or claim a VATS multiplier without supporting evidence.
