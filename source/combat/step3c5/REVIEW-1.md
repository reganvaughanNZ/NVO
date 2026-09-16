# Packet 3C5 / 310 - user flight test accepted

**Accept this limited two-weapon, non-VATS flight checkpoint. The prior local-Z loss is corrected in these observations.** This is not blanket acceptance of all projectile types or final physical calibration.

Archived game-root NVOCombatCore.log under `captures/2026-09-15-3C5-da21de37bf4f/NVOCombatCore.log`: SHA256 `da21de37bf4f35d5330c29084c54c80ec5c76e9903f7878e285984ad55ccbf82`, 50,833 bytes, 228 lines, last write 2026-09-15T15:52:45.456926 local. Archive read was stable and the log ended with normal exit. `tools/review_combat_3c5.py` parses the evidence, verifies pairing/counts, and independently compares the rounded logged intended/actual vectors. Details in review-data.json.

## Outcome

One successful load, rifle then pistol, private weapons/ammunition/projectile bases correctly identified. Both hit scenery 00106B5E, with one matched impact and destruction apiece. Reuse of dynamic reference FF001993 occurred after destruction, not concurrently.

| Evidence | Hunting rifle | 9mm pistol |
|---|---:|---:|
| Unchanged baseline matches | 1 | 1 |
| Edited free-flight steps matched | 2 | 8 |
| Edited collision segments | 1 | 1 |
| Controller entry/return pairs | 4 | 10 |
| Reset branch observed | 4 | 10 |
| Reset skipped for applied vector | 3 | 9 |
| Pending calls at destruction | 0 | 0 |

There were 12 movement-input edits. Ten were free-flight segments and all passed the unchanged actual-displacement tolerance. Each projectile's final edited segment encountered collision and was correctly excluded from free-flight comparison: the engine truncated movement at the obstacle. The 12 applied versus 10 verified counts are therefore explained, not missing verification of freely travelling segments.

Maximum logged vector error across applied free flight was 0.00918273231 engine units; the highest error/tolerance ratio was 0.198856. Position-accounting error was zero in the verified rows. Omitting local Z would exceed tolerance in 10 of the 10 applied free-flight samples. The new branch preserves the intended component with a measurable effect on actual motion.

## What this establishes

All 14 observed controller calls dispatch through vtable 01090594 to C73170. PHYSICS_LOCAL_Z confirms that C73517's reset branch actually executes. Baselines replay it; all 12 edited requests preserve their already-copied local vector. Request values match submitted input and remain unchanged after controller return. The checked frame/stack/identity/timestep/rotation contracts succeeded in these samples. Actual movement now matches the full integrated vector, rather than the old omission pattern.

The independent timing observer reports 16 samples: two startup/no-motion, 12 moving (including two baselines), and two collisions. Movement speed decreases during flight while base speed/multiplier remain unchanged, consistent with NVO's displacement-based drag. Model endpoint speed is not itself an independent engine velocity measurement. Logged m/s values still assume the configured 70 engine units per metre.

No reported rejection, mismatch, read/identity failure, unpaired accounting, overflow, live address reuse, nesting/overlap or log cap. No open projectile lifetimes or pending controller calls at exit. All updates used one worker thread distinct from the initialization thread; that is permitted by the existing per-lifetime handling, not an error. Damage authority remained disabled and the scenery test produced no actor damage contexts.

## Remaining limits and next check

This run contains one load and no new reload, VATS, NPC firing or stress coverage of the correction. Keep the existing 310 build for a short reload/VATS regression before wider ammunition coverage or tracer changes. Ask the user before giving that next checkpoint; no new DLL/GECK work is required merely to obtain those observations.

The intentional first unchanged segment per lifetime remains a pilot limitation. Unit scale, cartridge tuning and fixed atmosphere are not independently calibrated by this run. Collision-step trajectory/energy at the exact impact time is not validated by free-flight matching; do not substitute commanded engine travel counters or the cached pre-collision speed for a future penetration calculation without resolving that distinction.

Review only: archived evidence and checkpoint documents/tools. No native edits, build, install, game launch, GECK work, gameplay or process-memory access. Installed version 310 and user test files remain unchanged. The additional donor review is separate and did not activate those mods.
