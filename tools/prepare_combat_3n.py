"""Prepare complete GECK sources from the installed originals; never writes game files."""
from pathlib import Path
import hashlib, html, json, re, shutil
from verify_combat_3i import parse, text, variables, source_key

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'source/combat/step3n'
REL = ROOT / 'release/NVO-Combat-Packet-3N-Disabled-Model'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
REF = Path(r'C:\Users\regan\Desktop\NVO Mod References (Open Source)\NVSE-master (1)\NVSE-master\nvse\nvse')
def sha(data): return hashlib.sha256(data).hexdigest()
def norm(s): return re.sub(r'\r+\n?', '\n', s)
def save_json(path, value): path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')

PACK.mkdir(exist_ok=True)
(PACK/'Scripts').mkdir(exist_ok=True)
(PACK/'baseline').mkdir(exist_ok=True)
live = GAME/'Data/NVO.esm'
stamp = live.stat(); raw = live.read_bytes()
assert raw == live.read_bytes() and stamp.st_mtime_ns == live.stat().st_mtime_ns
expected = json.loads((ROOT/'source/combat/step3m/PACKET-RESULT.json').read_text())
for f in expected['installed_baseline_verified']:
    assert sha(Path(f['path']).read_bytes()) == f['sha256'], f'Baseline changed: {f["path"]}'
backup=PACK/'baseline/NVO.esm'
if backup.exists(): assert backup.read_bytes()==raw
else: backup.write_bytes(raw)
rows=parse(raw)
names=('ALTRichKidHit','ALTBackRichKidUDF','ALTQscript','NVOStartPreview')
sources={}; audits=[]
for name in names:
    original=[r for r in rows if r['kind']=='SCPT' and r['edid']==name]
    assert len(original)==1
    r=original[0]; old=norm(text(r['fs']['SCTX']))
    if name=='ALTRichKidHit':
        # Retain declaration names/order/types and parameter ABI, even iCaps.
        new=old[:old.lower().index('begin function')] + 'begin Function {rTarget, rAttacker}\n    return\nend\n'
    elif name=='ALTBackRichKidUDF':
        needle='\tSetEventHandlerAlt "OnHit" ALTRichKidHit 1::Player\n\tSetEventHandlerAlt "OnHit" ALTRichKidHit 2::Player\n'
        assert old.count(needle)==1
        new=old.replace(needle,'\tRemoveEventHandler "OnHit" ALTRichKidHit\n')
    elif name=='ALTQscript':
        needle='\t\telseif ALTBackground == 53\n\t\t\tSetEventHandlerAlt "OnHit" ALTRichKidHit 1::Player\n\t\t\tSetEventHandlerAlt "OnHit" ALTRichKidHit 2::Player\n'
        assert old.count(needle)==1
        new=old.replace(needle,'')
        anchor='\t\tif IsPluginInstalled "JIP LN NVSE" == 0'
        assert new.count(anchor)==1
        # Existing GetGameLoaded branch; after NVSE check, before other plugins.
        new=new.replace(anchor,'\t\tRemoveEventHandler "OnHit" ALTRichKidHit\n\n'+anchor)
    else:
        needle='You receive a 5,000-cap grant. Carrying more caps increases both damage dealt and damage taken. Wealth also makes you vulnerable.'
        assert old.count(needle)==1
        new=old.replace(needle,'You receive a 5,000-cap grant. Your starting wealth helps you buy equipment and supplies.')
    assert not re.search(r'SetEventHandlerAlt\s+"OnHit"\s+ALTRichKidHit',new,re.I)
    decl=lambda s: re.findall(r'^\s*(?:int|float|ref|string_var|array_var|short|long)\s+\w+\s*$',s,re.I|re.M)
    assert [x.strip().lower() for x in decl(old)] == [x.strip().lower() for x in decl(new)]
    sources[name]=new
    (PACK/'Scripts'/f'{name}.txt').write_bytes(new.replace('\n','\r\n').encode('ascii'))
    audits.append({'editor_id':name,'form':f'{r["fid"]:08X}',
        'script_type':'Quest' if name=='ALTQscript' else 'Object',
        'prior_variables':variables(r['parts']),'declarations_preserved':True,
        'baseline_compiled_sha256':sha(r['fs']['SCDA']),
        'replacement_sha256':sha((PACK/'Scripts'/f'{name}.txt').read_bytes()),
        'geck_compile_pending':True})
