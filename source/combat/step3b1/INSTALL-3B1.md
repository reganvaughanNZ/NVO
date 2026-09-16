# Packet 3B1 installation receipt

Status: installed on 15 September 2026. NVOCombatCore **0.3.1 / 301**. Existing session authorization covered this installation and closing FalloutNV if needed. The game was already closed; no process was closed or relaunched.

Purpose: read-only matching and flight-input preview for the two pilot combinations. No flight/damage changes are enabled. No GECK edits or gameplay tests were performed by the assistant.

## Installed files

| File relative to game root | Verified SHA256 |
|---|---|
| Data/NVSE/Plugins/NVOCombatCore.dll | `064630e921e62911678d5e459b74839025404b31dd7dafd0588ea82f4cfdb2c3` |
| Data/NVSE/Plugins/NVOCombatCore.pdb | `1474aeedb6a8accc3729167afc454ecc88a46ed3c1d41904981e73e6f01ca070` |
| Data/NVSE/Plugins/NVOFlightPreview.ini | `213997f62df0c0c5b3a02f11c51e84b40a89ae4fe71aca8da434cc23f03f95dc` |

The installer replaced the two version-203 NVO binaries and added NVOFlightPreview.ini. It verified all **43 protected files unchanged**, including unrelated NVSE files, NVO.esm/NVO.bsa/NVO.override and ALTStartConfig.ini where present. JIP, ShowOff and ITR full-file hashes matched the inspected versions before installation. No old donor files were deleted or activated.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3B1-20260915-092815-e4cd75dd`

The backup contains the prior DLL/PDB under originals/Data/NVSE/Plugins, baseline logs, plan.json, before.json and result.json. There was no previous NVOFlightPreview.ini. To revert, close the game, restore both old binaries and remove only the newly added NVOFlightPreview.ini. Keep backups outside the game NVSE folder. No changes to plugins or saves need reversing.

Installer: tools/install_combat_3b1.ps1. Exact file plan: INSTALL-3B1-plan.json. It validates resolved target paths, refuses reparse paths, backs up/hashes before replacing, avoids overwriting potential mod-manager hardlinks and supports rollback. Mod-manager staging was not modified; later deployment may overwrite a direct installation.

Build: native/NVOCombatCore/out/build-10959-2104. Compiled/static checks passed with no warnings; DLL/PDB identities agree. Runtime acceptance awaits the user's log. Start with the five-shot check in START-HERE.html. Expected version command result: 301. Do not advance to flight writes before reviewing that capture.
