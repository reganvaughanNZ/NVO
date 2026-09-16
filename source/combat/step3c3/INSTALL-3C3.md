# Packet 3C3 installation

Installed version 308 on 2026-09-15. Replaced only Data/NVSE/Plugins/NVOCombatCore.dll and its matching PDB. Game was already closed at installation; no process was terminated or launched. 52 protected entries (51 distinct file paths) verified unchanged. No gameplay or GECK testing by assistant.

Backup: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-3C3-20260915-142855-45a3fc60`. Previous matching version 307 DLL/PDB are under `originals/Data/NVSE/Plugins/` in that folder. With the game closed, restore both files for full reversal. Original plan, file hashes and protected-entry inventory are retained in the backup; install result is INSTALL-3C3-result.json beside this receipt.

DLL SHA256: `983214ee467b8286983a132695550d6b0b37d781f1f3c766950e94dd565624e4`

PDB SHA256: `772ce0c188231ba21c642f137012925f36779b1a95a12ecf5a4ee5f2fa50252b`

Compiled build: `native/NVOCombatCore/out/build-4771-13594`, zero warnings/errors, PE32 x86, two NVSE exports. Matching DLL/PDB GUID a096bd9e-a268-4bc0-a5dd-f52231ca8684 age 1. Static checks only; the new movement-boundary capture awaits the user's two-shot test. No ESM/ESP/INI or activation edits; quiet-startup candidate remains uncompiled and uninstalled.
