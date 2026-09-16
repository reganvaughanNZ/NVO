# Packet 3C native movement boundary

Version 305. See reference/FLIGHT-PHYSICS-SOURCE.json for fingerprints from the live, decoded engine code captured read-only at the main menu. Captured game code is retained locally for inspection and is not redistributed in this release.

## New write path

FlightPhysics.cpp patches only CALL 00930255 in the non-controller movement branch of 0092F260, targeting a preserving bridge before the original matrix-vector function 004B4500. It installs at xNVSE DeferredInit, before activating loaded-world physics. The full movement body (4668 bytes), missile movement/update and matrix helpers must match. A later guard normalizes only our owned five bytes; other changed code disables new movement. Existing JIP/ITR/ShowOff hooks are retained.

The bridge preserves GP registers, EFLAGS, x87/SSE/MXCSR and last error. It passes original EBP/EBX, ECX matrix and second input-vector argument to a helper, then tail-jumps to the original once. The engine's original ret 8 performs argument cleanup. Output vector and continuation remain the engine's. No lock spans an engine call.

The helper requires the exact missile stack callers 009BF416 and 009BF35D, current-thread stack bounds, owner identity, unqueued movement branch, exact input pointer moveFrame+0xC, rotation matrix frame-0x2D8, finite orthonormal rotation and zero base gravity (+64). It writes only the checked 12-byte caller stack vector. No object-position/angle setter, damage path, queued controller, impact response or lifespan deletion is replaced.

The original timestep comes from the 009BF300 wrapper's saved argument, before 009BF370 conditionally adjusts its own timestep for source AV 33. The already-created displacement remains based on the original argument. Initial velocity is the actual world displacement divided by this timestep and configured units, retaining engine launch direction and speed rather than reconstructing angles or guessing power factors. Both timestep values are logged. Subsequent baseline speed changes or duplicate/reversed markers retire the pilot lifetime to engine movement. VATS correctness of this new path still awaits the user's test.

DLL-owned velocity integrates gravity and G1/G7 drag with RK4, substeps at most 1/240 second. Accepted movement steps are positive and at most 0.25 second. Initial engine speed must lie between 10 m/s and Mach 4.9; unsupported inputs pass through. Drag coefficient is rho*pi*0.0254^2/(8*0.45359237*BC), multiplied by interpolated Cd and speed for vector acceleration. No wind; fixed density and sound speed; world Z is vertical. Seventy units per metre remains a donor simulation scale assumption.

Physics has 128 concurrent identities, reused after destruction; diagnostic quotas never end physics. First impact stops further gravity/drag edits for that lifetime. Reload/suspension clears transient state, and an unknown post-load projectile is left alone. No saved in-flight velocity restoration is claimed. First eight tracked lifetimes per capture log up to 64 applied steps each. Movement/collision effects are not validated merely by a PHYSICS_STEP intent row; compare with actual FLIGHT_STEP output.

NativeLog reserves 7168 detail rows and 1024 priority rows per process, plus one detail-limit notice. This preserves lifecycle/summary space during ordinary long captures without unbounded logging. Exhausting even the reserve is still possible.

Public NVSE/event/hit ABI modules remain as in 304. CurrentHit, NativeObserver and DamageEvents source is unchanged. FlightTiming logic is unchanged; fields now say timing_writes=0 to distinguish its read-only role from physics. FlightPreview similarly labels its own read-only fields and registers physics before its diagnostic cap. Unknown equipment and all non-pilot weapons retain existing movement.

