# Segment-speed contract and source findings

Two independent results are retained. `ImpactModel` remains the narrow point/time fit, unchanged. `ContactSpeed` supplies an observed engine-segment mean or a whole-step NVO speed interval, with compile-time `damageAuthority=false`. Availability is not point association, body-region authority, launch-speed measurement or an energy-application permission.

For owned flight, drag acceleration is opposite velocity and gravitational acceleration has magnitude g. Thus d|v|/dt <= g. From both ends of an interval of length dt:

    max(0, endSpeed - g*dt) <= speed(t) <= startSpeed + g*dt

The small 0.00001 m/s margin is a numerical/replay comparison allowance, not a collision tolerance or formally certified integration bound. Reintegrating the recorded start velocity must reproduce the submitted displacement and full-step velocity before offering the range. No midpoint is chosen as the true impact speed. Actual engine collisions are swept during a movement update; our ODE is an authored model of speed over that update, not precise internal-organ geometry.

For the unchanged first segment, observedVelocity*dt*units must reproduce its movement vector and both logged velocities must agree. The result is the segment's mean with the numerical allowance. Do not set baselineVerified merely because the projectile collided or retrofit missing launch/gravity history.

Required producer context is established by the existing pending movement/accounting stack, thread and projectile identity checks, including no prior contact at BeforeMovement. Additional reads require one first contact and no linked extra contact; flags exclude hitscan, stuck, engine gravity and AlwaysHit/redirected paths. Zero/invalid timestep, unread flags, missing reset observation or incompatible movement remains unavailable. Config/profile bounds match supported ordinary G1/G7 diagnostic use, with BC 0.05..2. This is not a general projectile-family contract.

## Terrain snapshot

Historical hash-verified decoded movement code at 00930150 calls the terrain query; 00930155..00930169 tests floor-candidate.Z > 30; 0093016B..00930186 copies floor into Z and updates position. It does this even when the query returns false. The existing movement-body and constant fingerprints already cover this branch. Source observations do not substitute for a new runtime trace.

The existing hook now retains a bounded, read-only pre-clamp sample only for a captured collision. The subsequent speed check requires that sample to reproduce the expected endpoint, and requires target, flags, region and point to match. Final position and accounting must equal the specific Z-only correction. A repeated sample invalidates the alternative proof. Query success is recorded, not used to pretend that the engine skipped its documented false-result branch. Existing terrain-repair writes retain their original applied-flight eligibility and collision exclusion.

Normal flight pays one additional guarded contact-head read at this already hooked boundary. Full contact reads occur only when a contact exists and its lifetime is in the bounded diagnostic cache. No polling/world scan, allocation, new lock or new hook is introduced. Once per eligible contact, one additional full-step integration checks the interval's input; max 60 RK4 substeps at the existing dt cap. This is a structural cost assessment, not a measured FPS guarantee.

## Collision-point investigation

In the pinned projectile snapshot, normal AddImpact code at 009BF810..009BF847 copies the passed contact position/rotation into ImpactData; it does not correct them to the NVO path. Missile virtual slot 32C (009B8900) forwards to that routine. At 009C1257..009C1375, a caller builds a point from its own ray origin/direction/fraction and submits it. The AlwaysHit branch around 009BF618 instead permits target-derived coordinates. None of these facts proves why the historical ray and our submitted curve differ by hundredths of a game unit. No guessed rounding epsilon or radius has been used to enlarge the point tolerance.

Engine snapshot provenance is recorded in ENGINE-EVIDENCE.json; captures stay local and are not redistributed. The new interval avoids deriving time from an unverified surface point. It does not claim to repair collision geometry or VATS accuracy. A future authoritative contact producer must bind the true sweep/time to the damage transaction or adopt an explicitly reviewed bounded gameplay policy; do not convert a diagnostic interval into a precise penetration result without that decision.

Pre-movement contacts retain an unavailable result because no checked timestep/vector exists. Handling their launch/preflight collision path is separate native work, with no current-speed/muzzle fallback in this packet.
