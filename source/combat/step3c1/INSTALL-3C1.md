# Packet 3C1 installation receipt

Installed version 306 on 2026-09-15 after user authorization: "how? proceed". Replaced only NVOCombatCore.dll and its matching PDB. Existing configuration, NVO assets, other NVSE files and activation retained. Installer verified 52 protected-file entries (51 distinct paths). Game was already closed; no launch, gameplay test or GECK operation by assistant.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3C1-20260915-125052-aa77328b`

DLL SHA256: 5d581c458470ff25e34e421842fb3352313fa0545a6f4e6b58463585305eff56

PDB SHA256: bf042bd22dfb0c325100a83a7de2f9ad1413f0b844d979030fad00c1c023b9d0

The game-root logs were copied into the backup before a future launch. Version 305's six-shot log also remains archived separately in source/combat/step3c/captures/2026-09-15-3C-bd94aae6ce5b/.

## Reversal

Close New Vegas and restore both files from the backup's originals/Data/NVSE/Plugins into the matching game directory. Leave NVOFlightPhysics.ini, NVOFlightPreview.ini, NVOFlightPilot.esp and NVO.esm unchanged. Temporary disabled pilot: enabled=0 in the existing physics INI and reload; keep it at 1 for the two-shot diagnostic. The backup restores unaccepted version 305, not an assertion of working physics.

## Pending user check

Two distant shots outside VATS: one private NVO Flight Hunting Rifle and one private NVO Flight 9mm with matching private ammunition. No reload/VATS/stress/video needed. Exit and report completion; read the game-root NVOCombatCore.log directly before another launch. This packet adds evidence for a missing movement route. It does not yet establish the root cause or a working gravity/drag connection.
