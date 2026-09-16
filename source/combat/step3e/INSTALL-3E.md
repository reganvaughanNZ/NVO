# Packet 3E installed - three standard-ammunition profiles

Installed the approved preview INI, expanded private-projectile ESP and new console kit. Two existing files replaced and one kit added. 52 protected entries verified unchanged, including NVO.esm, the native DLL/PDB, other extenders, physics INI, older kits and activation. New Vegas was already closed. No assistant game launch, gameplay or GECK work.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3E-20260915-180454-ac04655d`

Installed hashes:

- `Data/NVOFlightPilot.esp` - SHA256 `39802a9f7c702f3fc1d74b2703ea019c4a6f835945a4add13d8d5cf18d276249`
- `Data/NVSE/Plugins/NVOFlightPreview.ini` - SHA256 `9e344ee367774454e16e5cc37a9ffd2487de1f3fbf7f83bdeb6a0aec11d5b4d3`
- `NVOFlightKit3E.txt` - SHA256 `bc3c0e83e840c8fd18b84a6783a1b3d8638ef87d798ed97d5a27f34ce88d3a9a`

To reverse, close the game, restore **Data/NVOFlightPilot.esp** and **Data/NVSE/Plugins/NVOFlightPreview.ini** from this backup's `originals` directory into the matching game paths, then remove the newly added game-root **NVOFlightKit3E.txt**. Restore both members of the record/config pair. Keep the existing DLL, physics INI, older kits and NVO.esm. This returns to the accepted 3D1 configuration. Logs and preimage hashes are also backed up.

The DLL remains build311 /0.3.11 and its header still says phase3D. There is no new native build. Nine loaded profiles and private projectile IDs080A..080C identify3E. All18 native source/header files match the3D source snapshot. All seven ordinary mappings/clones passed static checks; previous ten complete private records and six profile sections are preserved. Damage replacement remains disabled.

Run `bat NVOFlightKit3E` inside the game after loading your prepared save and waiting three seconds. It supplies the canonical 10mm Pistol, .357 Magnum Revolver and .44 Magnum Revolver plus100 standard rounds each. Follow START-HERE.html: one shot from each at distant scenery, one reload, then one .44 shot in VATS at a distant live enemy. No previous-weapon retest required.

Gameplay acceptance is pending. INSTALL-3E-plan.json and INSTALL-3E-result.json are immutable transaction records. The installer copy in this release is an audit copy; the executed script is in the workspace tools directory.
