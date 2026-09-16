# Packet 3D1 installed - records/configuration update for build 311

Installed the two approved files and verified their hashes. 52 protected entries, including the native DLL/PDB, NVO.esm, other extenders, physics configuration, existing kit and activation files, verified unchanged. New Vegas was already closed. No assistant game launch, gameplay or GECK work.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3D1-20260915-172450-4aed956c`

Replaced files:

- `Data/NVOFlightPilot.esp` - SHA256 `0cb272358e7d7a8cd73eee8e4e5f2ab670ba5933bf5652e2351b972545415e74`
- `Data/NVSE/Plugins/NVOFlightPreview.ini` - SHA256 `fb1e590397deeb074d84286fd99a1232e5566a93ec2f75975e79cc0c4cff81a7`

To reverse this update, close the game and restore **both** files from this backup's `originals` directory into their matching paths below the game root. This returns to packet 3D, including its known SMG mapping error. No new game files were added. Keep the existing DLL and physics INI. The backup also contains logs and original hashes.

The DLL remains build311 / 0.3.11 and its log header still says phase3D. Verify this update by its file hashes and the SMG profile source `0017A2C6`; do not expect a new plugin version. Native code was not recompiled. All18 current native source/header files match the 3D release snapshot.

The source audit confirms four weapon-to-projectile mappings and all four private clone contracts. Only private PROJ01000808 changed; all ten other parsed records, including TES4, remain unchanged. One configuration value changed, plus the packet comment. Damage replacement is disabled.

Follow START-HERE.html: regular SMG short burst and one shot from each rifle at a farther unobstructed solid target, then one reload and a distant live-target Service Rifle VATS shot. The pistol result remains accepted. Gameplay acceptance of this correction is pending.

INSTALL-3D1-plan.json and INSTALL-3D1-result.json are immutable transaction records. The archived installer script is for audit; the executed copy is in the workspace tools directory.