assert not re.search(r'(?i)damageav|\.kill\b|getitemcount',sources['ALTRichKidHit'])
msg=next(r for r in rows if r['kind']=='MESG' and r['edid']=='ALTRichKid')
description=norm(text(msg['fs']['DESC'])).split('\n\n+ Start')[0]+'\n\n+ Start with a 5,000-cap grant\n'
(PACK/'ALTRichKid-description.txt').write_bytes(description.replace('\n','\r\n').encode('ascii'))
save_json(PACK/'SOURCE-AUDIT.json',{'baseline_esm_sha256':sha(raw),'scripts':audits,
    'message':{'editor_id':'ALTRichKid','form':f'{msg["fid"]:08X}'},
    'unregister':'RemoveEventHandler "OnHit" ALTRichKidHit',
    'semantics':'Only this callback on OnHit, all its filter/priority registrations; does not remove other callbacks',
    'source_pins':[{'file':str(REF/n),'sha256':sha((REF/n).read_bytes())}
        for n in ('Commands_Script.cpp','Commands_Script.h','EventManager.cpp')],
    'native_compilation_is_not_GECK_compilation':True})

cards=[]
for a in audits:
    name=a['editor_id']; source=sources[name]
    cards.append(f'<section><h2>{html.escape(name)}</h2><p>Open the original Editor ID. Keep Script Type: <b>{a["script_type"]}</b>. Replace the entire source, then compile/save.</p><button onclick="copyText(\'{name}\',this)">Copy complete script</button> <a href="Scripts/{name}.txt">Open text</a><details><summary>Show full source</summary><textarea id="{name}" readonly>{html.escape(source)}</textarea></details></section>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NVO · Packet 3N — Baron retirement</title>
<style>:root{color-scheme:dark}body{max-width:920px;margin:40px auto;padding:0 24px;background:#111b18;color:#e2e9dd;font:17px/1.65 system-ui}h1{font-size:32px}h2{font-size:23px;color:#d0e1b7}a{color:#bcde9e}section,.notice{border:1px solid #455b49;background:#1a2a21;padding:22px;margin:24px 0;border-radius:8px}button{font:600 16px system-ui;padding:13px 20px;background:#c3dfaa;color:#122115;border:0;border-radius:5px;cursor:pointer}textarea{box-sizing:border-box;width:100%;height:280px;background:#0b1410;color:#dce9d8;padding:12px;font:13px/1.4 monospace}li{margin:10px 0}</style>
<h1>Packet 3N: retire the Baron ability</h1>
<p>The separate offline armour calculator compiled and passed <b>45 checks</b>. It is not in the game DLL and cannot change health. Its laser/plasma/flame/blast checks use synthetic profiles; live adapters and balance are still pending.</p>
<div class="notice"><b>Your step now: four original scripts and one message description.</b> The fourth script only removes the obsolete ability text from the start preview. No combat test, new quest, new script record, Recompile All or DLL installation is needed.</div>
<ol><li>Close New Vegas. Open GECK Extender and load <b>NVO.esm as the active file</b>.</li>
<li>Use <b>Gameplay → Edit Scripts → Script → Open</b>. Select each exact original name below, without a DUPLICATE suffix. Do not use New.</li>
<li>For each script, use its Copy button, select all source in GECK, paste and compile/save. Keep the stated script type. Existing reserved declarations are intentional.</li>
<li>In the Object Window, find <b>Miscellaneous → Message → ALTRichKid</b> (display name Brahmin Baron). Keep the Editor ID and title. Replace only its message/description text with the final Copy button below. Click OK.</li>
<li>Save <b>NVO.esm</b> in the main GECK window, close GECK and reply <b>SAVED</b>. I will verify the original records, compiled changes and variable slots before the next packet.</li></ol>
<p>Backup already stored in the project: <a href="../../source/combat/step3n/baseline/NVO.esm">pre-edit NVO.esm</a>. If you have other unsaved GECK changes, save a separate copy before proceeding.</p>
''' + ''.join(cards) + '<section><h2>ALTRichKid — message description only</h2><button onclick="copyText(\'description\',this)">Copy description</button><details><summary>Show description</summary><textarea id="description" readonly>'+html.escape(description)+'''</textarea></details></section>
<p>Wealth, starting equipment/location and other backgrounds are preserved. A replacement benefit and broader background review come later. The old function stays as a harmless compatibility record for saved references.</p>
<p><a href="README.md">Technical notes and reversal</a> · <a href="MODEL-CHECKS.txt">Offline check results</a></p>
<script>async function copyText(id,b){const t=document.getElementById(id);try{await navigator.clipboard.writeText(t.value);b.textContent='Copied';}catch(e){t.closest('details').open=true;t.focus();t.select();b.textContent=document.execCommand('copy')?'Copied':'Press Ctrl+C';}}</script></html>'''
(PACK/'START-HERE.html').write_text(page,encoding='utf-8')
model=ROOT/'native/NVOCombatModel'
build=(model/'out/build.log').read_text()
checks=(model/'out/results.txt').read_text()
assert 'RESULT checks=45 failures=0 gameplay_writes=0 synthetic_fixtures=1' in checks
assert not re.search(r'\b(?:warning|error) (?:C|LNK)\d+',build,re.I)
(PACK/'MODEL-CHECKS.txt').write_text(checks,encoding='utf-8')
save_json(PACK/'PACKET-RESULT.json',{'packet':'3N','native_runtime_version_unchanged':320,
    'engine_damage_replacement':False,'pre_damage_gate':'HOLD','offline_checks':45,
    'seeded_conservation_cases':4000,'repeated_pure_previews':10000,
    'build':'MSVC x86 /W4 /WX C++17 standalone executable','GECK_compilation':'pending_user',
    'baron_runtime_retirement':'pending_user_compile_save_and_verification',
    'installed_files_changed':[], 'baseline_esm_sha256':sha(raw),
    'baseline_assets':expected['installed_baseline_verified'],
    'model_sources':[{'file':n,'sha256':sha((model/n).read_bytes())}
        for n in ('ArmourModel.hpp','ArmourModel.cpp','tests.cpp','README.md','run_checks.cmd')],
    'fixture_executable_sha256':sha((model/'out/model_checks.exe').read_bytes()),
    'claims_not_made':['live_nonkinetic_adapter_support','calibrated_armour_balance','exact_once_engine_application','GECK_compile_success']})

REL.mkdir(exist_ok=True)
(REL/'Scripts').mkdir(exist_ok=True)
(REL/'Model').mkdir(exist_ok=True)
for name in names: shutil.copy2(PACK/'Scripts'/f'{name}.txt',REL/'Scripts'/f'{name}.txt')
for name in ('START-HERE.html','ALTRichKid-description.txt','SOURCE-AUDIT.json','MODEL-CHECKS.txt','PACKET-RESULT.json','README.md'):
    shutil.copy2(PACK/name,REL/name)
for name in ('ArmourModel.hpp','ArmourModel.cpp','tests.cpp','README.md','run_checks.cmd'):
    shutil.copy2(model/name,REL/'Model'/name)
files=[p for p in REL.rglob('*') if p.is_file() and p.name!='MANIFEST.json']
save_json(REL/'MANIFEST.json',{'packet':'3N','automatic_install_files':[],
    'files':[{'name':str(p.relative_to(REL)),'sha256':sha(p.read_bytes())} for p in files]})
print(json.dumps({'release':str(REL),'scripts':list(names),'offline_checks':45,'GECK':'pending','game_files_written':False}))
