# Packet 3S — impact-energy inputs

Purpose: establish traceable bullet mass and a strict contract for contact-speed estimates before armour consumes energy. This is an offline development packet. Native323 (0.3.23) remains installed; damage replacement remains OFF and the Ultra gate remains HOLD.

## Result

The new C++ module compiled for x86 with warnings treated as errors. All 61 focused checks passed. Reusing 19 logged contact records from 3G2 and 3Q produced four conditional energy estimates, eight unavailable candidates, two unsupported first-segment contacts, and five out-of-scope weapon profiles. Zero records are admitted as authoritative damage energy. This is not a fresh gameplay test or a collision-physics replay.

The four estimates belong to the previously captured .308 scenery contacts. They do not establish an actor-contact solution. Invalid/missing energy is represented by an empty optional / JSON null, not zero. An explicitly known zero speed has a separate zero-energy result in the synthetic checks.

## Your action

No GECK record, copy/paste script, loose game file, installation or repeat firing test is needed. You can leave the game closed. No game process was launched or stopped. The installed DLL/PDB hashes still match the normal probe-disabled native323 build. This packet cannot change combat behaviour.

There is no game rollback to perform. To set this work aside, retain native323 and do not integrate the separate ImpactEnergy module. Do not restore the 3R1 immediate backup merely to undo this packet: that backup contains the old diagnostic probe-enabled DLL.

## What was added

- `native/NVOCombatModel/ImpactEnergy.hpp/.cpp`: pure conditional estimate and rejection rules; no engine calls, armour conversion or damage application API.
- `ImpactEnergyProfiles.inl`: generated, narrow standard-9mm-pistol and standard-.308-hunting-rifle data. Actual donor archive, member hashes, units and rows were rechecked.
- `impact_energy_tests.cpp`: identity/session reuse, missing data, early contact, geometry, unit/time mismatch, AP/HP separation, nonfinite input, overflow and underflow checks.
- `tools/prepare_combat_3s.py`: repeatable source verification, fixture build and keyed replay of old diagnostic rows. Exact capture hashes and line numbers are recorded in `REPLAY-RESULT.json`.
- `CONTRACT.md`, `PROFILES.json` and `CHECKS.json`: the input contract, attribution and evidence.

The generated profiles use BallistX's selected 115-grain and 147-grain projectile masses. Conversion uses the grain-to-kilogram factor in [NIST SP 811](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b9). These are donor tuning values, not a claim about every real cartridge or winning game override. See CREDITS.md.

## Next packet, only after approval

Verify the world-distance and simulation-time convention, especially VATS, using the available source and captures first. Then determine which contact-speed producer can satisfy it without inventing first-segment or off-path values. Request a new gameplay check only if existing evidence cannot settle that specific point. Armour, damage scaling ownership, exact-once application and other projectile families remain later gates.

Energy alone does not decide penetration or injury. Special ammunition needs explicit construction/profile data. Grenades, lasers, plasma, thrown weapons and flames remain outside this bullet-energy packet; their family-specific rules are still in the plan.
