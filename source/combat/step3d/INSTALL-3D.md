# Packet3D / build311 installed

Installed six approved files; five replaced and one new kit file. 48 protected entries, including NVO.esm, other extenders and activation, verified unchanged. New Vegas was already closed. No assistant game launch, gameplay or GECK work.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3D-20260915-165232-25cd5ab3`

With the game closed, restore these five files from the backup's `originals` directory to the same relative paths below the game root:

- Data/NVSE/Plugins/NVOCombatCore.dll
- Data/NVSE/Plugins/NVOCombatCore.pdb
- Data/NVSE/Plugins/NVOFlightPreview.ini
- Data/NVSE/Plugins/NVOFlightPhysics.ini
- Data/NVOFlightPilot.esp

Remove the new game-root NVOFlightKit.txt to complete reversal. Do not mix the old DLL with schema2 INIs. The backup also preserves logs and original hashes. The original six private records remain unchanged in the expanded ESP; no stock forms or NVO.esm were overridden.

Build out\build-32754-5840, zero compiler warnings/errors. PE32 x86, exactly NVSEPlugin_Query and NVSEPlugin_Load, matching PDB GUID 305ee840-3201-4e1a-99a1-6a4265cdc933 age1.

DLL SHA256 f91a5e6e363443a9a0ce0be6803cdb05b758122cb9e0486ad4805b5ebfb99255

PDB SHA256 fe6156cb49d988022317c4b117f4ae3d6b5034959c3a98473a65da249968560e

Run `bat NVOFlightKit` after loading a test save and waiting three seconds. Follow START-HERE.html for the four-weapon checkpoint and one reload/Service Rifle VATS shot. Native damage replacement remains disabled. Runtime acceptance is pending; a successful installation is not a gameplay pass.

INSTALL-3D-plan.json and INSTALL-3D-result.json record the exact transaction. Do not regenerate pre-install hashes after installation.
