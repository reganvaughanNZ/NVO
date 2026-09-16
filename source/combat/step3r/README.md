# Packet 3R — controlled flight-capacity refusal

Native 323 / NVO 0.3.23. Purpose: exercise the actual production pool's refusal path and unchanged supplied-projectile fallback without a large NPC battle. Damage replacement stays OFF. This is a temporary diagnostic build, not a performance benchmark or final combat balance.

## Short user check

1. Start New Vegas through xNVSE, load a disposable outdoor save and wait five seconds. Keep NVO.esm and NVOFlightPilot.esp active. AI can stay off. Run `bat NVOFlightKit` if needed.
2. Equip the ordinary **9mm SMG**, using **standard 9mm**. Aim above the horizon into clear sky, away from nearby terrain/buildings (not straight overhead). Fire one short automatic burst, about five rounds. Consecutive fire is needed so the first bullet is still airborne when the next arrives. No target or VATS required; an exact count is unnecessary.
3. Wait ten seconds in gameplay, then reload the same save once. Wait five seconds. Use the kit if needed and fire one standard 9mm **pistol** shot into the distance.
4. Wait ten seconds in gameplay, quit normally, reply **Finished** and mention any new firing problem. No GECK edits, extra NPCs, recording or repeated test unless the log actually shows missing evidence.

## What the diagnostic does

Only in a build compiled with `NVO_ADMISSION_CAPACITY_PROBE=1`, the first eligible player standard-9mm-SMG admission with an empty physics pool reserves 127 inert tickets in the actual 128-slot pool. They have no game objects, physics tracks or lifecycle records. The first real shot takes the last slot normally. While it remains owned, the next real reservation reaches the unchanged full-pool refusal and the observer rolls back its temporary lifetime ticket. SpawnBoundary then forwards the supplied original projectile unchanged. The probe releases only its 127 tickets, checks the surviving real ticket's identity/state and disables itself for the process. Later shots can occupy all normal slots. It never evicts an active shot or falsifies the pool's capacity/refusal result.

If no overlap occurs, the synthetic tickets are released after 16 successful admission attempts or at the next capture/suspend. A consumed probe never rearms after reload/menu. Restarting the game rearms this diagnostic build. Test operation does not depend on successful logging. Any failed cancellation or owner-preservation check blocks further NVO substitutions rather than attempting object repair. Normal build defaults exclude the probe entirely (`BUILD.cmd --no-pause`; CMake option OFF). Reproduce this test build with `BUILD.cmd --no-pause --capacity-probe`.

The normal refusal path now records whether its lifecycle reservation was rolled back, and reports a failed rollback as a process fault. Both pools log zero occupancy AFTER lifecycle reset, in addition to their pre-reset summaries. This resolves the ambiguity of an airborne projectile at quit seen in 3Q. No flight equations, damage rules, engine patches or creation-forwarding ABI are changed.

## Acceptance and limits

Require native323 plus `CAPACITY_PROBE_BUILD enabled=1`; exactly one `CAPACITY_PROBE_ARM synthetic_reserved=127`; a real selected/committed shot; `CAPACITY_PROBE_RELEASE reason=actual_pool_refusal` with 128 before / 1 after, 127 released, preserved=1 and a live survivor phase. Require `FLIGHT_ADMISSION_REFUSED lifecycle_rollback=1`, matching one-slot rollback, and the corresponding `SPAWN_BOUNDARY` supplied/forwarded bases identical with reserved=0 and base_argument_changed=0. Verify the resulting stock creation/return where available; synchronous stock destruction/null must be reported distinctly rather than treated as an owned shot. Later shots must commit normally, with no second probe arm after reload. The original owned shot must continue matched movement/retirement or be explicitly cleared at lifecycle reset. Require both post-reset logs to show zero.

**One physics capacity refusal/overflow and one observer physics refusal are expected for this deliberately saturated test.** They are not a process fault. Unexpected extra refusals, post-selection rejection, mismatches, failed rollback or failed probe release fail the checkpoint. If release reason is attempt_limit/suspend instead, full capacity was not demonstrated: do not call it a pass. No natural destruction claim for a projectile still airborne when the user quits.

18 offline checks exercise the same production pool/probe helper: real saturation, active-owner preservation, later reuse, double release, pre-existing flights, process-once behaviour, cancellation and stale reset. These do not execute engine hooks. Prior 3Q pool/ABI checks remain unchanged; they are not claimed rerun. Both diagnostic and normal configurations are compiled and inspected. This test is not 128 real simulated bullets, an FPS/stability benchmark, lifecycle-pool saturation, nested/foreign-thread creation, exceptional cancellation, damage authority or support for every weapon family. Frozen Ultra pre-damage gate remains HOLD.

## Installation and reversal

Only NVOCombatCore.dll and its matching PDB are replaced. NVO.esm, the pilot ESP, INIs, scripts, load order and other plugins are preserved. `Installation/INSTALL-3R-result.json` identifies the verified native322 backup. Close the game and restore those two original files from its `originals/Data/NVSE/Plugins` directory, or ask the assistant to restore them. The probe is for this checkpoint and will be removed from the installed build in a subsequent authorized packet after review.
