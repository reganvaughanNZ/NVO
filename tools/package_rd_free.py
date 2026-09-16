"""Package the audited xEdit output and the pending complete GECK sources."""
from pathlib import Path
import hashlib, html, json, shutil

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'source/combat/step3j'
OUT=ROOT/'release/NVO-Combat-Packet-3J-RD-Free'
NAMES=['NVOCombatBootstrapScript','ALTQscript','ALTStartQscript']
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'Data').mkdir(exist_ok=True)
(OUT/'Scripts').mkdir(exist_ok=True)
shutil.copyfile(SRC/'xedit-work/Data/NVO.esm',OUT/'Data/NVO.esm')
shutil.copyfile(SRC/'RD-REMOVAL-AUDIT.json',OUT/'RD-REMOVAL-AUDIT.json')
for name in NAMES:
    shutil.copyfile(ROOT/'source/combat/step3i/Scripts'/f'{name}.txt',OUT/'Scripts'/f'{name}.txt')

instructions='''# NVO Packet 3J: remove RD.esm

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

Close the game, GECK and mod manager. Copy NVO.esm and RD.esm from the receipt's backup folder to the game's Data folder, and restore the backup plugins.txt and loadorder.txt to C:\\Users\\regan\\AppData\\Local\\FalloutNV. Then use a save from before the migration. Keep any newly edited NVO.esm separately before rolling back. Do not restore only RD without the matching pre-migration NVO, because that would run two startup quests.

If Vortex manages these plugins, retire the old RD deployment there and retain the new NVO file. Redeploying the old package can restore the retired files. No Vortex database was edited.
'''
(OUT/'README.md').write_text(instructions,encoding='utf-8')
(SRC/'README.md').write_text(instructions,encoding='utf-8')
cards=[]
for n,name in enumerate(NAMES):
    code=(OUT/'Scripts'/f'{name}.txt').read_text(encoding='ascii')
    assert 'RD.esm' not in code
    cards.append(f'''<section><h2>{n+1}. {name}</h2><button onclick="copyScript('{name}',this)">Copy complete script</button>
    <a href="Scripts/{name}.txt">Open text file</a><details><summary>Show script</summary><textarea id="{name}" readonly spellcheck="false">{html.escape(code)}</textarea></details></section>''')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NVO 3J — RD removed</title><style>
:root{color-scheme:dark}body{max-width:860px;margin:40px auto;padding:0 22px;background:#10191b;color:#e7eeeb;font:17px/1.55 system-ui,sans-serif}h1{font-size:32px;line-height:1.2}h2{font-size:21px}section,.notice{background:#18282b;border:1px solid #36504c;padding:22px;border-radius:10px;margin:22px 0}a{color:#9fe1ca}button{background:#a9e9d0;color:#12221f;border:0;border-radius:6px;padding:13px 18px;font:600 16px system-ui;cursor:pointer;margin:0 16px 12px 0}button:focus-visible{outline:3px solid white}li{margin:12px 0}textarea{width:100%;height:300px;box-sizing:border-box;background:#0c1417;color:#dcece7;font:13px/1.4 monospace;padding:10px;margin-top:14px}.small{font-size:14px;color:#b5c7c1}details{margin-top:10px}</style>
<h1>RD removed from NVO</h1><p>The combat startup quest and script now belong to NVO.esm. RD's Player boosts and test records are retired. Your five health settings are preserved.</p>
<div class="notice"><strong>RD removal needs no GECK editing.</strong> The three scripts below finish the pending quiet startup repair. Use this packet instead of Packet 3I's old apply helper. <a href="INSTALL-RECEIPT.json">Installation and backup</a>.</div>
<ol><li>In GECK Extender, use <b>File → Data</b>. Set <b>NVO.esm</b> as the active file and load it. RD must not be requested.</li>
<li>Use <b>Gameplay → Edit Scripts</b>. Open each existing script below. Select all its code, copy the complete replacement, paste, then compile/save it. Keep the type <b>Quest</b>.</li>
<li>Save NVO.esm in the main GECK window, close GECK and reply <b>compiled and saved</b>. I will check the saved records before your next gameplay check.</li></ol>
<p>No new quest or record needs creating. Do not use Recompile All. If a compile fails, send its exact error.</p>
'''+''.join(cards)+'''
<p>Keep all official DLC, NVO.esm and NVOFlightPilot.esp enabled in the game. Native318 is unchanged and damage replacement remains off.</p>
<p>Use a fresh normal new game after the saved-record check. Existing saves can retain RD state; they have been left intact.</p>
<p class="small">File validation: 822 records load in xEdit with RD absent; no unresolved non-null references. Six existing donor records still have empty effects. The complete sources above await your GECK compilation.</p>
<p><a href="README.md">Details and reversal instructions</a> · <a href="RD-REMOVAL-AUDIT.json">Record audit</a></p>
<script>async function copyScript(id,button){const box=document.getElementById(id);try{await navigator.clipboard.writeText(box.value);button.textContent='Copied';}catch(e){box.closest('details').open=true;box.focus();box.select();button.textContent=document.execCommand('copy')?'Copied':'Press Ctrl+C';}}</script></html>'''
(OUT/'START-HERE.html').write_text(page,encoding='utf-8')
(OUT/'CREDITS.txt').write_text('NVO retains the original Alternative Start author credits and donor notices from the project. This packet migrates existing NVO/RD records. Master cleanup and validation performed using official xEdit 4.1.5f (TES5Edit contributors): https://github.com/TES5Edit/TES5Edit/releases/tag/xedit-4.1.5f . xEdit binaries are not included in this packet. No new donor license grant is asserted.\n')
manifest={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.name not in ('MANIFEST.json','INSTALL-RECEIPT.json')}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(package=str(OUT),files=len(manifest),script_buttons=page.count('Copy complete script'),native_changes=False)))
