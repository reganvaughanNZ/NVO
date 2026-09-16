# Packet3F2 / native313 installed

Replaced only the DLL and matching PDB. Verified 53 protected entries unchanged. Closed processes: 1, under the user's existing permission. No assistant launch, gameplay or GECK operation.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3F2-20260915-200722-ac88ab5e`

- `Data/NVSE/Plugins/NVOCombatCore.dll`: `ad34527aced3296d090e99246cd8c603ee84a0c082851ee9f82a1680585ded04`
- `Data/NVSE/Plugins/NVOCombatCore.pdb`: `4fdb5044ef8c332da1079cb394291321c8d3ee9e2335f47af72f7afe34906101`

Rollback: close New Vegas and restore both files from the backup's originals/Data/NVSE/Plugins directory to the game's matching directory. This restores native312. Keep current3F ESP/INIs/kit and NVO/RD masters; no load-order or save changes are required.

New header0.3.13 / phase3F2; GetPluginVersion returns313. Terrain query correction and following accounting must be observed before accepting the gameplay fix. No change to damage authority, ammo tuning or HP save persistence. Follow START-HERE.html for the short VATS miss/reload/HP check.
