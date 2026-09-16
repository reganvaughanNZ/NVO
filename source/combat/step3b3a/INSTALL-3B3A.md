# Packet 3B3A installation receipt

Installed 2026-09-15, local time 11:27. NVOCombatCore 0.3.4 / integer 304. User explicitly authorized preparing and installing this correction.

Only Data/NVSE/Plugins/NVOCombatCore.dll and NVOCombatCore.pdb were replaced. Their installed hashes match the release. Fifty protected files were verified unchanged, including other NVSE files, NVO assets, the pilot ESP/INI, and plugin activation. The three reviewed dependency hashes matched. Fallout New Vegas was already closed. No assistant game launch, gameplay test or GECK work.

Backup of version 303 and logs: `backups/combat-install-3B3A-20260915-112711-983b32e0`.

Build: native/NVOCombatCore/out/build-1432-18000. Win32 MSVC, zero compiler warnings/errors; expected exports, source boundaries, observer assembly and matching DLL/PDB identity inspected. GUID bec1638e-f5b8-48f2-b607-c7ae274b81d5, age 1.

DLL SHA256: 5782b506e2fd4b7dcc916f48587df247aa560ae390c1e8d6b4ade9bd19813f02

PDB SHA256: 5a9d09c5be7408a469593f72fa66b4533f91bfa04323ec4fcff9ec08dbc3d381

Rollback: close the game and restore both version-303 files from the backup's originals/Data/NVSE/Plugins folder to the same game paths. Unlink the two deployed files before copying if mod-manager hardlinks are used. Keep the current test ESP, INI and activation. No saves were changed.

Runtime acceptance is pending the user's four-shot/reload check in START-HERE.html. This correction admits projectile updates on their executing threads and shares lifetime impact/destruction state across callbacks. It changes no flight or damage settings. Read and archive the game-root log directly once the user reports completion, then ask before the next packet.

The archived failed timing capture and review remain under source/combat/step3b3. INSTALL-3B3A-plan.json and INSTALL-3B3A-result.json describe this exact transaction. The copied installer is workspace-specific; use the prepared guide for this already installed packet.
