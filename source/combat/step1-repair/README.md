# Step 1 repair: missing extender dependencies

Purpose: restore the commands needed by existing scripts before introducing NVO hit diagnostics. This packet is a personal repair copy of files already on this computer. It does not merge donor gameplay into NVO.esm.

## Install this small packet

1. Close Fallout New Vegas and GECK.
2. Extract `NVO-Dependency-Repair.zip` into a temporary folder. Copy the **three files** from its `Data/NVSE/Plugins` folder into:

```text
C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas\Data\NVSE\Plugins
```

The files are **johnnyguitar.dll**, **JohnnyGuitar.ini** and **ShowOffNVSE.dll**. If a file with the same name now exists, keep a backup outside Data before replacing a DLL; keep an existing customized JohnnyGuitar.ini instead of overwriting its settings. The inspected installation lacked these DLLs. No ESP/ESM checkbox or new GECK record is needed for this dependency repair.

This is a manual three-file installation. Later Vortex deployments can replace manually installed files, so keep this packet and its provenance available.

3. Launch the game through your usual xNVSE-enabled route and try the same start. Report whether the three precompile errors disappear. If they remain, provide the new error text and we will inspect that run's log before continuing.

No installation or testing has been performed by the assistant. No further combat packet should be enabled until this checkpoint is resolved.

## What is included

- **JohnnyGuitar 5.16**: your existing Vortex-staged DLL and INI, copied without modification. The INI enables its JIP 57.30 fixes and existing item-stack fix; its optional fleeing/shooting-angle changes remain at their staged values of 0. It is not a new NVO damage configuration.
- **ShowOff 1.84**: the DLL from your existing downloaded release ZIP. The source archive contains a DLL and debugging symbols, not an INI; only the DLL is needed here.
- **manifest.json**: source paths, file sizes and SHA-256 hashes.

The repair uses those existing versions rather than installing today's newer JohnnyGuitar release, whose published requirements include a newer xNVSE than the 6.3.10 observed in your test. Runtime compatibility of the copied pair still needs your check. There is no xNVSE update or native NVO DLL in this packet.

The purpose of ShowOff here is concrete: the three failing legacy NVOCombat UDFs call its AuxTimerStart, and two call AuxTimerTimeLeft. Restoring that dependency addresses a known compile blocker; further script issues may become visible afterwards.

## Related Step 1 status

The installed NVO.esm inspected during this review contains the working start-category changes, but no records with NVOCombatBootstrap in their Editor IDs. Successful compilation inside GECK does not by itself establish that the script and attached quest were saved into the file used by the game. After dependency repair, finish saving/attaching the corrected bootstrap using the existing packet 1 instructions. If the records already exist in the current GECK session, save those records rather than making duplicates.

The corrected copy-button source is `../step1/COPY-STARTUP.html`. It recognizes both JIP registration names. Recompilation of that correction has not yet been reported.

## Reversal

Close the game and GECK. Remove only the files newly installed from this packet, or restore the previous backed-up versions if you replaced them. Leave NVO.esm, JIP and the other installed files alone. There is no ESM change to reverse for this dependency repair.

## Upstream credits and requirements

This packet is for the user's local repair, not a combined public NVO release. Preserve upstream credits when redistributing any original dependency package.

- JohnnyGuitar: c6, carxt, lStewieAl, WallSoGB and upstream contributors. https://www.nexusmods.com/newvegas/mods/66927
- ShowOff: The Dormies, Demorome, Trooper, WallSoyGB and the contributors credited upstream. https://www.nexusmods.com/newvegas/mods/72541

Both upstream pages list the Microsoft Visual C++ runtime as a requirement. If a DLL still fails to load, inspect the new nvse.log for its load failure before adding more changes.
