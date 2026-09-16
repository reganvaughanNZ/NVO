# Packet 3E implementation and static evidence

The accepted 3D1 capture established the limited four-weapon flight/reload checkpoint. This packet adds three ordinary weapon/standard-ammo combinations without changing native source or rebuilding the DLL.

## Source and identity checks

The preparer reads the verified local FalloutNV.esm and supplied BallistX 5.4 archive. It uses exact stock weapon IDs rather than display-name matching, since the base game contains additional weapons with identical display names. Each addition must have:

- A WEAP record whose DNAM projectile reference matches the explicit engine source.
- An AMMO record contained in that weapon's referenced ammunition list, with no projectile override in its DAT2 field.
- One matching donor weapon row and one explicitly selected cartridge row. Engine source identity remains separate from donor cartridge identity, preserving the lesson from the SMG correction.
- A non-explosive missile projectile compatible with the existing native loader's validation.

The audit also checks for NVO overrides of the relevant stock weapons, ammunition and source projectiles. None were present during preparation. Runtime exact-match and source/clone checks remain authoritative if another provider changes the loaded data.

## Retained donor inputs

| Weapon | Barrel inches | Maximum velocity m/s | Peak travel inches | Drag model | BC | Derived muzzle m/s |
|---|---:|---:|---:|---|---:|---:|
| 10mm Pistol | 6 | 503 | 0.45 | G1 | 0.155 | 437.39130435 |
| .357 Magnum Revolver | 5.5 | 602 | 1.05 | G1 | 0.184 | 435.65789474 |
| .44 Magnum Revolver | 6.5 | 567 | 0.9 | G1 | 0.190 | 444.03614458 |

Muzzle speed follows the existing donor formula `maximum * barrel / (barrel + 2 * peak)`. These values are inherited tuning, not independently verified real-world specifications. In particular, the donor's 10mm weapon comment questions its real-world model analogy. Donor damage numbers and zeroing/spread values are not applied by this packet.

## Record and configuration changes

Append PROJ0100080A, 0100080B and 0100080C under the existing PROJ group. Clone the actual original projectile's full subrecords, preserving model, range and all other properties except the private Editor ID/display name and the established flight changes: clear only the hitscan flag, set gravity to zero, and set base speed to the derived muzzle speed times70.

All DATA bytes beyond offset12 and the projectile type remain unchanged. Unused or opaque source fields are preserved, not interpreted or normalised. Check all seven ordinary source/clone pairs against the native loader contract. The previous ten private record payloads and complete record bytes remain identical. The TES4 HEDR record/group count becomes16 and next local ID080D; its description is updated. No stock record overrides, new masters, quests, scripts or placements.

Append the new profiles after the six existing sections, preserving previous profile indices and values. The result has nine profiles, below build311's16-profile capacity and16KB input limit. The canonical native preview INI is updated. The existing physics configuration and integrator remain intact.

`NVOFlightKit3E.txt` contains six AddItem commands for the verified three weapons and standard ammo. It grants100 rounds per weapon. No equipment replacement, healing, stat changes, god-mode toggling or quest edits. Earlier kit files remain available.

## Native and installation boundary

Use the installed build311 DLL/PDB unchanged. Its log header remains `0.3.11 | phase=3D`; nine loaded profiles and the new projectile IDs distinguish this update. No new native hooks, binary/source edits, altered guards/tolerances or damage authority. Unsupported ammunition combinations continue through the existing fallback.

The three-file installer retains preimage/hash checks, exact target paths, backups, protection of other NVSE files/NVO.esm/activation, hardlink-safe file replacement and rollback. It may close the exact FalloutNV executable under existing user authorization. It never launches or tests the game. Old releases and transaction receipts are retained.

`RECORD-AUDIT.json` includes donor rows, source/clone fields and identity checks. `STATIC-CHECKS.json` records source preservation and binary/record checks. The release is an Update requiring3D1, not a standalone native package. Source tools and a baseline snapshot are included for audit; they use the configured local workspace and donor paths.

Gameplay acceptance requires the four-shot checkpoint. Special ammunition, exact collision-time velocity/energy, unit calibration and later armour/physiology/damage authority remain separate work.
