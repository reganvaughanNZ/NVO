# Packet 3C5 / 310 - guarded controller local-Z correction

Purpose: preserve the pilot projectile's calculated vertical movement at the controller operation that would otherwise zero it. This is a correction candidate; user flight verification remains required.

## Evidence and native change

The 309 log identifies virtual C8 of ProjectileListener vtable 01090594 as C73170. Both edited requests contain the intended local Z but actual displacement fits omission of that component. The hash-verified 2048-byte prefix shows conditional FLDZ/FSTP at C73517, after request XYZ is copied into a local vector. The precise reset branch was not directly observed in 309.

310 replaces those six bytes with CALL LocalZBridge + NOP. Arriving at that bridge directly observes the reset branch. The helper pairs the active private projectile, thread, controller and request with the existing enclosing movement observation. It checks the incoming C73170 frame, parent frame, owned virtual-call return, aligned local stack, saved vector pointer, exact vtable/target, timestep, unchanged rotation, collision-free identity and byte-identical submitted/request/working vectors. Flag bit 11 must be clear. No guessed meaning is assigned to engine modes or flags.

For an unchanged baseline, or any untracked/unsupported/rejected call, replay the original FLDZ/FSTP. The bridge's CALL adds four stack bytes, so fallback uses [ESP+5C], exactly the original [ESP+58]. For a verified applied pilot vector only, preserve the already-copied local vector by skipping this reset. No C++ write to controller, request, position, collision or damage fields is added. Both bridge outcomes restore GP registers, flags, x87/SSE/MXCSR and stack balance. The engine continues at C7351D through its original scaling, rotation and collision path.

The initial unchanged segment must both match actual displacement and visit the checked reset boundary before future flight edits become eligible. A guard failure stops subsequent edits for that lifetime; it cannot undo an already-submitted segment. Conditional paths that naturally skip the reset after an accepted baseline still undergo unchanged actual-displacement verification.

The existing caller-owned 12-byte movement input write, RK4 gravity/drag, two exact private combinations, tolerance, impact/destruction attribution and reload cleanup remain. Unknown equipment receives original reset behavior. Damage authority remains disabled. No armour, injury, VATS policy or broader projectile features are added.

Eight hook spans occupy four distinct pages. Existing transactional protection/flush/rollback and exact owned-byte normalization now include the six-byte reset span. The full 2048-byte captured controller prefix is fingerprinted before installation and each capture, alongside previous guards. This is not a full-function fingerprint. Raw controller-byte logging is retired because its identification is complete; evidence remains archived internally.

## User check

Keep NVO.esm and NVOFlightPilot.esp active. Load the prepared save and wait three seconds. Outside VATS, fire one private NVO Flight Hunting Rifle shot and one private NVO Flight 9mm Pistol shot, with their private ammunition, at the same distant solid wall or water tank. Pause between shots, exit normally, and report finished. God mode is fine. No extra reload, stress test, video or GECK edit is required.

Expected evidence: PHYSICS_LOCAL_Z baseline preserve=0/original_reset=1, applied preserve=1/original_reset=0 when the reset branch is reached; PHYSICS_ACTUAL matched=1 for baseline and multiple applied free-flight segments of both weapons; nonzero applied_verified, zero mismatches/unpaired/guard failures. Impact must still terminate flight through original collision handling. Merely arming, reaching the branch or skipping the reset is not physics acceptance.

The world scale and atmosphere remain fixed assumptions. This short check does not establish stress performance, reload/VATS acceptance of this new branch, broad compatibility or injury behavior. No assistant gameplay, DLL loading or GECK execution is performed.

## Installation and reversal

Install only the matching NVOCombatCore.dll/PDB pair after the allowlisted installer verifies hashes and creates its backup. No new dependencies or configuration files. See INSTALL-3C5.md for the actual receipt and backup. Close the game and restore both 309 files from that backup to reverse. Existing NVOFlightPhysics.ini enabled=0 disables the pilot for the next capture.

One packet at a time: review the user's next log before further work. The separate BALLISTX-main simulation library was not incorporated. Existing donor credits/notices remain.
