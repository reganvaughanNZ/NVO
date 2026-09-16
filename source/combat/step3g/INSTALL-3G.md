# Packet 3G / native 315 installed

Replaced only NVOCombatCore.dll and its matching PDB. Verified 53 protected entries unchanged. No game was running during installation. No assistant launch, gameplay or GECK operation.

Backup: C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3G-20260915-214555-36dd9ee1

- Data/NVSE/Plugins/NVOCombatCore.dll: fa21f4ad5e6c9b46ac8dec0ee1ed9d4177608668b22bab9cd48c0e73524505b3
- Data/NVSE/Plugins/NVOCombatCore.pdb: 1cacf622b7404d462d2c75696fb56cd0f9b92707ccf8a0b438e3a012e3e934bc

Rollback: close New Vegas and restore both files from the backup's originals/Data/NVSE/Plugins directory into the game's matching directory. This restores native 314. Keep the existing ESP/INIs/kit, NVO/RD masters, activation and saves.

Expected header: NVOCombatCore 0.3.15 / phase=3G. Plugin version: 315. New IMPACT_ rows are in the game-root NVOCombatCore.log. Follow START-HERE.html for a very close solid-object shot, normal live-target hit and farther live-target VATS hit. Flight/range/damage rules are unchanged; the prior terrain correction remains accepted. Collision geometry and candidate speed estimates await the user test.
