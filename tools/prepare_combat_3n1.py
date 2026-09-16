"""Prepare the manual Baron callback check. Does not write to the game."""
from pathlib import Path
import hashlib, html, json

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'source/combat/step3n1'
RELEASE = ROOT / 'release/NVO-Combat-Packet-3N1-Baron-Check'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
EXPECTED_ESM = 'ff7abd370ca67ca6868cef070c76e79450432b280ab4e391a64102bb7099c31e'

CHECK = r'''ref rCallback
ref rBackground
ref rCaps
array_var aHandlers
int iBackground
int iCaps
int iGroupsBefore
int iGroupsAfter
int iPassed
int iWritten
float fBefore
float fAfter
float fMargin

begin Function {}
    SetFunctionValue 0
    let rCallback := GetFormFromMod "NVO.esm" "0074CA"
    let rBackground := GetFormFromMod "NVO.esm" "0022E7"
    let rCaps := GetFormFromMod "FalloutNV.esm" "00000F"
    if (IsFormValid rCallback) == 0 || (IsFormValid rBackground) == 0 || (IsFormValid rCaps) == 0
        WriteStringToFile "Data\NVSE\Plugins\NVOBaronCheck.log" 1 "3N1 BLOCKED reason=missing_form%r"
        PrintC "NVO Baron check: missing required form. Stop and report this."
        return
    endif

    let iBackground := GetGlobalVariable rBackground
    let iCaps := Player.GetItemCount rCaps
    let fBefore := Player.GetAV Health
    let fMargin := (iCaps * 0.001) + 10
    let aHandlers := GetEventHandlers "OnHit" rCallback
    let iGroupsBefore := ar_Size aHandlers
    let iWritten := WriteStringToFile "Data\NVSE\Plugins\NVOBaronCheck.log" 1 "3N1 BEGIN background=%.0f caps=%.0f hp_before=%.6f handler_priority_groups=%.0f%r" iBackground iCaps fBefore iGroupsBefore
    if iWritten == 0
        PrintC "NVO Baron check: cannot write the log. Stop and report this."
        return
    endif
    if iBackground != 53 || iCaps < 5000 || iCaps > 10000 || fBefore <= fMargin || iGroupsBefore < 0
        WriteStringToFile "Data\NVSE\Plugins\NVOBaronCheck.log" 1 "3N1 BLOCKED reason=preconditions%r"
        PrintC "NVO Baron check: use a healthy new Brahmin Baron with 5000 to 10000 caps. Report BLOCKED if already correct."
        return
    endif

    Call rCallback Player Player
    let fAfter := Player.GetAV Health
    let aHandlers := GetEventHandlers "OnHit" rCallback
    let iGroupsAfter := ar_Size aHandlers
    let iPassed := 0
    if fBefore == fAfter && iGroupsBefore == 0 && iGroupsAfter == 0
        let iPassed := 1
    endif
    let iWritten := WriteStringToFile "Data\NVSE\Plugins\NVOBaronCheck.log" 1 "3N1 END expected_result=%.0f hp_after=%.6f handler_priority_groups=%.0f call_target=player call_attacker=player gameplay_setters=0%r" iPassed fAfter iGroupsAfter
    if iWritten == 0
        PrintC "NVO Baron check: could not finish writing the log. Stop and report this."
        return
    endif
    if iPassed
        PrintC "NVO Baron check: expected result recorded. No retired handler and HP unchanged."
    else
        PrintC "NVO Baron check: unexpected result recorded. Stop and report this."
    endif
    SetFunctionValue iPassed
end
'''
BAT = 'Call (CompileScript "NVOBaronCheck\\Check.txt")\n'
NOTES = '''# Packet 3N1 — short Baron retirement check

Purpose: observe the actual compiled return-only callback and absence of its OnHit registrations after the Baron start and after one reload. The packet adds a manual console batch plus one loose UDF. No auto-loader, event registration/removal, quest, perk, native hook or ESM edit. Native320, damage replacement OFF, all profiles/settings unchanged.

Use a disposable NEW GAME, Powerful -> Brahmin Baron, Quick Setup / level 1. Let character creation finish and wait five real seconds in gameplay. Stand somewhere safe, keep the starting caps, and leave god/immortal modes off. Do not use main-menu coc: this test needs the actual background start. No weapons, shots or combat encounters are needed.

1. Run `bat NVOBaronCheck` in the game console. Expect the green-console text reporting the expected result. Any error/BLOCKED: stop and report it.
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
'''


