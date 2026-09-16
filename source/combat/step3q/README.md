# Packet 3Q — reserve flight capacity before selection

Native322 / NVO0.3.22. This replaces the old ShowOff pre-create selection callback with admission at the creation boundary verified by3P. Both a physics slot (128 total) and an observer lifetime slot (512 total) are reserved BEFORE the engine receives a private projectile base. A full pool, unsupported caller/thread, unknown equipment, changed supplied projectile or unavailable guard leaves the supplied projectile unchanged. There is no active eviction or dependence on log budgets. The two legacy private pilot weapons can also be admitted without changing their already-private base.

The actual creation callback binds provisional identity; the exact matching native return commits physics. NVO makes no movement changes before commitment. Only argument0 (projectile base) may change; the other15 stack words, single original engine call and returned pointer are preserved. A null return with no creation callback cancels both reservations. Ticket pool ownership and monotonic IDs reject old/cross-pool completions after slot reuse or reset. The main-thread, unnested path is enabled; other paths retain their supplied projectile.

## Failure policy

A post-selection mismatch, binding failure, exception or physics contract rejection sets an atomic process-wide admission fault. No further NVO projectile substitutions occur until New Vegas is restarted. Valid already-committed flights continue. A rejected flight receives no further NVO movement edits; its current private projectile is left to the engine. **This does not restore stock trajectory, undo an earlier displacement, or preserve the last integrated velocity automatically.** No unsafe game-object repair, deletion or fabricated return is attempted. Known/ambiguous ownership stays bounded until destruction or session cleanup; exceptions retain reservations without taking locks in the unwind handler. A reload cleans transient pools but deliberately does not clear the fault. The first fault code is retained independently of logging success.

The frozen Ultra pre-damage gate remains HOLD.317-07's pre-selection capacity gap has an implementation, pending this live check and later real stress/fault coverage. The exceptional private-projectile fallback limitation remains explicit. This is not armour/damage authority or a guarantee of crash-free operation.

## Your focused check

1. Launch through xNVSE, load a disposable save, wait5 seconds. Keep NVO.esm and NVOFlightPilot.esp active. AI/combat AI may stay off.
2. Run `bat NVOFlightKit` if needed. Use standard9mm and standard.308 ammunition.
3. Fire one9mm pistol shot at a building or rock across open ground, roughly50–100metres away. This gives us flight time after creation; a precise distance or hit is unnecessary.
4. Fire one hunting-rifle VATS shot at a nearby living target, then a short9mmSMG burst at a distant building/rock. Aim manually for the burst.
5. Reload the same save once, wait5 seconds, give the kit again if needed, and fire one9mm pistol shot across open ground. Wait a few seconds, quit normally, reply **Finished** and mention any new firing problem/crash.

No GECK edits, new character, large NPC stress battle or repeated long-range VATS attempts. Do not repeat merely because a shot misses. Log: game-root `NVOCombatCore.log`.

## Checks already performed and runtime acceptance

35 checks exercise the actual production pool/receipt primitives:128/512 capacities, refusal without eviction, first-resource rollback, cancellation, exact-match commit, destruction, retained faults, stale/reset/cross-pool tickets, and two20,000-operation traces independent of omitted logs.19 x86 forwarding/receipt checks also pass. The x86 DLL builds without warnings/errors and has a matching PDB. These fixtures do not execute game/DLL hooks, force live allocation failures, or prove the entire native coordinator, threading, cancellation/exception routes or real NPC overload. Actual integer exhaustion guards are inspected, not forced.

Assistant will require native322, ready boundary/selector, FLIGHT_SELECT with reservation_before_selection=1, paired returns with reserved=1, matching FLIGHT_ADMISSION_COMMIT and PHYSICS_TRACK entries, and matching reserved/committed totals with failed=0/process_fault=0. Check reload and retirement: slots_held/open should close to0 after projectiles finish. Look for applied/verified movement on the distant shots; if absent, do not claim flight integration was exercised. Treat any capacity refusal or unreserved projectile in context; unknown/unavailable profiles intentionally keep their supplied base. Reject missing evidence rather than loosening guards. Damage replacement stays OFF. No live capacity saturation is claimed by the short check.

## Reversal

Close New Vegas. Restore ONLY NVOCombatCore.dll and NVOCombatCore.pdb from the installation backup's `originals/Data/NVSE/Plugins` to that same game directory. Installation/INSTALL-3Q-result.json gives the backup path. This returns to tested native321. No ESM, scripts, INI, load-order or save changes are part of this packet. Ask the assistant to restore the pair if preferred.
