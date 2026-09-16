# Packet 3B3 — measure time and movement together

NVOCombatCore **0.3.3 / 303**. Purpose: establish whether the earlier low distance/lifetime averages came from startup or impact timing before adding drag. The engine still moves the bullets. This packet changes only the DLL and matching PDB, retaining the accepted 3B2 test weapons, ammunition, configuration and projectile settings. No GECK work is required.

## Your check

1. Launch normally, load your test save and wait three seconds. Keep **NVOFlightPilot.esp** enabled. Run `bat NVOFlightPilot` if you need the test equipment.
2. Outside VATS, fire two shots with **NVO Flight - 9mm Pistol** and two with **NVO Flight - Hunting Rifle**, using their matching NVO Flight ammunition. Use the same distant wall or solid ground as before; avoid very close impacts and empty sky. Pause briefly between shots.
3. Reload the original save in the same game session. Wait three seconds, obtain the kit again if needed, then fire one shot with each test weapon. This verifies the newly installed observation hook across reload.
4. Exit and tell me the test is finished. I will read `NVOCombatCore.log` beside `FalloutNV.exe` directly. Avoid another launch until the log is reviewed, since launching overwrites it. God mode is fine for this measurement. A video or transcription is unnecessary unless something looks wrong.

If the timing observer reports unavailable, stop and let me read the log. Do not change speeds to compensate or substitute ordinary weapons. No damage, injury or armour test is needed for this packet.

## Expected log

- `FLIGHT_TIMING_READY` identifies the guarded observer and its limits: first eight private-pilot lifetimes per capture, up to 64 updates each.
- `FLIGHT_TIMING_TRACK` associates the test weapon/ammo/base records with the existing unique lifetime serial.
- `FLIGHT_STEP` reports the actual update timestep, before/after lifetime and distance, gaps since the preceding return (or creation), position displacement, and impact callbacks inside that call. Values retain nine significant digits.
- `FLIGHT_STEP_STATE` adds before/after position, impact/list state, flags, internal missile state and speed settings. These are copied observations, not writes.
- `FLIGHT_TIMING_SHOT` and `FLIGHT_TIMING_SUMMARY` report counts, caps and rejected reads. A destroyed-during-update row deliberately has no post-destruction memory read.

Only positive-distance, positive-timestep updates without impact indicators or changed speed settings are candidates for `speed_valid=1`. Collision updates are still logged, but excluded from that speed comparison. This flag is a measurement filter, not a declaration that the ballistics model is validated. Zero movement is logged as `no_motion`, rather than being assigned a fake speed correction. Lifetime can remain unchanged inside the missile virtual call because the enclosing engine call increments it afterwards; the next update's `gap_life_s` exposes that separation.

## Native boundary and limitations

The new NVO module fingerprints the complete missile update and relevant movement functions against the user's read-only runtime capture. It verifies the game/JIP layout and requires the missile vtable slot at `0108FD54` to point to `009B8030`. It changes just that dispatch pointer to an observer, using a compare/exchange and restoring page protection. Unsupported code or ownership disables the timing feature with a log reason and a once-only console notice. No independent patch replaces the existing ITR base-update detour or ShowOff creation/impact/destruction hooks.

The entry wrapper saves general registers, EFLAGS, x87/SSE state and MXCSR. It passes the original timestep bits and receiver unchanged and tail-jumps to the original function exactly once. For sampled calls only, it substitutes a return continuation, records the post-update sample and returns to the saved engine caller with the original `ret 4` cleanup already completed. Thus the original function temporarily sees an NVO return address. The bridge preserves Win32 last-error state; the observer's own math uses a temporary default FP environment.

Before/after samples are synchronous. An eight-entry thread-local stack permits nested calls; over-limit or foreign-thread samples are skipped and counted. No lock is held while the original engine function runs. Lock ordering is parent observer, then timing, then log; timing never reacquires the parent. Identity and lifetime checks precede post-call reads, and a destroy callback retires the identity. Reload clears transient tracking, but does not erase outstanding return continuations. There are no asynchronous projectile dereferences, per-frame object-list scans, scripts or inventory grants from this observer.

The small dispatch wrapper remains installed until process exit, but becomes a passthrough outside active captures. Fingerprints and ownership are rechecked on capture activation. This is not universal compatibility with arbitrary runtime patchers; gameplay acceptance is still required. Logging itself has overhead, so this is bounded diagnostic instrumentation rather than the final production flight implementation.

No change to NVO.esm, test ESP, speed, gravity, spread, damage, saves or unrelated extenders. Existing hit instrumentation remains unchanged. No native drag, injury model, damage authority, Directional Shooting or Stewie adaptation is introduced. The engine-unit/metre conversion remains independently unverified. Do not promote terminal averages or clipped impact displacement to muzzle velocity.

## Installation and reversal

This is an incremental packet requiring the already installed 3B2 files. Install only `Data/NVSE/Plugins/NVOCombatCore.dll` and its matching PDB with the game closed. The assistant's installer checks source/destination hashes, preserves the previous pair and logs in a dated workspace backup, and verifies protected files. It does not alter plugin activation.

To reverse: close New Vegas and restore the **302 DLL and PDB together** from the backup named in `INSTALL-3B3.md`. Leave the existing test ESP and INI in place. To disable flight observation altogether, set the existing `[Preview] enabled=0` in `NVOFlightPreview.ini` and restart/reload; this does not revert the test ESP's physical projectile settings.

Build and static inspection are performed by the assistant. All gameplay remains for the user. Wait for the resulting log review and confirmation before the next packet.