def main():
    assert hashlib.sha256((GAME/'Data/NVO.esm').read_bytes()).hexdigest() == EXPECTED_ESM
    files = {'NVOBaronCheck.txt': BAT,
             'Data/NVSE/user_defined_functions/NVOBaronCheck/Check.txt': CHECK}
    for root in (PACK, RELEASE):
        root.mkdir(parents=True, exist_ok=True)
        for relative, content in files.items():
            dest = root / relative; dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))
        (root/'README.md').write_text(NOTES, encoding='utf-8')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NVO 3N1 — Baron check</title>
<style>:root{color-scheme:dark}body{max-width:800px;margin:42px auto;padding:0 24px;background:#111b18;color:#e2e9dd;font:18px/1.65 system-ui}h1{font-size:32px}li{margin:15px 0}button{font:600 18px system-ui;padding:14px 22px;background:#c3dfaa;color:#122115;border:0;border-radius:6px;cursor:pointer}textarea{display:block;width:100%;box-sizing:border-box;height:54px;margin-top:16px;background:#0b1410;color:#e2e9dd;font:18px monospace;padding:12px}a{color:#c3dfaa}.note{border-left:3px solid #b7d29f;padding:12px 20px;background:#1a2a21}#status{min-height:1.7em}</style>
<h1>Packet 3N1: finish the Baron check</h1>
<p><b>Purpose:</b> confirm the retired ability cannot add damage and stays unregistered after reloading. No GECK work or shooting is needed.</p>
<div class="note">Use a disposable new character. Keep god mode and immortal mode off. Native combat damage replacement remains disabled.</div>
<ol><li>Launch New Vegas through your usual NVSE setup. Choose <b>New Game → Powerful → Brahmin Baron</b>. Use Quick Setup / level 1 and finish character creation. Keep the starting caps.</li>
<li>Stand somewhere safe and wait <b>five seconds in gameplay</b>. Open the console and run the command below. Expect <b>“NVO Baron check: expected result recorded”</b>.</li>
<li>Close the console. Make a separate manual test save, <b>reload it once</b>, wait five seconds in gameplay, then run the same command again.</li>
<li>Quit the game and reply <b>Finished</b>. I will read the logs directly.</li></ol>
<button id="copy">Copy test command</button><textarea id="command" readonly aria-label="Test console command">bat NVOBaronCheck</textarea><p id="status" role="status"></p>
<p>If you see an error or <b>BLOCKED</b>, stop and report it. Do not use main-menu <code>coc</code> for this check: it skips the background setup we need to verify.</p>
<p>Results: <code>Data/NVSE/Plugins/NVOBaronCheck.log</code> in your New Vegas folder. The two manual invocations append results; nothing runs automatically in gameplay.</p>
<p><a href="README.md">Technical notes, limits and removal instructions</a></p>
<script>document.getElementById('copy').addEventListener('click',async()=>{const t=document.getElementById('command'),s=document.getElementById('status');try{await navigator.clipboard.writeText(t.value);s.textContent='Copied';}catch(e){t.focus();t.select();s.textContent=document.execCommand('copy')?'Copied':'Press Ctrl+C';}});</script></html>'''
    for root in (PACK, RELEASE):
        (root/'START-HERE.html').write_text(page, encoding='utf-8')
    manifest = {'packet':'3N1', 'expected_esm_sha256':EXPECTED_ESM,
                'runtime_tested':False, 'damage_replacement':False,
                'payload':[{ 'relative_path':r, 'sha256':hashlib.sha256((PACK/r).read_bytes()).hexdigest()} for r in files]}
    for root in (PACK, RELEASE):
        (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    main()
