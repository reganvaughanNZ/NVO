# Current packet: 3C5 / 310 guarded local-Z correction

See README.md. One guarded conditional-reset hook extends the private movement pilot. User physics acceptance pending. Historical boundaries below.

# Current packet: 3C4 / 309 controller request diagnostics

See README.md. Three additional read-only controller observations retain the existing bounded movement pilot. No controller/object/damage writes. Gravity remains unaccepted. Historical boundaries below.

# Current packet: 3C3 / 308 movement-boundary diagnostics

See README.md and source/combat/step3c3/IMPLEMENTATION.md. Two added CALL observers only read pending movement arguments and candidate positions. Existing 3C2 movement write and mismatch limits remain; gravity is not accepted. Historical boundaries below.

# 3C2: bullet movement argument pilot (307)

Purpose: put gravity and drag at the confirmed private-bullet movement call, with an independent observation of the displacement supplied to the engine's distance accumulator. Runtime acceptance remains pending. The precise conditional bypass of the old generic matrix hook is not established; this packet avoids depending on it.

## Code and evidence

Two main-menu read-only captures: `runtime-20260915-132934` and `runtime-20260915-133335`. Their manifests contain exact process identity, range hashes and two-read stability. The second adds the sine/cosine helper. Existing generic movement, projectile wrapper/update, rotation matrices and matrix-vector code match the earlier 3C capture after accounting for the two currently installed NVO calls. A difference inside the broader speed-helper capture lies beyond the speed function used here; no claim that the entire region is identical. Captured executable bytes stay local and are not distributed.

Loaded helpers establish rotation data at reference +24; pitch is +24 and heading +2C. The observed matrix construction is Rz(heading) times Rx(pitch), forward +Y, positive pitch downward. Helper 004169A0 uses FSINCOS, storing sine in the second argument and cosine in the third. Rotation conversion uses this convention and its inverse; no engine function is called to set angles or positions. Nonzero rotation Y, invalid angles and non-forward input vectors are unsupported.

- CALL 009BF411 -> 0092F260 is retained as the movement boundary. Receiver, original frame/owner, input pointer frame+0C, parent return 009BF35D and enclosing missile-update returns 009B83EA/009B8481 are checked. Original timestep comes from the enclosing 009BF300 argument, before source time adjustment. Adjusted timestep remains an untouched engine argument.
- New CALL 009BF461 -> 009C4E60 observes the actual displacement, by-value three floats plus the original accumulate flag, before the engine writes its displacement and distance fields. This is read-only; the original function runs once with its original arguments and return address.
- Old generic matrix call 00930255 is no longer hooked. Both new callsites are within the missile wrapper and guarded/installed transactionally at DeferredInit. They share one memory page, so the combined span receives one protection change/restore; this avoids nested calls leaving a page writable. Full-code checks normalize only matching owned patch bytes.
- Each projectile's first movement segment is unchanged. Its measured displacement and end-position delta must match the derived direction before subsequent writes are allowed. This checks forward direction, not every basis vector or internal branch. Later applied steps provide the necessary evidence for the inverse transform's other components. Do not describe baseline verification alone as complete flight validation.
- Subsequent steps integrate cached world velocity with existing BallistX G1/G7 drag data and world-Z gravity, then invert the rotation and replace only the checked caller-owned 12-byte movement argument. The accumulator observer compares intended and actual displacement; a mismatch stops subsequent edits for that lifetime. The already executed segment cannot be undone. It does not use or overwrite projectile +104 as cached velocity.
- The first unchanged segment is a deliberate diagnostic limitation. Close impacts can finish without receiving NVO physics. This is not final launch-to-impact ballistics and must not be described as such.

Original engine movement, collision handling and bookkeeping continue. Both bridges preserve GP registers, EFLAGS, x87/SSE/MXCSR and last error; no lock spans an engine call. No extra return substitution or TLS continuation is introduced. Pairing requires matching tracked identity, synchronous wrapper frame and thread. Overlapping or missing accounting stops the track. Impact/destruction/suspension retire it; reload clears transient state. No saved in-flight velocity restoration.

RK4 integration, fixed atmosphere, private profiles, INI schema and donor scale 70 units/metre are unchanged. Maximum 128 concurrent tracks; physics does not end when detail logs reach quota. First eight tracked lifetimes log at most 64 movement and 64 accounting rows each. Unknown equipment, damage, armour, AI, medicine and newly uploaded resources are outside this packet.

## Validation and checkpoint

