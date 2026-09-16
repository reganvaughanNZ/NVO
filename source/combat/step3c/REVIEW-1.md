# Packet 3C review: six-shot check complete; native physics did not run

User reports test complete and clarifies the first reload was to set up the environment. This review treats session 1 as setup, session 2 as the first two test shots, and session 3 as the repeated pair followed by the final two live-target shots. VATS for the last pair follows the user's report of completing the instructions; the log itself has no explicit VATS marker.

Read the game-root NVOCombatCore.log directly and archived identical bytes under `captures/2026-09-15-3C-bd94aae6ce5b/`. SHA256 bd94aae6ce5b6ff39177df3a868cd651d96c792063bf36d87b8f05fd40132080; 57,808 bytes, 248 lines; last write 2026-09-15T12:38:17.093505 local. Header 0.3.5 / 3C. No running FalloutNV process found at review. No game files, native code or configuration changed.

## Sequence and results

| Capture | Interpretation | Private shots | Timing steps | Free-flight steps | Applied physics steps |
|---|---|---:|---:|---:|---:|
| Session 1 | Setup before the first reload | 0 | 0 | 0 | 0 |
| Session 2 | Hunting Rifle then 9mm | 2 | 15 | 11 | 0 |
| Session 3 | Repeated rifle/9mm, then 9mm/rifle live-target pair | 4 | 21 | 13 | 0 |

All six private shots have matched creation, impact and destruction, using the exact private weapon/ammo/projectile combinations. Session 2 lifetime 2 is the rifle (3 free-flight steps), lifetime 3 is the pistol (8). Session 3 lifetime 4 is the rifle (4), lifetime 5 the pistol (9), lifetime 6 the final pistol shot (startup then collision), and lifetime 8 the final rifle shot (startup then collision). An ordinary NPC shot is lifetime 7 and is not one of the six private shots.

There are 36 timing updates overall: 24 free-flight, six startup/no-motion and six collision. Free-flight engine speeds match the unchanged settings within 0.000864% at most. The four distant shots give ample evidence that the zero native update count is not simply caused by every bullet hitting immediately. The two final shots have matching actor hit-input contexts: pistol head region 1 and rifle torso region 0, with correct private ammunition/lifetime links. Input health and ITR health-callback values are not measured committed damage or proof of a new NVO damage calculation.

PHYSICS_HOOK_READY appears, and every capture prints PHYSICS_READY. However, there are **zero PHYSICS_STEP rows**, every private PHYSICS_SHOT has steps=0, and both test captures report applied_steps=0. No PHYSICS_REJECT or PHYSICS_DISABLED is emitted. This means installation/arming was reported but the new integration-and-write path did not execute for these shots. The 3C gravity/drag checkpoint is **not accepted**.

Both reloads have successful post_load_game results, and LIFECYCLE exit_game is present. All final physics/preview/timing tracks close; no invalid timing, read/identity failures, overlaps, nested-limit hits, active-table overflow or live-address reuse is reported. Two unpaired ordinary-NPC callbacks occur only in setup session 1, consistent with the existing loaded-save boundary and irrelevant to private-shot completeness. No logging cap is reached; this short capture does not test exhaustion of the new priority reserve. No crash is indicated in this run, and this does not certify future write-path safety.

## Source inspection and next correction

Read the installed-source FlightPhysics.cpp and existing decoded engine capture. Version 305 instruments only matrix callsite 00930255 inside generic movement 0092F260. BeforeMatrix silently returns before any rejection counter if the stack/return-address filter fails or no matching owner is found. Other movement branches can bypass that callsite. The current log cannot distinguish an unvisited hook from those early returns. No exact root cause is proven, so do not claim a corrected call address or loosen write guards without evidence.

Next bounded correction should make entry/path/early-filter diagnostics visible, verify the private missiles' actual movement branch and preserved caller stack, and only route the existing gravity/drag integration through a verified boundary. Keep exact pilot identity restrictions, original engine collision handling and damage untouched. A tracked projectile that moves without any physics-boundary visit should be reported explicitly rather than only emitting PHYSICS_READY. This is a correction to Step 3, not permission to move on to armour, energy weapons or a larger scope.

Do not ask the user to repeat this unchanged build. Their requested six-shot sequence is complete and usable. Ask before preparing/installing the correction packet, following their one-packet-at-a-time preference. Keep the current files until that decision; this review only saved the capture, analysis and checkpoint.
