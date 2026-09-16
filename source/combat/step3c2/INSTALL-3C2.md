# Packet 3C2 installation receipt

Installed 307 / 0.3.7 on 2026-09-15. Closed exact FalloutNV.exe PID 22300 normally with CloseMainWindow; no forced termination, relaunch, gameplay or GECK work.

Replaced only Data/NVSE/Plugins/NVOCombatCore.dll and matching .pdb. Verified 52 protected entries (51 distinct paths), including existing INIs, ESM/ESP, dependencies and activation. Full plan/result are adjacent JSON files.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3C2-20260915-134208-acb1e65e`. Previous 306 pair is under `originals/Data/NVSE/Plugins/`; logs are at the backup root. The prior two-shot 306 gameplay capture remains independently archived under step3c1.

Build: `native/NVOCombatCore/out/build-29075-6525`, zero warnings, PE32 x86, exactly NVSEPlugin_Load / NVSEPlugin_Query. PDB GUID 8187e6ac-fc24-4fea-8701-497be05a2453 age 1.

DLL SHA256: 6b425cc2766849ddfbea128b473976492a5440023d3ab9cf7a405909fbc7379f

PDB SHA256: 7f8c978333dc394c0f808de33aadb31da5fad5e5d7a9bfaad10215e747ab4e4e

Full reversal: with the game closed, restore both matching previous files from the backup. Disable only flight edits by setting [Physics] enabled=0 in the existing NVOFlightPhysics.ini, then load again. Keep NVO.esm and NVOFlightPilot.esp active. No save deletion.

Runtime acceptance is pending. User check is two distant private shots outside VATS (one rifle, one pistol), then exit. Read game-root NVOCombatCore.log directly. Expected: matched baseline and nonzero applied/verified steps for both lives. Stop for review before any next packet.
