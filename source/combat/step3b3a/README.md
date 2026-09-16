# Packet 3B3A — projectile thread correction

NVOCombatCore **0.3.4 / 304** fixes the thread restriction exposed by your completed 3B3 test. That test correctly recorded six complete projectile lifetimes and a reload, but the observer rejected 15 updates on a different thread and produced no movement samples.

Purpose: measure time and distance in the same update before changing flight physics. This is a correction to the diagnostic packet. Only the DLL and matching PDB are replaced; existing weapons, ammunition, projectile settings, NVO.esm, configuration and activation stay as they are. No GECK work or additional downloads.

## Your shorter check: four shots

1. Keep **NVO.esm and NVOFlightPilot.esp active**. Launch normally, load your test save, and wait three seconds. Your save made after entering through main-menu `coc` is suitable for this flight check; character creation is unnecessary here.
2. Run `bat NVOFlightPilot` if you need the kit. Use **NVO Flight - 9mm Pistol** and **NVO Flight - Hunting Rifle** with their matching NVO Flight ammunition.
3. Outside VATS, stand well back from the Goodsprings water tank, farther away than in the last check if practical, and fire **one shot with each weapon**. Roughly 50–100 metres is useful so there can be movement updates before impact. A distant wall or solid ground also works. Pause briefly between shots.
4. Reload the original test save without restarting the game. Wait three seconds, reacquire the kit if needed, and fire **one shot with each weapon** again.
5. Exit and tell me you have finished. I will read `NVOCombatCore.log` beside `FalloutNV.exe` directly. Wait for review before launching again because launch overwrites that log.

God mode is okay. No video required. If the diagnostic reports unavailable or anything fails, stop and tell me so I can read the log. This check does not assess health damage or character/background initialization.

## What changed

- A tracked update may now be sampled on the thread executing it. `FLIGHT_TIMING_THREAD` records the initialization and update thread IDs; `other_thread_steps` counts accepted entries on other threads, rather than rejected entries.
- Impact counters belong to the shared projectile lifetime, protected by the observer lock. They can be updated by a callback on any thread. `impacts_in_window` counts callback deliveries between the two observations, not an exact collision timestamp. Any observed impact makes that lifetime's subsequent measurements ineligible for the free-flight speed comparison.
- A destruction notice retires the shared identity. The return observer checks session and identity before reading again. If the identity has retired, it logs an unavailable sample and returns to the engine without a post-call projectile read.
- If two observed calls overlap for the same lifetime, including reentrant calls on one thread, that lifetime is blocked from further timing. Both original engine calls still run. The first return also skips its post-call read. Independent projectiles and sequential updates on changing threads remain supported.
- Thread-local storage now serves only the synchronous return-continuation stack. It is never used to find impact/destruction markers on another thread and is not cleared on reload. Capture state is cleared under the shared lock; old continuations still return to their original callers without reading the new capture's state.

The dispatcher slot and byte fingerprints remain those inspected for 3B3. The assembly still preserves integer registers, EFLAGS, x87/SSE/MXCSR and the original argument bits, then tail-calls the original function exactly once. A sampled call temporarily sees an NVO return continuation; the engine's `ret 4` handles argument cleanup before the observer returns to the saved caller. The prior gameplay capture did **not** execute this sampled return path, because the thread filter rejected the updates first. The corrected packet still requires your runtime check.

No timing lock spans an engine call. Timing never acquires the parent observer lock or invokes scripts from the update thread. Shared data is accessed under the timing lock; the parent event callbacks take parent, timing, then log locks in that order. The supplied ShowOff destruction hook dispatches before returning to the engine free path; the supplied xNVSE non-deferred DispatchEvent supports synchronous handler delivery. Arbitrary alternative dispatchers or concurrent engine mutations outside these observed calls are not certified by this source review.

## Expected results and limits

`FLIGHT_TIMING_READY` should report `update_threads=any_serialized_per_lifetime` and `event_counters=shared`. Each shot should have timing rows or a specific unavailable/overlap reason, followed by lifetime and capture summaries. The new thread ID rows show which threads actually executed the sampled calls.

`FLIGHT_STEP` and `FLIGHT_STEP_STATE` retain before/after counters, position, speed settings and actual timestep with nine significant digits. Compare `speed_valid=1` moving updates; exclude collisions, no-motion updates, changed settings and reversed counters. Lifetime may remain unchanged inside the missile method because the base method increments it afterwards. A `gap_life_s` is a raw counter difference, not a hardcoded correction. Do not change speed settings to make terminal distance/lifetime averages match.

Caps remain eight private-pilot lifetimes per capture, 64 updates per lifetime and eight nested continuations per thread. `pending_update`, `blocked`, `retired_during_update`, `overlap_lifetimes`, `thread_changes` and `nesting_limit` expose incomplete/rejected observations. A pending call at a destruction summary can be followed by an identity-retired return row; it is not automatically a leaked lifetime.

The existing guard fails closed on unsupported code or dispatch ownership. The two test profiles alone are timed. Native projectile flight and damage writes remain disabled; no gravity, drag, injury, armour, Directional Shooting or Stewie feature is added. The engine-unit/metre conversion remains unverified. No speed or flight-authority checkpoint passes until the new log is reviewed.

## Installation and reversal

The installer backs up the previous **303 DLL/PDB pair** and logs, replaces only those two files, verifies their release hashes and checks protected assets and activation for changes. The game must be closed and is not launched by the assistant. Refer to `INSTALL-3B3A.md` for the completed transaction and exact backup path.

To reverse, close New Vegas and restore both backed-up 303 files together, leaving the existing test ESP, INI and activation intact. With mod-manager hardlinks, unlink deployed files before copying so the staging copy is not overwritten. The older 302 backup is also retained. To disable flight observation, set the existing `[Preview] enabled=0` and restart/reload; this does not undo the test ESP's physical projectile settings.

Compiled and statically inspected by the assistant. All gameplay remains for the user. Review this capture and ask before another packet.