Assistant validation is compilation and static source/assembly/PE/PDB inspection only. No assistant gameplay or GECK work. Compare `PHYSICS_STEP phase=baseline argument_write=0` with `PHYSICS_ACTUAL matched=1`, then `phase=apply argument_write=1` with matching actual displacement and `FLIGHT_STEP` observations. Require nonzero applied and verified counts for both distant private shots. `PHYSICS_ARMED` is readiness, not success. Any mismatch, rejection, missing accounting or all-zero applied counts must be reviewed before expansion.

User check: load prepared save, wait three seconds, fire one distant private Hunting Rifle shot and one distant private 9mm shot outside VATS, pausing between shots; exit. Same distant scenery used in 3C1 is suitable. God mode is fine. No reload/VATS/stress expansion in this first correction check. Read and archive the game-root log directly after completion.

Install only DLL/PDB, retaining all existing configuration, dependencies, ESM/ESP and activation. Back up previous 306 before replacement; user already authorized closing the exact game instance for installation. Full reversal restores that matching DLL/PDB pair with the game closed. Setting existing NVOFlightPhysics.ini enabled=0 disables the movement pilot on next capture. Stop for the user's result before any next packet.


## Historical boundaries through 306

# Packet 3C1 movement-route diagnostic boundary

Version 306 addresses missing diagnostic evidence from the 305 zero-update test. It does not assert the movement/physics connection has been fixed. One read-only checkpoint is added at CALL 009BF411 (original target 0092F260, engine return 009BF416). The old matrix hook at 00930255 remains under the same identity/stack/rotation/write guards and uses the same integration. No hook address is substituted speculatively.

MovementBridge preserves GP/EFLAGS/x87/SSE/MXCSR and passes the original ECX receiver, float dt, vector pointer and EBP to BeforeMovement. It tail-jumps to the original, leaving receiver, three arguments and return untouched; the engine callee's ret 0C performs cleanup. The helper records only counters and bounded log rows. Its expected input is caller frame+0C and saved parent return 009BF35D. Game object reads occur synchronously while the original call owns the object; no asynchronous retained pointer dereference. No lock crosses the original engine call.

BeforeMatrix now counts all active entries, stack failures, return mismatches, owner-read failures, untracked owners and stopped owners. First eight early failures per capture include bounded raw addresses, without scanning stack contents. Each private identity counts movement/matrix visits. First eight private identities log at most four movement-entry rows each. PHYSICS_NO_UPDATE is emitted at most once per zero-update lifetime and at most 16 per capture. PHYSICS_ROUTE_SUMMARY provides total counts at load/exit. ARMING is labelled PHYSICS_ARMED with execution_observed=0; actual PHYSICS_STEP plus engine displacement is still needed for acceptance.

Both five-byte CALL patches are byte/fingerprint guarded and installed transactionally during DeferredInit. Only verified own patch bytes are normalized before physics/timing fingerprints. Both page protections and instruction caches are handled; failed transactions restore owned original bytes without overwriting another hook. No update-time patching or global matrix-function detour. Source provenance in reference/FLIGHT-ROUTE-CHECKPOINT.json points at the existing read-only decoded capture; no game executable code is distributed.

Four modules (CurrentHit, NativeObserver, DamageEvents, FlightPreview) are unchanged from 305. FlightTiming only adds owned-hook normalization to its existing fingerprint reader so the new entry checkpoint does not disable timing. NativeLog reserves priority capacity for the new zero-update/armed messages. New packet installs only DLL/PDB; all existing INIs, records and dependencies remain.

Runtime execution of the new checkpoint and exact cause of zero updates require the next user capture. Ask for two distant private shots outside VATS only; no repeat of unchanged six-shot or stress coverage. Do not accept movement from hook installation alone or weaken a failing guard based solely on expected behaviour.

## Historical boundaries through 305

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

## Historical interoperability record (through 304)

# Packet 3B3A interoperability and hook boundary

## Packet 3B3A thread correction

The completed 303 test had 15 foreign-thread skips and zero movement rows. The filter is removed in 304; no new hook address or changed assembly wrapper is introduced. The original 303 sampled-return path had not executed in that test and still needs runtime acceptance. Runtime hook fingerprints are unchanged.

Only return continuation storage is thread-local. Per-lifetime impact counts and destruction retirement are shared under the timing lock. Before records the callback count and thread ID; After finds the same session/address/serial, excludes any impacted lifetime from speed comparison, and reports callback deliveries within its observation window. A retired identity is never dereferenced by the return observer. Same-lifetime overlapping/reentrant updates block further timing and skip the original pending call's post-read; original engine calls remain exactly once. Sequential updates may move between threads. No lock spans the engine function or reacquires the parent event lock.

