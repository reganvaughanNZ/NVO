# Packet3F1 / build312 installed

Replaced only the native DLL and matching PDB. 53 protected entries verified unchanged, including the3F ESP/INIs/kit, NVO.esm/RD.esm, other extenders, old kits and both activation files. New Vegas was already closed. No assistant game launch, gameplay or GECK work.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3F1-20260915-192545-8f81aaf9`

- `Data/NVSE/Plugins/NVOCombatCore.dll` — `c0a1a17de412b16b4e0637a35b7bcd7f68c8df387f1a3217ef883bfd673c4e9e`
- `Data/NVSE/Plugins/NVOCombatCore.pdb` — `061998ad2b5f34830d92bc2960bd7f23ca1036b5e31ca8b874f5f32333bb3403`

To reverse: close New Vegas and restore **both** Data/NVSE/Plugins/NVOCombatCore.dll and NVOCombatCore.pdb from this backup's originals directory to the matching paths. Keep the3F ESP, INIs and existing NVOFlightKit3F.txt. This returns to311's diagnostic coverage, leaving3F profiles and the earlier cleanup intact.

The new header is0.3.12 /phase3F1 and GetPluginVersion should return312. Eleven profiles remain active. The compiled source preserves all flight/guard rules and eight assembly bridges. New bounded failure reports use the existing disk log and priority reserve; no console messages are added. The root cause of the movement failures and reported HP selection loss remain unresolved.

Follow START-HERE.html: one standard and one AP shot under the same long-distance missed-shot conditions, waiting10 seconds after each; load a test save once, manually selectHP, and one distant live-target HP VATS shot. Wait10 seconds, exit, and report which missed and the first two shots' aiming mode. Use the existing `bat NVOFlightKit3F` only if supplies are needed. No repeated full ammo cycle or stress test. The assistant will read the game-root NVOCombatCore.log before another launch.

Gameplay/diagnostic acceptance is pending. The plan and result are immutable transaction receipts; source, compiler output, PE/PDB identity and assembly evidence are bundled. The executed installer is tools/install_combat_3f1.ps1 in the workspace; the release copy is for audit.
