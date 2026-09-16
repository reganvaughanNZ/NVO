# Packet3F2 / native313 implementation

## Established engine behavior

The user clarified that shot3 of capture77ebadbd30fd was a missed VATS shot. At step392 it requested deltaZ=-39.298344 from Z=-2065.97363, but ended at Z=-2048 with deltaZ=+17.9736328. The difference57.2719771 exceeds the inspected engine's30-unit terrain-raise threshold.

Read-only captures of the already running game are archived under runtime-20260915-195354, runtime-20260915-195458 and runtime-20260915-195715. Their manifests identify the process, addresses and hashes. The on-disk executable's corresponding code differs and was excluded from patch derivation. ENGINE-FINDINGS.json records the relevant hashes and constants. Engine bytes remain local research evidence and are not distributed in the release.

- Generic movement00930150 calls004572E0 with candidate `[EBP-30h]` and height output `[EBP-2B4h]`.
- Supplied JIP `nvse/GameData.h` names004572E0 as `TES::GetTerrainHeight`.
-0045738A loads the default float at01017824, verified as -2048.004573DC returns false when required terrain is unavailable.
- Generic movement immediately reads the height output without checking AL.0093015E compares height minus candidate Z against the double at0101DB88, verified as30. When strictly greater,0093016B..00930171 replaces candidate Z with that height.
- This establishes an engine mechanism consistent with the previous fault. Correlating its execution with corrected free-flight in this packet remains the user's gameplay checkpoint. Do not claim all VATS misses are affected or that successful terrain-query corrections are invalid.

## Narrow correction and ABI

One additional hook replaces CALL00930150 to004572E0. The existing eight bridges remain byte-identical in the compiled object. Generic movement's EBX is its incoming argument frame; callers other than009BF416 immediately tail-call the original query with flags restored. This avoids diagnostic overhead for normal character movement.

For the projectile caller, TerrainBridge duplicates both query arguments and invokes the original function exactly once using the original ECX. It retains the query's full EAX/AL and post-call register/flags/FP state across the observer: PUSHFD/PUSHAD, aligned FXSAVE, known temporary FP environment, FXRSTOR/POPAD/POPFD. The original callee consumes the duplicate8 bytes; the wrapper returns with RET8 for the caller's original arguments.

AfterTerrainQuery revalidates thread, checked stack bounds, generic caller and frame, projectile/weapon/source/base identities, controller pairing/reset and an accepted baseline. It ignores successful results. A failed query is corrected only if the result is exactly -2048, the engine's >30 threshold would raise the candidate, no impact/contact is present, and the candidate matches the expected displacement using the existing tolerance. Only the checked output float on the caller's stack is changed to candidate Z. Query return value, controller fields, actor/projectile position fields, collision records and native damage are untouched.

The standard accounting hook still independently verifies the actual post-movement displacement. A changed candidate, unfamiliar query result, unexpected code/hook ownership, or later displacement mismatch retains the existing rejection behavior. Matching an arbitrary end position of -2048 alone never grants an exception.

## Guards and limits

The existing whole generic-movement fingerprint includes the new site; hook normalization includes its original bytesE88B71B2FF. Additional fingerprints guard all260 bytes of the terrain query through its RET8, the default float and threshold double. Nine spans use the existing four code pages. The position-commit page's protect/flush/rollback span now starts at the terrain call, covering both owned sites in that page. Installation retains the existing transactional rollback and hook-ownership checks.

No integrator, drag coefficient, atmospheric input, initial baseline segment, ammunition profile, engine AMMO effect, save serialization or damage authority changed. HP selection persistence remains unresolved. The full flight checkpoint is pending gameplay; contact-energy and unit calibration remain future prerequisites for armour authority.

## Diagnostic evidence

PHYSICS_TERRAIN_READY reports the guarded scope once per loaded capture to disk. PHYSICS_TERRAIN_REJECT_DEFAULT logs up to16 corrections per session, including failed-query/default/candidate/error/tolerance. PHYSICS_TERRAIN_REJECT_DEFAULT_VERIFIED logs up to16 matching accounting results. Their REJECT names route them through the existing priority log reserve: they reject an invalid default, not the projectile. PHYSICS_REJECT continues to mean an actual stopped track.

PHYSICS_TERRAIN_SUMMARY counts eligible queries, failed queries, corrections, verified corrections, later collision exclusions and log-write failures. Detail limits never stop physics; the existing per-process log reserve still bounds all writes. Counters reset on load. The four-row3F1 failure snapshots remain available. No new console output is added.

## Validation and delivery

Compilation and static PE/PDB/export/source/assembly inspection only; no assistant gameplay. The builder verifies unchanged16 other source/header files, unchanged integrator/tolerance and eight prior bridges, query fingerprints, result/stack/identity guards, new bridge argument offsets/state restoration and bounded log formats. STATIC-CHECKS.json contains the evidence. DLL and matching PDB are packaged with complete native source and existing donor notices; private engine capture bytes are excluded.

The installer verifies the prepared plan, current312 preimages and protected dependencies, closes only the verified FalloutNV process using existing permission, backs up both files and the current log, installs two files, and checks protected assets/activation again. Reversal restores both native312 files; records, configs and load order remain as before.
