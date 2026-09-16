# NVO Combat Packet 3F1 — missed-shot diagnostics

**Purpose:** capture the missing measurements when a long-flying projectile trips the movement safety guard. The last log correctly identified ammunition but recorded three failures outside its detailed trace limits. The user confirmed those shots missed their targets.

This packet adds bounded disk-log reports. It does not fix the underlying movement discrepancy or change flight, ammunition, damage, armour, save/load behaviour or safety tolerances. The HP ammo-selection reset remains a separate unresolved issue.

Native version is **312 / 0.3.12 / phase3F1**. Keep **NVO.esm and NVOFlightPilot.esp active**, with RD.esm retained as the existing NVO dependency. All11 profiles and their records/configuration are unchanged. No GECK work or compilation is required from you.

## Short check

1. Load the prepared test save and wait three seconds. Use the ordinary Hunting Rifle. If you need supplies, run **`bat NVOFlightKit3F`**. The existing kit supplies the rifle and40 each of standard/AP/HP ammunition; each run adds inventory.
2. Repeat **one standard .308 shot and one AP shot** under the same long-distance conditions that produced misses in your last test. Use the same aiming mode you used then. Allow **10 seconds after each shot finishes** before continuing, so a missed projectile can complete its flight. If a shot hits, just report it; do not keep repeating shots to force a failure.
3. **Load your test save once**, wait three seconds and **manually select HP**. Confirm the label and let the ammo-switch animation finish. Fire **one HP VATS shot at a distant live target** with a clear line of fire. Wait10 seconds after VATS finishes. Mention if it misses.
4. **Exit and report completion.** Say which shots missed and whether the first two used VATS or manual aiming. I will read `NVOCombatCore.log` beside FalloutNV.exe. Wait for review before another launch overwrites it.

No full ammo-cycle repeat, video or stress test is needed. God mode is fine. Do not change your stats, damage settings or weapon condition to manufacture a miss. If firing fails or flight reports unavailable, stop and report that.

Manually selecting HP after loading lets us finish the missing post-load firing check without assuming the reported ammo-persistence issue is fixed. We are not testing saved HP selection in this packet.

## What the log adds

Each of the first16 displacement failures per loaded session can record four compact rows, even if ordinary per-frame tracing stopped:

- **PHYSICS_REJECT_METRICS:** identity, phase, errors, tolerance, and whether vector error, position error or both failed. Includes whether routine tracing covered that lifetime/step.
- **PHYSICS_REJECT_MOTION:** expected and actual displacement, accepted/proposed velocity, timestep, previously accepted flight time and current engine lifetime/travel.
- **PHYSICS_REJECT_POSITION:** starting and ending positions, their difference and the position residual.
- **PHYSICS_REJECT_CONTEXT:** submitted/returned local vectors and already-observed controller identity/counters.

`PHYSICS_DIAGNOSTIC_READY` identifies the diagnostic schema. `PHYSICS_DIAGNOSTIC_SUMMARY` reports complete reports, write failures, omissions and lifetime detail limits. These go to the existing disk log, not the console. Routine logging remains limited to8 lifetimes/64 entries; failure rows use the existing bounded priority reserve. If its process-wide reserve or disk writes fail, the logger cannot guarantee delivery of every row.

If the failure reproduces, the report should reveal which measurement broke the contract. A capture without a reproduced failure is useful but does not prove the prior problem fixed. The guard still stops further NVO movement edits for the affected track; it does not reverse its selected private projectile.

## Installation and reversal

Requires the currently installed3F record/configuration packet. Replace only:

- `Data/NVSE/Plugins/NVOCombatCore.dll`
- `Data/NVSE/Plugins/NVOCombatCore.pdb`

The receipt names the verified backup. To reverse, close New Vegas and restore **both** files from the backup's `originals` folder to their matching paths. Keep3F's ESP, INIs and kit unchanged. This restores build311 with its previous limited diagnostics. NVO.esm, RD.esm, other extenders, activation and the earlier unused-file cleanup are untouched.

The assistant compiled and statically inspected the DLL; gameplay remains your checkpoint. Native source, matching symbols, build evidence and existing third-party notices accompany the packet. Await review before another packet or physics fix.