Capture suspension clears tracking but not TLS continuations. Supplied ShowOff free-hook and xNVSE non-deferred DispatchEvent evidence is hashed in reference/FLIGHT-TIMING-THREADS.json. This does not certify arbitrary external dispatchers or unobserved concurrent engine mutations. No game-thread-only functions or script calls are introduced inside update callbacks. All five existing hit/event/flight-preview/log modules are byte-identical to 303. See README for fields, limits and four-shot reload check.

## Historical packet 3B3 addition

FlightTiming.cpp owns one guarded dispatch slot: missile vtable 0108FA44 +310 = 0108FD54, expected target 009B8030 (2149 bytes, FNV-1a A1B80FE6DF917F84). Full fingerprint provenance is in reference/FLIGHT-TIMING-HOOK.json. It also guards the base dispatch/lifetime span and movement/vector helpers. ITR's 009BECC0 detour and ShowOff hooks are preserved.

The two existing private pilot profiles alone register timing identities. Limits are eight lifetimes, 64 calls each and eight nested return frames. Entry and return assembly preserve integer/EFLAGS/x87/SSE/MXCSR state; helpers preserve Win32 last error. A sampled original call sees a substituted NVO return address, while its receiver, argument bits and original stack layout remain intact. The original callee performs its own ret 4, then the observer returns through the saved engine address without an additional argument cleanup. Unmatched calls tail-jump directly with the original return address.

The read-only before/after data uses the callback's actual float timestep. Contact/impact markers exclude terminal updates from speed comparison. No lock spans the original engine call. Return frames remain valid across capture suspension; retired identities are not dereferenced. This adds an instrumentation pointer write, not flight or damage authority. Before and after are phases of one engine call, not asynchronous retained-object access. All current-hit and damage-provider code remains unchanged.

See README.md for exact log fields, checks and limitations. Compilation/assembly inspection does not establish runtime acceptance.

## Historical packet 3B2 addition

The native interfaces and existing hit/event hooks below remain unchanged. The isolated six-record NVOFlightPilot.esp supplies engine-driven physical flight for calibration copies. FlightPreview adds only game-root NVOFlightPilot.txt output at capture initialization and a fixed kit-ready PrintC after releasing the observer lock. The batch contains four resolved AddItem commands and is executed only by the user. No native engine object, flight or damage write is introduced. Four profiles now include the original two baselines plus two calibration copies. The two PrintC messages are fixed diagnostics, not arbitrary script execution. Historical 3B1 preview details below describe the retained measurement path.

## Public interfaces retained

Win32 NVSEInterface prefix 32 bytes (QueryInterface 24, GetPluginHandle 28); PluginInfo 12 bytes; Messaging prefix 8 bytes, interface 2, version >=4. EventManager prefix 20 bytes, interface 8, no leading version, native registration/removal offsets 12/16. Console prefix 8 bytes, interface 1, version >=2, RunScriptLine offset 4. The latter runs one fixed PrintC line after a failed capture activation; no dynamic script input or opcode registration. Exact provided sources are hashed in sdk-reference.json. Current plugin version is 304; this public interface prefix is unchanged.

ShowOff CREATE/DESTROY parameters are [source, weapon], IMPACT [source, weapon, struckRef], BLAST [target, source], with the projectile/explosion as thisObj. Classic onhit/onhitwith pass nullptr and [victim, otherForm]. These are separate typed decoders, not current hit data. A classic hit object may be EXPL. Classic callbacks may coalesce.

## New current-data observer

JIP internal/hooks.h installs CopyHitDataHook into 0x1087FD8 and 0x10897C0 (virtual CopyHitData slot +0x774). Its inspected installed function is jip_nvse.dll RVA 0x9490, length 106, returning with ret 4. The receiving process is ECX and the ActorHitData argument is [entry ESP+4]. We wrap both pointers only if both still point to that exact inspected JIP function; we do not detour its instructions. The new wrapper is authored NVO code. It calls the observer before tail-jumping once to JIP. JIP's allocation, copy and critical-event behavior remain in the provider function.

The wrapper preserves EFLAGS, all integer registers, original stack/return address, x87/SSE state and MXCSR; the C++ bridge preserves GetLastError. Its logging uses a temporary default FP environment. The compiled wrapper was disassembled to inspect stack offsets, save/restore, bridge argument ordering and final indirect jump. Runtime behavior still requires the user's check.

