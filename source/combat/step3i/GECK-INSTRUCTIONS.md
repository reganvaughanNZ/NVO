# Packet 3I: apply once, compile three scripts, save

## 1. Apply the Player baseline

Save any current GECK edits and close GECK, New Vegas, Vortex and xEdit. If saving changes NVO.esm, the helper will stop instead of replacing the newer work; report that result so the packet can be refreshed.

From this release folder, run **APPLY-PLAYER-BASELINE.cmd** once. It copies `Staged/Data/NVO.esm` to the game Data directory after checking its exact starting hash, and creates a timestamped backup under `C:\Users\regan\Documents\ChatGPT\NVO\backups\combat-records-3I-*`. It reports the backup location. This step applies the Player override only; the startup scripts still need compilation below. Do not manually overwrite a file after the helper has reported a mismatch.

## 2. Edit the existing records in NVO.esm

Launch your usual GECK Extender. In File > Data, select **NVO.esm as the active file**. Keep RD.esm and all required masters loaded as masters. RD.esm must not be active. Keep your existing ESM-editing setup; no new plugin or quest is needed.

Use Gameplay > Edit Scripts and open each **existing** script below. Script Type stays **Quest**. Use its page button, select all existing script text, paste the complete replacement, and save/compile in the script editor. Do not duplicate/rename the scripts or run Recompile All.

| Order | Existing script | Replacement | Record identity |
|---|---|---|---|
| 1 | NVOCombatBootstrapScript | Scripts/NVOCombatBootstrapScript.txt | RD.esm local000DBE, saved as an override in NVO |
| 2 | ALTQscript | Scripts/ALTQscript.txt | NVO.esm local002900 |
| 3 | ALTStartQscript | Scripts/ALTStartQscript.txt | NVO.esm local0022E1 |

Load-order prefixes vary: identify by Editor ID and origin, not a hard-coded runtime prefix. The existing quest is **NVOCombatBootstrapScriptQ**, RD local000DBF. Its Script field already points to NVOCombatBootstrapScript. Keep that assignment, its Start Game Enabled flag and the quest itself. Do not create the similarly named quest suggested by an older packet. An override in NVO retains the existing script identity and quest linkage; the RD file itself stays unchanged.

Open Actors > NPC > **Player**, FormID00000007, to inspect the staged values if desired: base health100, SPECIAL5, speed multiplier100, fatigue200 and zero skill offsets. Base inventory contains the two original entries, not ReganGear. No manual Player editing is required. The distinction between Base Health and calculated health is described in the [GECK Stats tab documentation](https://geckwiki.com/index.php/Stats_Tab_-_NPC); your health game settings still apply.

After all three compile, **save NVO.esm from the main GECK window**. Stop this checkpoint and reply **“compiled and saved”**, or paste the compiler error with the script name. The assistant will check the saved record identities, source/compiled-data change, Player override and five preserved GMSTs before asking for the short startup check. No firing test is needed.

## Expected startup check after saved-record verification

Launch through NVSE. Start a disposable new game normally, select a simple background such as Mercenary, and finish character setup. Note the displayed HP, chosen Endurance and level; there is no promised fixed HP total. Save to a new test slot and reload once. Normal startup should show the existing choice menus without dependency popups or repeated foundation-success console lines. Real missing-dependency messages, if any, are console-only and once per process from the bootstrap. Compatibility warnings may still appear for real conflicts.

New-game testing matters: a main-menu `coc` skips character creation, and old saves may retain health, skill, inventory or script state from RD. Do not reset a kept character with SetAV/RemoveAllItems to make this check pass. No need to uninstall working dependencies just to trigger an error.

## Reversal

Close the game and save/close GECK. Preserve any later edits separately. Restore **NVO.esm** from the specific `backups/combat-records-3I-*` folder printed by the apply helper to the game Data folder, replacing the packet-edited copy. That backup is the complete pre-packet ESM, including its compiled scripts. RD was never changed. Keep native318, NVOFlightPilot.esp, dependencies and activation as before. Use the pre-test save; plugin reversal does not remove changes stored in a new save. The immutable preparation snapshot also exists at `source/combat/step3i/baseline/NVO.esm`; do not substitute an older release ESM.
