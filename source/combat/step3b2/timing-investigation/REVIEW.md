# 3B2 timing investigation — 15 September 2026

The existing log does **not** establish that the pilot bullets are too slow. Keep the configured speeds unchanged. The loaded engine advances projectile lifetime separately from movement, so total distance divided by total lifetime is not a reliable muzzle-speed measurement. The next bounded packet should observe individual movement updates before introducing drag.

## What was inspected

The user opened New Vegas at its main menu. A read-only process capture saved 57,344 bytes of projectile code, 2,508 bytes of vtables and a 4,096-byte image header in `runtime-20260915-102703/`. Code matched across two reads. The manifest records process identity, addresses and SHA256 hashes. There was no process write, injection, suspension, assistant game launch, gameplay test, DLL build or game-file edit.

`projectile-disassembly.txt` in that runtime folder is the usable disassembly. The similarly named `projectile-engine-disassembly.txt` in this parent folder came from packed on-disk code and is **not usable for engine semantics**. The COFF wrapper only supplies addresses to Microsoft's disassembler; it is not an executable plugin.

## Confirmed update order

The runtime missile vtable at `0108FA44` has `UpdateProjectile(float)` at slot `+310`, pointing to `009B8030`. JIP's supplied class declaration identifies this interface. Its `ProcessImpact` slot `+314` points to `009B8B10`.

Within the base update body:

1. `009BEF7A–009BEF8F` passes the local timestep to virtual `UpdateProjectile` (except projectile type 5).
2. **After that call returns**, `009BEF91–009BEFA0` adds the timestep to `lifeTime` at `+D8`. This addition does not require a positive distance change.

The missile update has paths that return or skip its movement section. In particular, `009B8260–009B8292` checks `hasImpacted` at `+90`, the hitscan flag and state `+150`; an already impacted, non-hitscan missile outside state 3 jumps to the later auxiliary section at `009B87A1`. The enclosing lifetime addition still follows the virtual call. Earlier return paths also exist. We have not mapped every state to a gameplay situation.

The movement path calls `009BF300`, which passes its timestep and a constructed vector to `009BF370`. That helper obtains vectors before and after a movement call, subtracts them and calls `009C4E60` with the final boolean argument set to 1. `009C4E60` stores a vector at `+104`; only its true branch adds a derived scalar to `distTravelled` at `+110`. The false branch instead processes the stored vector without incrementing distance. The scalar/vector math callees lie outside the captured range and were not independently disassembled here.

Consequently, `+104` must not be assumed to be a permanent velocity vector. The supplied ITR source also explicitly describes it as launch aim initially and applied movement delta later.

## Donor and provider evidence

- JIP's projectile commands expose `lifeTime` and `distTravelled` directly. They do not align these counters to the same moving interval.
- `BallistXMain-reference.txt`, lines 190–204, stores lifetime while distance is zero and subtracts that offset later. This is evidence that the donor accounts for startup timing; it does not prove which updates occurred in our six-shot capture. Its later `fTimeLag` calculation serves a different purpose. Do not transplant its packed roll-angle storage scheme.
- ShowOff's impact/destruction helper copies impact coordinates into reference position. This is not a distance-counter correction. Position and counter samples around an impact must be labelled separately.
- The runtime base-update entry at `009BECC0` already contains a detour. The supplied ITR `OnNearMissHandler.cpp` installs a detour at this exact address and calls its original trampoline before near-miss scanning. Runtime destination-module ownership was not captured, so this is a source match, not a complete ownership verification. Do not overwrite that entry with another independent hook.

## What the six shots establish

The accepted capture remains `../captures/2026-09-15-3B2-135b1dd786ea/analysis.json`. All six private projectile lifetimes completed, with correct identity and reload behaviour and no reported tracking faults.

For five shots, recorded lifetime minus distance/configured speed is approximately 15–16 ms; for one it is approximately 31 ms. Those values are derived from rounded log counters, not precise frame-duration measurements. They are consistent with update timing or non-moving intervals. However, creation/impact/destruction samples do not show which intervals contributed. Main-menu code inspection establishes possible control flow, **not the branch history of a previous shot**. Collision timing, timestep adjustments and units also remain to be measured. Neither a universal 16 ms subtraction nor a speed multiplier is justified.

## Proposed next packet: 3B3 aligned movement observation

Purpose: compare distance and time from the same engine update, separating non-moving startup updates and collision updates from ordinary flight.

- Restrict the new observer to the two existing private pilot profiles, with bounded sample counts and copied scalar data.
- Record the actual timestep argument, before/after lifetime, distance and position, projectile identity and impact state. Mark nested impact callbacks within the update so callback-phase differences are visible. Preserve raw observations rather than inventing corrected values.
- Compare unobstructed moving updates separately. Do not use clipped terminal displacement to assert a lower muzzle speed. Stop or flag samples when identity/lifecycle validation fails.
- Prefer a verified missile-update dispatch boundary if compatible; fingerprint the original function and verify ownership before installing any wrapper. Preserve existing provider calls exactly once. The captured vtable target is a candidate, not an implemented or validated hook.
- Keep projectile speed, gravity, damage and the ESP unchanged. No directional-shooting integration. User performs a short two-weapon check after the observer is compiled and installed; do not repeat the existing six-shot test with the same insufficient logging.

Investigation complete. **Await user confirmation before preparing/installing 3B3.** Version 302 remains installed; exact speed calibration and native flight authority are not accepted yet.
