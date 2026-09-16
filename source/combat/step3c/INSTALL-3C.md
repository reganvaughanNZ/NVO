# Packet 3C installation receipt

Installed version 305 on 2026-09-15. Two files replaced and one new INI added. Fifty protected files verified unchanged, including other NVSE files, NVO assets and activation. No game launch or gameplay test by assistant.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3C-20260915-123257-690e4f37`

The first installer attempt requested closure of exact FalloutNV PID 25412 but stopped before creating a backup or changing game files while process exit finished. A follow-up read confirmed no running FalloutNV process and the old 304 DLL hash unchanged. The second attempt completed; its closed_processes array is empty because the game was already closed.

## Installed files

- `Data/NVSE/Plugins/NVOCombatCore.dll` — SHA256 `5c46ed77e0436550550e70d9c13bee68459fba86a71dee7c36b3db68d791263c`
- `Data/NVSE/Plugins/NVOCombatCore.pdb` — SHA256 `2a94b1ac726c76311223041efbe02201cd6772f265aba40e23794b7924b91d79`
- `Data/NVSE/Plugins/NVOFlightPhysics.ini` — SHA256 `7b6a2648eab03ea958bd4e934b91e1c44f747544646b5bea09376be65706cd5c`

## Reversal

Close New Vegas. Restore NVOCombatCore.dll and NVOCombatCore.pdb from the backup originals/Data/NVSE/Plugins directory into the corresponding game directory. Remove the new NVOFlightPhysics.ini. Keep NVO.esm, NVOFlightPilot.esp, NVOFlightPreview.ini and activation unchanged. For a temporary comparison use enabled=0 in the new INI and reload instead.

The game-root NVOCombatCore.log, nvse.log and jip_ln_nvse.log were archived in the backup. Runtime acceptance of new gravity/drag remains pending the six-shot user check.
