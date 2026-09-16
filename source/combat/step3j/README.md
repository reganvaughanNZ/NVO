# NVO Packet 3J: remove RD.esm

Purpose: NVO owns its combat startup quest and script. RD is no longer a required master.
This supersedes Packet 3I's staged Player override and its APPLY-PLAYER-BASELINE helper. Do not use that older helper.

The assistant installs Data/NVO.esm and archives RD.esm outside the game. See INSTALL-RECEIPT.json for the exact backup. RD removal itself needs no GECK edits. All official DLC, NVO.esm and NVOFlightPilot.esp remain active. Native318 and damage-disabled configuration stay in place.

## Finish the pending quiet startup repair in GECK

These three complete sources carry forward the prepared Packet 3I work. They have NOT been compiled in GECK by the assistant. The installed RD-free ESM still has its previously compiled script bodies.

1. Open your usual GECK Extender. File > Data: select NVO.esm, click Set as Active File, then OK. RD.esm must not be loaded or requested. Let GECK load the official masters. Leave NVOFlightPilot.esp enabled for the game; it need not be selected for these script edits.
2. Gameplay > Edit Scripts. Open the EXISTING NVOCombatBootstrapScript. In the code area press Ctrl+A. Use its Copy button on START-HERE.html, paste the entire script, then compile/save the script. Keep Script Type = Quest. Do not create a new script or rename it.
3. Do the same for EXISTING ALTQscript and ALTStartQscript using their own Copy buttons. Do not use Recompile All.
4. Save NVO.esm from the main GECK window, close GECK, and tell me "compiled and saved". I will read the saved file before the next gameplay checkpoint. If a script fails, give me its exact error instead of trying line-number edits.

The migrated start-enabled quest NVOCombatBootstrapScriptQ is already linked to NVOCombatBootstrapScript. Do not create, relink or start another quest. Both now belong to NVO.esm, with local IDs 01941B and 01941A respectively.

## What changed

- RD's five test/Player/perk records are retired. Its bootstrap quest and compiled script were copied into NVO with new NVO-owned identities.
- Official xEdit 4.1.5f cleaned unused master declarations and remapped references. No reference was changed through a blind hex replacement.
- NVO retains all 819 original non-header records, all 269 compiled script blocks, and all five of your health GMSTs. Two bootstrap records were added.
- xEdit loaded all 822 records with RD physically absent. It found no unresolved non-null references. Six existing empty donor effects still report NULL effect definitions. These are not RD dependencies; their definitions need a separate future review.
- xEdit canonically sorted dialogue/list data, emitted NULL placeholders for those six empty effects and made existing actor reference 00160845 persistent. The audit documents these save normalizations; this is not a zero-byte-change claim for unrelated serialized records.
- The new master list is FalloutNV.esm, DeadMoney.esm, HonestHearts.esm, LonesomeRoad.esm, OldWorldBlues.esm. All other official DLC remains explicitly active even though NVO did not directly reference its records.

## Later gameplay checkpoint

After the saved-record review, start a disposable NORMAL new game, choose a background and note level, Endurance and HP. Save and reload once to check startup. Old saves can retain RD's actor/quest state and may warn about the removed content; a main-menu coc is not a clean character-generation check. No saves were deleted. This does not promise a particular displayed HP value.

## Reversal

Close the game, GECK and mod manager. Copy NVO.esm and RD.esm from the receipt's backup folder to the game's Data folder, and restore the backup plugins.txt and loadorder.txt to C:\Users\regan\AppData\Local\FalloutNV. Then use a save from before the migration. Keep any newly edited NVO.esm separately before rolling back. Do not restore only RD without the matching pre-migration NVO, because that would run two startup quests.

If Vortex manages these plugins, retire the old RD deployment there and retain the new NVO file. Redeploying the old package can restore the retired files. No Vortex database was edited.
