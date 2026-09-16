# Packet 3N1 — short Baron retirement check

Purpose: observe the actual compiled return-only callback and absence of its OnHit registrations after the Baron start and after one reload. The packet adds a manual console batch plus one loose UDF. No auto-loader, event registration/removal, quest, perk, native hook or ESM edit. Native320, damage replacement OFF, all profiles/settings unchanged.

Use a disposable NEW GAME, Powerful -> Brahmin Baron, Quick Setup / level 1. Let character creation finish and wait five real seconds in gameplay. Stand somewhere safe, keep the starting caps, and leave god/immortal modes off. Do not use main-menu coc: this test needs the actual background start. No weapons, shots or combat encounters are needed.

1. Run `bat NVOBaronCheck` in the game console. Expect the console text reporting the expected result. Any error/BLOCKED: stop and report it.
2. Close the console, make a separate manual test save, and reload it once. Wait five real seconds in gameplay, then run `bat NVOBaronCheck` again.
3. Quit the game and reply Finished. The assistant reads Data/NVSE/Plugins/NVOBaronCheck.log, NVOCombatCore.log and nvse.log directly.

Acceptance: two complete BEGIN/END pairs, background53, caps5000..10000, positive safe HP, zero matching handler-priority groups before/after, identical HP before/after, no script errors, and corroborating new-game/load lifecycle evidence in the native log. Merely seeing unchanged HP is not sufficient. Missing/stale/incomplete logs are not passes. The supplied command does not register or remove the handler, so it cannot make its own handler-absence check pass by repairing state first.

The direct call uses Player for both function arguments: both retired incoming/outgoing registrations used the same function, which now immediately returns. This is a narrow retirement check, not a synthetic hit event or proof of all combat paths. It does not validate native damage authority, armour/energy adapters, or migration of every old save. An existing pre-retirement Baron save would be separate evidence if later available. The health margin stops the call for an unwell character; the expected installed no-op itself performs no gameplay writes. Do not enable god/immortal mode, which could hide unwanted health changes. The helper does not toggle either mode or alter HP/caps/difficulty.

## Command provenance and limitations

Inspected supplied xNVSE Commands_Script.cpp: CompileScript caches relative files under Data/NVSE/user_defined_functions; GetEventHandlers takes event and optional script filter. With no priority argument it returns a map containing only nonempty matching priority groups; ar_Size0 means no registered match, NOT a general total-handler count. Commands_Array.cpp returns -1 for invalid arrays, which blocks this check.

Inspected supplied JIP functions_ln/ln_fn_game_data.h: GetFormFromMod resolves filename plus local hex ID against the current load order. Installed NVO.esm readback resolves ALTBackground0022E7 (value53 for Baron) and ALTRichKidHit0074CA. functions_jip/jip_fn_global_var.h GetGlobalVariable reads global->data. functions_jip/jip_fn_utility.h WriteStringToFile appends formatted text and reports successful file access. Call/CompileScript and file logging use the established packet2 loose-UDF approach. No fixed NVO load-order prefix or invented command is used.

Preparation checked the installed ESM hash and script/source identities from3N. The new loose helper has not been compiled/executed in the game by the assistant; xNVSE handles that on your launch. A runtime/parser error means stop, not pass. No combat model/native checks were rerun because they did not change.

## Reversal and later deletion

After review, archive/remove only NVOBaronCheck.txt from the game root and Data/NVSE/user_defined_functions/NVOBaronCheck/Check.txt. Keep the log as evidence. No DLL or ESM rollback is needed. The disposable test save can be left unused; no production save is altered by the assistant.

The user prefers eventual deletion of redundant background code. ALTRichKidHit is a temporary compatibility stub. Before deleting it during the background pass, remove its two explicit unregister references in ALTBackRichKidUDF/ALTQscript, recompile their originals while preserving variable slots, check compiled/external references, and decide the supported old-save transition. Do not delete unrelated reserved variable slots or records merely because a source search looks empty. Full record deletion is deferred as requested.
