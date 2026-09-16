# Packet 3C4 / 309 — user test review

**Diagnostic checkpoint accepted. Gravity/drag is still unaccepted. No repeat of unchanged 309 is needed.**

Archived the game-root log before another launch: `captures/2026-09-15-3C4-7e3ad3449a2c/NVOCombatCore.log`, SHA256 `7e3ad3449a2c959bda7231b06540e132f97bd8a6cb009e094b849248f5f722a5`, 37,963 bytes, 194 lines. Source last-write time: 2026-09-15 15:22:38 local. `tools/review_combat_3c4.py` validates the archive, computes comparisons and decodes the bounded captured code offline. Structured results are in the capture's `review-data.json`.

## Runtime result

One successful load/session, two private shots (rifle then pistol), both hit scenery 00106B5E and were destroyed. Normal exit. Seventeen timing samples: 13 moving, two startup/no-motion, two collision. No reported invalid timing, read/identity errors, unpaired accounting, nesting/overlap, live address reuse, capacity overflow, open lifetimes or detail cap. This is not a new VATS, damage, stress or reload test.

Both initial unchanged baseline segments matched. Each first edited segment failed the unchanged displacement test and stopped further NVO movement edits for that lifetime. Applied writes=2; applied verified=0. Controller entries/returns=2/2 for each shot, with zero pending controller calls at destruction. All four observations used `virtual_enter`; the alternate direct path did not appear in those samples.

## New evidence

Both weapons actually dispatch through vtable **01090594**, virtual slot C8, to function **00C73170**. The local JIP source names this vtable `ProjectileListener` in `internal/class_vtbls.h:806`. The runtime address evidence is primary; the source name is supporting identification.

The controller request equals NVO's submitted input and remains unchanged after the controller returns. Timestep matches the generic movement argument. Both edited requests include their vertical correction:

| Measurement | Rifle | Pistol |
|---|---:|---:|
| Request local Z | -0.326924920 | -0.326088876 |
| Full intended displacement error | 0.326768025 | 0.325649559 |
| Existing acceptance tolerance | 0.0744856654 | 0.0552525183 |
| Error predicted by omitting local Z | 0.00119180 | 0.00568661 |

Values are engine coordinates, not calibrated metres. Candidate and actual displacement match at logged precision. The omission pattern remains consistent with earlier captures, but is now tied to the actual dispatched controller implementation.

## Concrete correction candidate

The bounded 2,048-byte code capture is complete and hash-verified: FNV64 `0193951146A4412C`, SHA256 `20a927ae6742fc61e6cdf8f0a52c945051a7a33cf743c1aa7c7a151627e0beac`. It is the beginning of a larger function, not the complete function. Offline COFF/dumpbin decoding executes none of the captured instructions. The capture stays in internal review evidence and is not distributed in a release.

Decoded instructions show:

1. C734D7–C734FC copies request XYZ at ESI+10/+14/+18 into the controller's local working vector at ESP+50/+54/+58.
2. C73500 calls 009306B0; C73507 skips the reset if that helper returns true. Otherwise a test of controller flags at +414, bit 11, can also skip it.
3. **C73517 FLDZ; C73519 FSTP [ESP+58] explicitly zeros the working vector's Z.** It does not overwrite the original request, explaining how input readbacks can remain correct.
4. C7351D onward scales the working vector and C73557 passes it to 004A3E00 for storage at controller+510. Subsequent captured code conditionally applies pitch rotation.

The earlier runtime capture also decodes 009306B0: it calls 005C0880 and compares the result to 5. This review does not assign an unverified semantic name to that mode, and the log did not sample the helper result or flag bit inside this function.

This is a strong, specific explanation for the measured local-Z omission. **The exact conditional reset's execution has not yet been independently sampled.** Do not globally bypass that branch, change controller mode/flags, widen acceptance tolerance, or replace the final object position after collision. The next packet should confirm this boundary for the already-paired private projectile and preserve its intended working vector only under the exact existing identity, code and timestep guards. Keep the original remaining controller/collision path and actual-displacement check authoritative for acceptance. Unsupported paths must retain their original behavior and stop further NVO edits.

## Next step and limits

Propose one focused correction packet for the controller's local vector preparation, with a baseline and short two-weapon acceptance check. Continue with only the two private combinations, no armour/damage work or new dependencies. Runtime proof must show applied displacement matches, beyond merely reaching the hook. Ask before preparing/installing that next packet.

This turn changed only internal review tools/evidence/checkpoints. No native code edits, build, install, game-memory reads/writes, gameplay or GECK work. The game was closed when checked. Version 309 remains installed. Xhigh remains appropriate; Max is not needed for this next bounded task. The legacy-code review does not change this combat checkpoint.
