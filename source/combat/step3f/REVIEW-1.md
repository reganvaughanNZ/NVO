# Packet 3F review — ammunition identities pass; full checkpoint held

2026-09-15. The user reports completion and that HP ammunition did not stay equipped between loads. **Do not mark the complete 3F flight/reload checkpoint accepted.** The capture confirms correct per-shot ammunition identities but also records three movement-guard rejections and no shots after either save load.

Archived log: `captures/2026-09-15-3F-f57f04e1f1b9/NVOCombatCore.log`. SHA256 `f57f04e1f1b9ce8bae6fdbf22bf25f498e413e78319ff0d93c53a286de384010`, 463,017 bytes, 1,980 lines, last write 18:59:22.684016 +12. The adjacent `capture.json` and `review-data.json` retain source metadata and detailed results. `tools/review_combat_3f.py` verifies this immutable capture without changing or launching the game.

## What passed

All 17 shots match the selector's ammunition to the actual creation event, weapon and private projectile. This independently confirms result consumption, rather than relying on the selector's intention alone.

| Profile | Shots | Actual ammo | Actual private projectile |
|---|---:|---|---|
| Standard .308 | 8 | 0006B53C | 0C000807 |
| .308 AP | 3 | 0013E442 | 0C00080D |
| .308 HP | 6 | 0013E443 | 0C00080E |

All use Hunting Rifle00004333 and source projectile0008F20A. Linked actor-hit contexts also exist for all three rounds: HP lifetime7, AP lifetime9 and standard lifetime14, all against actorFF001978. Their creation ammunition agrees with the hit context. No selector skips, identity failures, reused live addresses, overflow, unpaired accounting or open lifetimes are reported.

The log contains three loaded sessions and a normal exit. All 17 shots occur in session1; sessions2 and3 initialize11 profiles and contain zero shots. Thus load/reset initialization is observed, but an HP shot after loading is not verified. This is a statement about the capture, not an inference about the user's intended sequence. Extra shots do not invalidate the identity evidence, but they exceed the current detailed trace budget.

## Movement failures and the trace gap

The session reports1,312 applied segments,1,296 verified edited segments,17 matching baselines and3 movement mismatches. There are1,767 movement/accounting entries each,1,329 guarded reset entries and1,312 preserved resets. Thirteen projectiles report impacts and all17 report destruction. The applied-versus-verified difference is consistent with13 impact exclusions plus3 mismatches.

| Lifetime | Round | Rejection | Lifetime at destruction | Engine travel at destruction |
|---|---|---|---:|---:|
| 8 | AP | applied_displacement_mismatch | 8.38725s | 265,986 units |
| 10 | Standard | applied_displacement_mismatch | 8.0002s | 265,406 units |
| 13 | Standard | applied_displacement_mismatch | 8.0272s | 265,301 units |

These are long-flying projectiles, including two using the previously accepted standard profile. This is not evidence of an AP-only mapping problem. Destruction times/travel totals are not the precise rejection times or coordinates. Do not assert a cause such as an engine clamp, VATS correction or floating-point error from these totals.

The supplied native source limits detailed physics logs to the first8 lifetimes and first64 movement/accounting entries per detailed lifetime (`FlightPhysics.cpp`, `kLoggedLives`/`kLoggedSteps`). Lifetime8's destruction summary reports420 applied steps and419 verified steps; its failure happens after the detailed step window. Lifetimes10 and13 have no detailed physics trace. `PHYSICS_REJECT` prints their reason, but the failed `PHYSICS_ACTUAL` measurements are suppressed by the ordinary logging limits. The mismatch could originate in either displacement-vector error or position error; the rejection string alone does not distinguish them.

The available trace independently verifies126 edited comparisons (63 each for lifetimes1 and8),8 baselines and140 controller/reset pairs. Six short collision segments are excluded. Maximum detailed edited-vector error is0.00936163013 units, maximum error/tolerance fraction0.183519711 and maximum detailed position error0.0000305175781 units; all retained detailed comparisons pass the existing tolerance. These detailed matches do not negate the three later summary failures. In particular, HP's early traced shots reach collision directly after baseline; later HP shots exceed the lifetime trace limit, so per-HP edited-flight confirmation is incomplete.

The guard marks a failed track stopped and ends further NVO movement edits for that track. This does not undo the already-selected private projectile or prove equivalent vanilla flight after rejection. Keep the existing guard and tolerance; do not treat rejection as a clean flight pass or loosen tolerance without evidence.

## HP did not remain selected after loading

Record this as a separate unresolved ammo-persistence report. Packet3F reads the engine's actually equipped round at firing; it adds no save serialization or equipment-restoration code. Its log records neither the selected ammo immediately before saving nor immediately after loading. With no subsequent shots, this capture cannot identify what round was selected on load or why HP was lost. It also cannot establish a causal connection to the flight mismatches.

The supplied Stewie source contains `code/Features/RememberWeaponAmmos.cpp`, including stored weapon ammunition and an `OnMiddleHighProcessLoadGameHook`. This is a relevant candidate for a future small ammo-memory fix, not a proven diagnosis or a drop-in change. Its hooks, extra-data handling, dependencies and applicable notices need review before adapting it. No Stewie code or runtime DLL is installed by this review.

## Next proposed packet

Ask for a diagnostic-only3F1 packet before another gameplay check. Give each displacement failure a bounded failure snapshot outside the normal detailed-log limits: weapon/ammo/profile/lifetime/step, expected versus actual displacement, vector and position errors, tolerance, elapsed time and the already-observed controller/position context. Include whether detail limits were reached, without flooding the console or expanding routine per-frame logging. Keep physics rules, hooks, tolerance, private records, ammo tuning and damage ownership unchanged. This makes the next captured failure diagnosable. No additional playtest is requested until that packet is ready.

Ammo persistence remains a separately recorded issue. After the diagnostic cause is understood, complete only the missing flight/reload observations; no automatic repeat of the entire standard/AP/HP kit test. Prior limited3E evidence remains recorded, with the newly exposed longer-flight limitation added here. NVO damage replacement stays disabled. No game files, native code, release archive or installation receipt were changed during this review.