The 0x64-byte layout includes source +0, target +4, carrier union +8, region +0x10, health/base/fatigue/limb +0x14/+0x18/+0x1C/+0x20, armor +0x28, weapon damage +0x2C, weapon +0x30, flags +0x58. Static assertions check key offsets and size. Live form headers provide type +4 and ID +0xC. The target must be an actor type 0x3B/0x3C and its process +0x68 must match the receiving process. Mismatch or unreadable data is a bounded HIT_CONTEXT_INVALID row. The hook still tail-calls its original provider on failed observation.

Carrier +8 is a UNION: it may be projectile, explosion, source actor (including some fist cases) or null. We never assume a projectile from this field alone. Only projectile form types 0x3D..0x40 or 0x69 can use the projectile/ammo layout. Flag 0x2000 is logged as the supplied explosion flag; flag 4 is supplied critical status. Reported regions are integers; no internal organs are inferred. Caller location is logged only as an RVA inside the supported game image, or zero if external; it is diagnostic provenance, not a stage classification.

## Compatibility guards

Installed game PE: base 0x400000, timestamp 0x4E0D50ED, SizeOfImage 0x107B000, PE32/x86. Installed JIP PE: timestamp 0x665225A8, SizeOfImage 0x80000. Module pages must belong to the expected loaded images. JIP CopyHitData's entire 106 bytes use FNV-1a64 fingerprint 5DB9CC631AC1E846 after normalizing the sole relocation at byte +0x59 to preferred JIP base 0x10000000. The calls remain relative; no provider code bytes are copied or executed by NVO. Fingerprints are compatibility checks, not a security boundary.

Install runs on the first pending main-loop capture activation, after provider initialization. Both page protections must succeed before changing either slot; aligned atomic compare/exchange refuses intervening owners and rolls back partial installation. Page protections are restored and a failure is explicitly logged. No patch is written to a game file. A later capture rechecks slot ownership and never overwrites an unrecognized replacement. The wrapper stays resident while capture is suspended; no provider function is invoked by the logging bridge, and no event-registration call is made under the observer lock.

## Ammunition

JIP patches projectile initialization at game 0x9BC241 with a jump to installed JIP RVA 0x10620. Its full 156-byte fingerprint is B1A07310C15D7E37 (no module relocations). Both the branch destination and fingerprint must match independently before the ammo layout is enabled. This check can fail without preventing current damage-field observation.

For a live projectile, JIP GetAmmo returns extraDataList.ammo at +0x60 only when numProjectiles at +0x14A is nonzero. NVO mirrors those read conditions and additionally requires the pointed form type AMMO (0x29). It stores the ID at creation and reads it again from the current carrier; it does not substitute the weapon's selected ammo. Missing or unsupported data is ammo_known=0. Unknown does not mean no ammo. The creation snapshot may be unavailable even when the hit snapshot is valid.

## Recording and limits

600 provider-event rows and 200 current-context rows have independent counters. CREATE/IMPACT/DESTROY bookkeeping continues after provider text stops; other notices stop at their text budget. Thus summary projectile counters can exceed printed rows. A 512-slot table matches live address identity AND refID, with a new serial for every creation, retires on destroy and clears on capture restart. No stored pointer is dereferenced later. No hit row is discarded to merge it with a classic event or assumed application count.

The actor's stored lastHitData is never consulted. The copy-input phase establishes a fresh argument, not final damage application timing or observed HP loss. It may receive multiple copies per attack and does not inherently prove every damaging path or every pellet reaches it. Current fields include all upstream processing that already occurred. Damage replacement, ammo tuning, projectile flight, wounds, save serialization and health writes remain disabled/unimplemented.

Capture suspends on preload/failure/exit, queues after successful load/new-game, then removes/rebinds only NVO event handlers after load flushes. Successful capture rechecks the wrapper without installing it twice. Console failure notification is at most once per process. The log is recreated per game launch and appended across same-process loads, bounded to 8192 rows. No game or GECK was launched by the assistant.

Credits and applicable notices are in THIRD-PARTY-NOTICES.md. Source hashes and installed binary hashes are in sdk-reference.json. Previous packet assumptions remain preserved in the original 2B2 archives.


## ITR public damage-event observer (2B4)

DamageEvents.cpp registers two native callbacks through the existing xNVSE event-manager prefix. The source's ITR_VERSION is 20202. The installed ITR DLL SHA256 is 31f5abad415750141906efbe810a32eb35ac714335e65e806215655c72c7fc0c. At runtime the module must be x86 PE32 with timestamp 6A948FDD and SizeOfImage B3000. These runtime metadata checks are not a full memory fingerprint or proof of ITR hook ownership. The installation precondition additionally checks the complete DLL file hash. No ITR binary is replaced.

