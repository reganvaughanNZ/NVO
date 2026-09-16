# Packet 2B3 installed

Installed on 2026-09-14 at the user's explicit request. Fallout New Vegas process 8176 closed normally through its window; force termination was not needed. The game was not restarted or tested.

Installed NVOCombatCore 0.2.2 / plugin version **202**, including the matching PDB. Both installed SHA256 values match the compiled release manifest. The old 2B2 DLL was backed up before replacement.

Archived and removed 26 superseded files:

- Seven packet 2A diagnostic files: its loader, five callback UDFs and configuration.
- Fifteen legacy NVOCombat UDFs and their Sandbox.ini. Inspected current loose files and all installed non-Bethesda plugin records contained no external callers to these helpers. NVO.bsa contains only Alternate Start assets, without NVSE scripts. These helpers are not needed by packet 2B3.
- Three generated NVO logs, including the prior game-root native log, retained in the backup. The next game launch creates a fresh native log.

Backup folder: `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-install-2B3-20260914-230207-7b0c785d`

`originals` preserves paths relative to the game root. `before.json` records original hashes and protected files; `plan.json` lists exact actions; `result.json` records completion. The old nvse.log and jip_ln_nvse.log are also copied for reference. Every original was copied and hash-verified before removal. No recursive deletion was used. Replaced files were unlinked before copying, protecting possible mod-manager hardlinks.

43 protected files were hash-verified unchanged, including the unrelated NVSE extenders/configuration and the existing NVO.esm, NVO.bsa, NVO.override and ALTStartConfig.ini. No game plugin, save or unrelated extender was removed.

## Next user action

Launch through your usual xNVSE route. `GetPluginVersion "NVOCombatCore"` should return **202**. Complete the short combat/reload capture in the packet's START-HERE.html and send game-root NVOCombatCore.log. The old NVOCombatDiagnostics.log is retired. Gameplay validation is still pending; damage replacement remains disabled.

The compiled release's original `installed_by_assistant: false` records its preparation-time status. This installation receipt supersedes that for this machine; the release archive remains unchanged.

## Reversal

Close New Vegas first. Restore the original files from this backup's `originals` directory to matching paths beneath the game root, replacing the new NVOCombatCore.dll. Remove the newly introduced NVOCombatCore.pdb when restoring the previous DLL, because no matching old PDB was installed. Restoring the old diagnostic files reactivates packet 2A on the next launch. The archived native log is historical, not a capture from version 202.

The mod-manager staging area was not changed. A later mod-manager deployment may restore files from its own older packages; retain this receipt and current packet when changing that setup.
