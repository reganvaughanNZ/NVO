# Packet 3F installed — Hunting Rifle standard/AP/HP checkpoint

Installed the preview INI, private-projectile ESP and new console kit: two replacements and one new file. 52 protected entries verified unchanged, including NVO.esm/RD.esm, native DLL/PDB, other retained NVSE files, physics INI, older kits and both activation files. New Vegas was already closed. No assistant game launch, gameplay or GECK work.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3F-20260915-185053-e97206fc`

- `Data/NVOFlightPilot.esp` — SHA256 `bc522fba37ff5f7c5b622bf3a7cb53235d8daac587735d9ae920b042d0c7fe8f`
- `Data/NVSE/Plugins/NVOFlightPreview.ini` — SHA256 `f90c540d9201c492f699f05a9a02a13954fad8b3e45c3b750304b9b36bad5af4`
- `NVOFlightKit3F.txt` — SHA256 `387e095bb0a2a706a267378d584fb2e1fd7fbd1980e3c0c205ecd6f3ffa800f2`

To reverse: close New Vegas, restore **Data/NVOFlightPilot.esp** and **Data/NVSE/Plugins/NVOFlightPreview.ini** from this backup's `originals` directory to the matching game paths, then remove the new game-root **NVOFlightKit3F.txt**. Restore both files together. Keep the existing DLL, physics INI, older kits, NVO.esm and RD.esm. This returns to accepted 3E and does not undo the separate unused-file cleanup.

Native build311 /0.3.11/phase3D stays unchanged. Eleven loaded profiles and private projectiles080D/080E identify3F. The previous13 complete private records and9 profiles are preserved. All18 native source/header files match the accepted3D source snapshot. NVO damage replacement remains disabled. AP/HP flight inputs deliberately match standard .308 for an identity checkpoint; no claim of variant ballistic calibration.

Run `bat NVOFlightKit3F` in the game console after loading your prepared save and waiting three seconds. Fire standard → AP → HP → standard outside VATS at distant scenery. Select HP, finish switching, make a test save and load that save once. Wait three seconds, confirm HP and fire one HP VATS shot at a distant live target. Exit and report completion or any miss/selection change. Full instructions are in START-HERE.html and README.md. Gameplay acceptance is pending.

The plan/result are immutable transaction records. The release's installer copy is for audit; the executed workspace script is tools/install_combat_3f.ps1.