OnPreHitDamage supplies [target, source, weapon, packed float, integer region, multiplier pointer]. OnPreHealthDamage supplies [target, source, packed float, multiplier pointer]. We copy only the first five / three argument slots, decode the scalar float bits without dereferencing them, validate the actor target and callback thisObj identity, and retain source type without assuming all health-event sources are actors. The mutable multiplier slot is never read or written. Callbacks preserve Win32 last-error state and make no script/API calls; native result setters are not used. xNVSE resets the native result before each callback and supplies an invalid result for callbacks returning none. These ITR events do not require a result, and their multiplier callback ignores invalid results. Thus registering NVO does not multiply or replace damage.

The two streams have independent 200-row budgets. Callback totals continue after text is capped. Suspension marks callbacks inactive; the next successful load/new-game activation removes only NVO's own registrations and rebinds after load flushes. No retained actor pointers, heap-owned actor state or serialization are introduced. One additional fixed console diagnostic can appear if ITR registration/build checks fail. Registration success is explicitly not proof that the provider emits events; the user capture is required. ITR's listener probe refresh may take roughly 30 main-loop updates, hence the brief pause before testing.

ITR invokes pre-hit before the original Actor::HitMe at six configured call sites, after upstream mitigation; it excludes non-main-thread and nested dispatch, no-process targets, player region-14 hits and nonpositive health-and-limb inputs. It reports health damage or a limb fallback, not both fields. Its pre-health event observes a pending negative DamageActorValue input, can include ordinary hits again, and excludes some reentry/thread cases. Neither proves committed HP loss. Do not combine these with copy inputs as independent damage applications or infer one-to-one pairing from ticks. Further diagnostic coverage remains necessary before authority over damage.


## Packet 3B1 flight-preview boundary

No new event bindings or engine writes. NativeObserver calls FlightPreview from its existing CREATE/IMPACT/DESTROY handlers under its own serialization lock. Config and loaded-mod resolution run once per capture. Suspension and queued capture clear scalar caches. A pending, fixed console notice is emitted only after the observer releases its lock. No engine calls occur under that lock in the new module. NativeEvent return values/multipliers remain untouched.

Projectile reads require the existing game/JIP ammo-layout guard to pass for the capture. xNVSE GameData.cpp's DataHandler pointer is read at 0x11C3F2C; GameData.h specifies loadedModCount +0x218 and loadedMods pointers +0x21C. ModInfo supplies a 260-byte name at +0x20 and modIndex at +0x40C. Count 1..255, nonnull readable entries, terminating names, unique names, sequential indices and FalloutNV.esm at zero are required. Only scalar IDs are retained. No internal DataHandler/LookupForm function is called. Resolution establishes loaded filenames/IDs, not winning form contents.

For each pilot shot, live reference type must be missile 0x3D. Base pointer +0x20 must be PROJ 0x33. Source weapon +0xF8 must be WEAP 0x28; source +0xFC must agree with callback identity. Actual ammo comes from the already guarded ProjectileAmmo reader; equipment-selected ammo is never substituted. All three profile IDs (weapon, ammo, projectile base) must agree. Current base/live fields are observed, so unrecognized overrides cannot be silently chosen by a weapon name.

JIP GameForms.h BGSProjectile: UInt16 flags +0x60 (hitscan bit 1), UInt16 type +0x62 (missile 1), floats gravity +0x64, speed +0x68 and range +0x6C. JIP GameObjects.h Projectile: floats speedMult +0xD0, lifetime +0xD8, distanceTravelled +0x110. JIP Projectile::GetData and command wrappers corroborate lifetime/distance/speed-multiplier fields. Reads use the existing isolated SEH reader and validate form types and finite bounded fields. The new module writes only its own state and the diagnostic log; it does not call setters or retain/dereference game pointers after callbacks.

Reported baseSpeed * speedMult is setting-derived, not a measured velocity vector. Average travel is (endDistance - startDistance)/(endLifetime - startLifetime), marked unavailable for hitscan, nonpositive/insufficient time or decreasing counters. Even an available average is not initial muzzle velocity. BallistX's 70 units/metre remains an explicitly unverified preview scale. A future integrator must establish time/unit/vector semantics and flight ownership before changing speed, gravity, hitscan or positions.

NVOFlightPreview.ini is a deliberately small runtime format exported from selected 3A JSON fields. The native DLL does not parse JSON or drag tables. Schema rejects unknown/duplicate keys and incomplete profiles, bounds all numbers and file/array sizes, and performs no dynamic script compilation. A missing/invalid profile leaves preview inactive; all damage and flight authority remain disabled. The packet does not establish all hooks' compatibility or exactly-once damage.
