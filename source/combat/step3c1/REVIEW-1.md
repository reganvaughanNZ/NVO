# Packet 3C1 review: bullet movement checkpoint works; matrix route is wrong for this test

User completed the requested two distant private shots outside VATS and exited. Read game-root NVOCombatCore.log directly, verified the source bytes stayed stable while archiving, and saved the capture under `captures/2026-09-15-3C1-b89761391038/`. SHA256 b89761391038367b314cf5b5b500e34ada83e241ad2a30d52aa44eaf292c3bd1; 25,364 bytes; 110 lines; last write 2026-09-15T13:07:12.258305 local. Header 0.3.6 / phase 3C1. One successful load and normal LIFECYCLE exit_game. Game was closed when reviewed.

## Captured results

| Evidence | Private Hunting Rifle | Private 9mm |
|---|---:|---:|
| Creation / impact / destruction | 1 / 1 / 1 | 1 / 1 / 1 |
| Timing updates | 6 | 11 |
| Free-flight updates | 4 | 9 |
| Calls at bullet movement checkpoint 009BF411 | 5 | 10 |
| Private identity accepted at matrix hook 00930255 | 0 | 0 |
| Applied native physics updates | 0 | 0 |

The movement checkpoint identifies both projectiles with exact private weapon/ammo/base matches. Its 15 entries correspond to 13 free-flight and two collision updates; the two initial no-motion timing updates do not enter movement. Both sampled movement frames pass the checked original parent return 009BF35D and vector pointer frame+0C. All eight bounded PHYSICS_MOVE_ENTRY rows have successful vector/counter reads. The input vector is forward-only (0, speed*dt, 0) as expected at this pre-rotation boundary.

PHYSICS_ROUTE_SUMMARY reports move_entries_all=15, move_untracked=0 and move_bad_stack=0. This independently confirms the new read-only bullet movement checkpoint is executing, including on update thread 22212 while initialization was on thread 2500.

The original matrix hook reports 27,661 active entries, **all rejected by the expected-caller filter**. No stack-bound failures or owner-read failures. The first eight bounded early examples show caller 008A633E rather than the expected missile caller 009BF416. Do not claim all 27,661 calls came from 008A633E: only those eight addresses were sampled. No call from the expected missile caller passed the filter, and neither private identity reached the integrator. Existing captured generic-movement code contains several conditional rotation routes; its EBX argument-frame register is assigned once in the prologue, and the new read-only wrapper preserves the original return. This evidence supports the conclusion that the chosen matrix route is inappropriate for the observed private bullet movement. It does not identify the precise alternative internal branch or certify a replacement world-vector write point.

Both PHYSICS_NO_UPDATE notices correctly diagnose zero-update lifetimes. PHYSICS_ARMED is not proof of execution. PHYSICS_STEP remains absent; applied_steps=0. Free-flight speed stays within 0.0007492% of the original settings. No new gravity/drag acceptance.

All private timing/physics/preview lifetimes close. No unmatched callbacks, active-table overflow, reused live address, invalid timing, overlap, nested-limit failure, read or identity failure is reported. No logging cap is reached. The run records a normal exit; absence of faults here does not validate an unexecuted physics write path or establish frame-time performance. No damage input contexts occur for these scenery shots; no damage/armour conclusions follow.

## Decision and next bounded work

Accept **3C1 diagnostic coverage** of the real bullet movement entry and the previously silent matrix-caller failure. Do not repeat this unchanged two-shot packet. Working gravity/drag remains unaccepted.

Next correction should remove or avoid the unrelated high-frequency generic matrix interception, use the now-observed bullet movement call as the entry point, and derive/verify the correct world-space displacement and inverse transformation before altering the engine movement argument. Preserve engine collision/attribution, exact private identities and write guards. Do not simply accept caller 008A633E: those examples are not identified as pilot bullets. Do not weaken the caller filter or attach physics to all generic movement. Preserve diagnostics that distinguish arming, intended movement, actual displacement and pass-through.

Ask before preparing/installing that next correction, following the user's one-packet-at-a-time preference. This review saved only log/evidence/checkpoint files; it did not modify native source, build, install, change INIs/ESM or launch the game. Installed 306 remains. The newly mentioned Quake-style movement sources and Dynamic Encounters remain deferred and untouched; no compatibility or permission conclusions have been drawn about them.
