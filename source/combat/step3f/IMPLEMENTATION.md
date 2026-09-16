# Packet 3F implementation

This bounded update adds explicit standard/AP/HP selection for one already accepted weapon. No native source is edited or rebuilt. The preparer checks all 18 current native source/header files against the build-311 packet 3D snapshot and verifies the installed dependencies and accepted 3E files.

## Why the Hunting Rifle

The verified base-game Hunting Rifle (00004333) uses projectile 0008F20A and ammunition list 001537E9. Standard .308 (0006B53C), .308 AP (0013E442) and .308 HP (0013E443) are all members. Each has speed multiplier 1, default shot-count field 0, no alternate projectile and no ignore-resistance/non-playable flag. Selection cannot distinguish these rounds from the weapon/source projectile alone.

The existing `FlightPreview.cpp` selector requires the exact weapon, the process's actual equipped ammunition and the original projectile. The post-creation path independently checks the actual weapon, ammunition and private projectile base before tracking. Distinct ammo keys are valid for the same weapon/source; the duplicate-key guards reject only identical selection tuples. Reusing these interfaces avoids another hook or native rebuild.

## Records and tuning

The existing standard profile and private PROJ01000807 remain unchanged. Append AP PROJ0100080D and HP PROJ0100080E. Each copies the complete original projectile subrecords, changing only the private Editor ID/name and the established flight fields: clear hitscan, zero gravity, and use the accepted muzzle velocity multiplied by 70. Type, model, range and all DATA bytes from offset 12 onward remain unchanged. The old 13 complete record byte sequences are preserved, with no stock WEAP, AMMO or AMEF overrides. Header record/group count becomes 18 and next ID 080F. The only master remains FalloutNV.esm.

Append `hunting-rifle-ap` and `hunting-rifle-hp` after the old nine profile sections, retaining all prior indices and values. Total 11 is below the native 16-profile capacity and the INI stays below 16KB.

All three use the previously accepted BallistX standard .308 inputs: G7 BC 0.209, maximum velocity 1012 m/s, barrel 22 inches, peak travel 2.1 inches. The donor formula gives 849.770992366 m/s. Keeping flight tuning constant makes this an identity checkpoint, not an AP/HP ballistic calibration. The stock AP/HP names are not automatically mapped to BallistX's separate converted ammunition family. No donor conversion scripts, alternate-ammo plugin, donor damage numbers or new assets are installed.

## Existing ammunition effects

The preparer follows AMMO RCIL references into the AMEF records. JIP's supplied `GameForms.h` enum establishes damage type 0, DT type 2, multiplication operation 1 and subtraction operation 2. The audit retains raw record fields and source hashes.

| Round | Existing effects preserved |
|---|---|
| Standard | No AMEF entries |
| AP | DT subtraction 15; damage multiplier approximately 0.95 |
| HP | DT multiplier 3; damage multiplier 1.75 |

These are existing record values, not new NVO damage rules or predictions of final damage. None of the retained non-base plugins overrides the selected weapon, source projectile, ammunition list, rounds or linked effects in this installation. Runtime guards still govern loaded projectile eligibility; the packet does not claim general compatibility with unknown runtime edits.

## Static checks and user acceptance

`RECORD-AUDIT.json` records source identities, donor rows, the three ammunition records/effects, two clone records, retained-plugin hashes and native selector provenance. `STATIC-CHECKS.json` records all 18 unchanged native source hashes, record preservation, profile order, distinct selection tuples, capacity and all three source/clone contracts. Full stock records are not rewritten. The .308 JSP Hand Load list member is deliberately not profiled.

The user checks standard → AP → HP → standard, then saves with HP selected, loads that save and fires HP in VATS at a live target. Inspect profile selection and actual creation/ammo agreement independently; require edited free-flight segments, clean load reset and linked HP hit context. A reported VATS miss is not a flight failure; distinguish absence of actor-hit evidence from selection/flight faults. Do not infer final HP loss, duplicated damage or penetration from engine-stage observations. NVO damage authority remains disabled.

## Installation

Update only the ESP, preview INI and new kit, with preimage hashes, verified backups, hardlink-safe replacement and rollback. Preserve NVO.esm/RD.esm, current dependencies, existing kits and both activation files. Existing permission permits closing the exact New Vegas process if needed; the installer never launches the game. Editor/mod-manager activity stops installation before mutation. Restoring both prior ESP/INI files and removing the new kit reverses this packet to accepted 3E. The earlier unused-file cleanup stays in effect.
