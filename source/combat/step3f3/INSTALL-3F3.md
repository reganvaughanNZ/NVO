# Packet 3F3 / native 314 installed

Replaced only NVOCombatCore.dll and its matching PDB. Verified 53 protected entries unchanged. No game was running during installation. No assistant launch, gameplay or GECK operation.

Backup: C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3F3-20260915-205700-9cafdc74

- Data/NVSE/Plugins/NVOCombatCore.dll: 538969c607f87d53c38de4de7460f08a769c07f7ef904ac973b0b007613c2b95
- Data/NVSE/Plugins/NVOCombatCore.pdb: 359671087a82440207b62676e3e01b1f07fd8dd163e1dccfddfdc69d38a13c57

Rollback: close New Vegas and restore both files from the backup's originals/Data/NVSE/Plugins directory into the game's matching directory. This restores native 313. Keep the existing ESP/INIs/kit, NVO/RD masters, activation and saves.

Expected header: NVOCombatCore 0.3.14 / phase=3F3. Plugin version: 314. New FLIGHT_RANGE rows are in the game-root NVOCombatCore.log. Follow START-HERE.html for one hip-fired shot and the original distant VATS miss attempt. Flight/range/damage rules are unchanged; terrain-correction acceptance is still pending.
