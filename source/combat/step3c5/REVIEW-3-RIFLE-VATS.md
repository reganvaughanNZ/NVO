# Packet 3C5 / 310 - rifle VATS flight checkpoint accepted

**The remaining rifle free-flight observation is present. Accept the limited two-weapon flight/reload/VATS regression checkpoint, combining this capture with reviews 1 and 2. No repeat of this test is needed.** This does not validate every VATS effect, exact collision-time energy, all ammunition, or damage replacement.

The user reports firing the hunting rifle from as far away as VATS would allow. The log records three private rifle shots across two loaded sessions, with one reload and normal exit. It does not directly label individual shots as VATS, so the VATS context comes from the user's report. Every shot has verified edited free flight, regardless of which shots were in VATS.

Archive: `captures/2026-09-15-3C5-5ffa63f073d0/NVOCombatCore.log`. SHA256 `5ffa63f073d093706363e8d88de583b08e87f8ef1d5dda49295f728cf86d4c0b`. 58,134 bytes, 265 lines; original last write 2026-09-15T16:22:41.9349888+12:00. The archive matches the original source hash. `tools/review_combat_3c5_rifle.py` verifies the immutable capture and records comparisons in its adjacent review-data.json.

| Session / lifetime | Edited steps | Verified free-flight steps | Final collision segments | Controller pairs |
|---|---:|---:|---:|---:|
| 1 / 1 | 2 | 1 | 1 | 3 |
| 2 / 2 | 4 | 3 | 1 | 5 |
| 2 / 3 | 4 | 3 | 1 | 5 |

All three shots use the private rifle 0C000801, ammunition 0C000803 and projectile base 0C000805. All three unchanged baselines and all seven edited free-flight samples match. Maximum logged edited-vector error is 0.00696832111 engine units; the largest error/tolerance fraction is 0.130422. Verified position-accounting error is zero.

All 13 movement/accounting/controller/reset observations pair, with the original reset retained for the three baselines and skipped for the ten edited vectors. Submitted requests, working vectors and returned arguments match. Each shot ends with one matched impact and destruction. No reported rejection, movement mismatch, read/identity failure, unpaired accounting, live address reuse, overflow, nesting/overlap, invalid timing, open lifetime, pending controller call or log cap. Reload cleanup and rearming complete cleanly.

The first and third shots have linked actor hit contexts with known ammunition. The first records a critical flag; it is still an observation of the existing damage path, not NVO critical/armour acceptance. The second shot has an impact without an actor damage context. A later explosion has no linked tracked projectile and unknown source/ammunition; the log keeps it separate. Do not attribute that explosion to the rifle or treat the unlinked explosion context as failed bullet tracking. The different pre-hit and pre-health numbers are not measurements proving duplicate damage; actual damage application remains unverified and native replacement remains disabled.

The first shot's edited pre-contact movement is independently matched, closing the gap left by review 2. Its final collision-boundary candidate also follows the intended input within small rounding differences, but collision endpoints are still excluded from the free-flight verifier. This does not explain away the previous capture's collision-only Z correction or establish exact contact-time speed/energy. Those remain engineering work before armour can depend on them.

Keep build 310 installed. Next proposed packet: expand explicit ballistic weapon/ammunition profiles beyond the two private pilot combinations, retaining guarded movement, engine collision handling and unknown-equipment fallback. Keep the scope small and ask before preparing it. Tracers, energy/flame projectiles and damage/armour changes are separate later work. The initial unchanged segment and uncalibrated 70-units-per-metre assumption remain documented pilot limitations.

This review changed only archived evidence, review tooling and checkpoint documentation. No native edits, build/install, game launch, gameplay, GECK or process-memory access.
