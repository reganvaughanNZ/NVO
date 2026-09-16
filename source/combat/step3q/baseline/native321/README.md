# Packet 3P — prove the projectile creation boundary

Purpose: establish the exact native call where NVO can later reserve flight-tracking capacity BEFORE selecting a private projectile. The public pre-create event has no cancellation/return receipt. Source and installed-provider disassembly identify a narrower boundary after ShowOff finishes its selectors and immediately before its engine creation call. This packet observes that boundary first. It does NOT yet fix capacity admission or change the current selector.

Native321 (0.3.21) forwards the same sixteen 32-bit argument words to the same engine continuation, once, and returns the same pointer. It compares the actual returned object with the synchronous creation event. No engine lock is held across the call. Stack-owned receipts, session epochs, eight observed nesting levels, conservative duplicate/destruction rejection and sixteen detailed rows per capture bound the diagnostic work. Aggregate counts continue independently of log limits. This adds temporary overhead; no FPS/stability guarantee follows from compilation.

The deployed ShowOff184 handler is checked using PE metadata, a full 159-byte relocation-normalized fingerprint, its firing/creation branches, and the captured engine entry fingerprint. One aligned writable continuation pointer in the loaded ShowOff module is atomically redirected; no provider file or executable code page is edited. Unknown bytes/foreign continuation owners disable this diagnostic. Existing flight remains unchanged. A future ShowOff update requires reinspection, not weakening this guard.

## Your short check

1. Start through xNVSE and load a disposable test save. Keep NVO.esm and NVOFlightPilot.esp active. Wait five seconds in gameplay.
2. In the console run `bat NVOFlightKit` if you need weapons/ammunition. This existing kit gives a 9mm pistol, hunting rifle and 9mm SMG. Use standard 9mm and standard .308 ammunition.
3. Fire one 9mm pistol shot into a rock, one close-range hunting-rifle shot in VATS at a living target, then a short 9mm SMG burst into a rock. Hits/misses do not determine this check; projectile creation does.
4. Reload the same save once. Wait five seconds, give the kit again if needed, and fire one 9mm pistol shot into a rock. Quit normally and reply **Finished**.

No GECK work, long-range accuracy test, NPC stress battle or new character is required. Do not repeat the test just because a shot misses. The log remains `NVOCombatCore.log` in the Fallout New Vegas game folder.

## Acceptance and limits

Assistant reads the fresh log. Require native321, SPAWN_BOUNDARY_READY on both captures, paired creation/return evidence for the pistol/rifle/SMG, a paired post-reload pistol call, and clean session closure. Investigate any mismatch, null return, depth overflow, foreign-thread event, unscoped creation or disabled guard in context rather than treating all as successes. A scope is ambiguous if it receives multiple create callbacks. Diagnostic log truncation is not proof of failure or success. User should report any new crash, freeze, firing/weapon behaviour difference.

19 offline x86 ABI/receipt checks pass, including 10,000 forwarding calls. These do not execute the game or native DLL and do not validate real event ordering, load transitions, SEH paths, deep nesting or threading. Existing flight, hit/damage observation, ESM, pilot and configurations are preserved. Damage replacement and flight reservation remain OFF in this new module. The frozen Ultra pre-damage gate remains HOLD.

## Next after your result

If this boundary is confirmed, replace the old pre-create selection path with scoped admission here: reserve both physics and required lifetime bookkeeping before substitution, commit only the exact return, and release an unused reservation at the call's end. Unknown equipment and capacity refusal keep the supplied projectile. Failures after substitution must retain ownership/diagnostics and stop further admissions; they must not be described as restoring vanilla flight. That future packet must explicitly settle residual current-projectile behaviour and outstanding return cleanup before closing317-07. No damage authority is enabled by this checkpoint.

## Reversal

Close New Vegas. Restore ONLY NVOCombatCore.dll and NVOCombatCore.pdb from the installation backup's `originals/Data/NVSE/Plugins` directory to the matching game directory. The backup path is in Installation/INSTALL-3P-result.json after installation. This restores native320; no ESM/script/save/config restoration is needed. The in-memory continuation pointer disappears when the process exits. Ask the assistant to restore the two files if preferred.
