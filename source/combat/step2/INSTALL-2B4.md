# Packet 2B4 installation - 15 September 2026

Installed NVOCombatCore 0.2.3 / integer 203 at the user's explicit request. The game was already closed. No game or GECK was launched.

Replaced only Data/NVSE/Plugins/NVOCombatCore.dll and NVOCombatCore.pdb. Installed hashes matched the prepared release. ITR's installed DLL matched the pinned 2.2.2 hash before installation. Forty-three protected files, including unrelated extenders and NVO.esm/BSA/configuration, retained their hashes. No donor, game plugin, save, or extender was removed or changed.

Backup: C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-2B4-20260915-075903-dfdc3637

The backup contains the previous version-202 DLL/PDB under originals/Data/NVSE/Plugins, copies of NVOCombatCore.log/nvse.log/jip_ln_nvse.log, plan.json, before.json and result.json. The previous capture is also preserved under source/combat/step2/captures/2026-09-15-2B3-e5f160c3dba7.

DLL SHA256: cea7097b58bbcfc11d4cf32465ac2add91837a70b2506545b8e77af84bcc1fb4
PDB SHA256: d7609d238203584a18496be441938488563ea6e7cccf4d0fa0ca6386678686e6

Build: native/NVOCombatCore/out/build-26602-31189. No compiler warnings. PE32/x86, two NVSE exports, KERNEL32 imports, matching full PDB GUID/age. Corresponding source and evidence are packaged in release/NVO-Combat-Packet-2B4-Compiled.zip and Source.zip. The release manifest describes preparation time; this receipt records installation on this machine.

Purpose: additional ITR hit/prehealth input observers with independent limits, alongside existing copy/ammo diagnostics. New callbacks do not read/write mutable multiplier slots or set event results. No damage replacement, medicine, physiology, ballistics, AI or save serialization is enabled. Successful source/build inspection is not runtime validation.

Next action belongs to the user: open release/NVO-Combat-Packet-2B4-Compiled/START-HERE.html, perform the short body/melee/reload capture and send the game-root NVOCombatCore.log before another launch. Pause for review after that capture; do not start the next implementation packet automatically.

Reversal: close FalloutNV; restore both previous DLL/PDB from the backup originals directory to Data/NVSE/Plugins. Keep DLL backups outside the game NVSE folder. Mod-manager staging was not changed, so a later deployment could overwrite this direct installation; recheck GetPluginVersion after such deployment.
