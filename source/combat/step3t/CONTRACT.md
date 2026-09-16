# Distance and clock contract — Packet 3T

## Adopted scale, not a claim of physical calibration

Define one NVO simulation metre as 70 game-coordinate units, retaining the existing BallistX-based configuration. This is a model convention. A muzzle-speed profile in m/s becomes coordinate speed by multiplication by 70; world displacement returns to model metres by division by the same value. Do not multiply speed, gravity or energy by an additional Havok conversion. This path operates on projectile world displacement, not rigid-body velocity or imported heightmap coordinates.

The local primary donor reference is `source/combat/step3b2/timing-investigation/BallistXMain-reference.txt`, notably its `GetProjectileRefDistanceTraveled/70` conversion. The current preview and physics INIs both use 70. The current movement argument and baseline observations satisfy the round-trip convention. This evidence verifies consistency, not the real-world size of a terrain cell or an actor mesh.

Changing the authored convention later requires rebuilding/revalidating the matching profile and movement conversion together. It must not silently reinterpret previously calculated velocities. No scale change is part of this packet. Packet 3S's conditional outputs and permanently false damage-authority flag stay unchanged.

## Primary engine/source trace

The decoded engine capture is `source/combat/step3b2/timing-investigation/runtime-20260915-102703/projectile-code-009B7000.bin`. Its manifest SHA256 is rechecked by the audit. Inspect the corresponding runtime disassembly, not the packed on-disk EXE disassembly. Address ranges and byte-slice hashes are preserved in RESULT.json; captured game bytes are not redistributed.

1. `009BECE0–009BECEA` obtains the base timer delta from the timer object at 011F6394 through 0084D030 and stores it in the parent local at -0C.
2. `009BECED–009BED4C` checks the VATS camera object at 011F2250, mode 4, and a projectile flag. Depending on projectile source (player or VATS target), it may multiply that local by a helper's result. Supplied JIP GameUI.h identifies the VATS camera object and target global. We do not infer specific helper return values from an address alone.
3. `009BEF7A–009BEF8F` passes the resulting local to virtual +310 (the missile UpdateProjectile at 009B8030). `009BEF91–009BEFA0` adds the same local to lifetime +D8 **after** the virtual call returns. The recorded next-update lifetime follows this order, including the older user-labelled VATS capture.
4. The guarded missile update forwards its argument through the supported movement calls at 009B83E5 and 009B847C. At `009BF309–009BF333`, the wrapper constructs the local forward displacement from speed times that argument. It then passes both displacement and argument to 009BF370.
5. `009BF3D5–009BF3FE` may divide the later movement argument by the current time multiplier when the source's actor value 0x33 is positive. Supplied JIP GameForms.h names 0x33 Turbo. The prior displacement is not rebuilt there. The helper at 00716440 reads 011AC3A0, also named currentTimeMult in supplied NVSE GameAPI.cpp. This is a later Turbo-related correction, not evidence that NVO must divide all VATS velocities by a fixed factor.

The NVO stack contract reads the wrapper's preserved argument, verifies its owners/callers, and integrates using it. It does not read wall-clock frame time or apply another VATS multiplier. Therefore use this incoming projectile delta as the model's simulated elapsed time. A scene in slow motion may take more wall-clock time to reach the same simulated flight state; that alone must not change the energy calculation.

## What the executable checks prove

The offline harness extracts the actual vector helpers, Cd interpolation, acceleration and RK4 Integrate implementation from current FlightPhysics.cpp. Only a minimal profile shim supplies drag model and ballistic coefficient; no engine function is executed. Actual donor drag tables are included unchanged. The harness reconstructs the horizontal velocity magnitude from logged total speed and vertical velocity. This is valid for this integrator because horizontal drag is rotationally symmetric and gravity acts only on Z; it would need revision if wind or anisotropic forces are added.

Each replay checks final speed, vertical speed, displacement magnitude and vertical displacement against the nine-significant-digit log. The comparison budgets are 1e-5 m/s and 1e-4 coordinate units. These are serialization/replay budgets, not physical measurement uncertainties and not collision tolerances. Reported maxima are much smaller.

The partition checks compare the same total simulated second with different step partitions. They cover the two current G1/G7 pilot coefficient profiles, numerical convergence and the absence of an extra clock multiplier in this model. They do not emulate the full VATS camera, engine callbacks, aimed-hit correction, collision, scheduling or another mod's hooks. The zero-drag cases also use an analytic constant-gravity result, giving an oracle independent of partitioning the same code.

An intentionally wrong-clock fixture uses a tenfold difference between parent and later delta: dividing an unchanged displacement by the wrong delta yields one-tenth of the speed and one-hundredth of the kinetic-energy value. The production clock choice avoids that fixture error; no actual tenfold Turbo case was present in the selected runtime captures.

## Remaining gates

The clock-selection and authored-unit conventions are settled for this inspected path; they should no longer be treated as an unexplained conversion guess. They are not a blanket `unitsCalibrated=true` permission for live damage. The upstream parent/VATS code is historical snapshot evidence, outside the full current movement fingerprint. Any future authority adapter must validate its supported producer/compatibility conditions and leave unsupported cases untouched.

In particular, the first segment remains engine-owned and unintegrated by NVO; the contact model cannot claim drag/time evolution there. Off-chord contacts, multiple contacts, missing snapshots and source/target mismatches remain unavailable. Instantaneous contact speed, region/armour interpretation, AP/HP construction, authoritative damage boundary, exact-once application, difficulty scaling and other families remain separate work. Packet 3T does not lift Ultra HOLD or activate damage.
