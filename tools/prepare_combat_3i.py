"""Prepare a Player-only staged ESM and complete GECK sources. Never install or compile."""
from pathlib import Path
import hashlib, html, json, re, shutil, struct, difflib, zipfile
from inspect_plugin import records, fields

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'source/combat/step3i'
BASE = OUT / 'baseline'
REL = ROOT / 'release/NVO-Combat-Packet-3I-Records'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
EXPECTED_NVO = '2bb53410287c1c409a0bbb9b51ef38bf14bba2a4e3376f23b5cfc9f73fc0028d'
EXPECTED_BASE = '44e654569d47fcf8ceddc576c26dd11a32f207e60b1fd23cd6089e1e5f8fa84b'

def sha(b): return hashlib.sha256(b).hexdigest()
def normal(s): return re.sub(r'\r+\n?', '\n', s)
def original(name, plugin='NVO.esm'):
    return normal((BASE / f'{plugin}-{name}.txt').read_bytes().decode('cp1252'))

def flat_raw(data, start=0, end=None):
    end = len(data) if end is None else end
    pos = start
    while pos < end:
        assert pos + 24 <= end
        size = struct.unpack_from('<I', data, pos+4)[0]
        if data[pos:pos+4] == b'GRUP':
            assert size >= 24 and pos+size <= end
            yield from flat_raw(data, pos+24, pos+size)
            pos += size
        else:
            stop = pos+24+size
            assert stop <= end
            yield data[pos:pos+4].decode(), struct.unpack_from('<I', data, pos+12)[0], data[pos:stop]
            pos = stop
    assert pos == end

def make_player_copy():
    old = (BASE/'NVO.esm').read_bytes()
    vanilla = (GAME/'Data/FalloutNV.esm').read_bytes()
    assert sha(old) == EXPECTED_NVO and sha(vanilla) == EXPECTED_BASE
    player = [raw for kind,fid,raw in flat_raw(vanilla) if kind=='NPC_' and fid==7]
    assert len(player)==1
    player = player[0]
    before = {(k,f): r for k,f,r in flat_raw(old)}
    assert len(before)==len(list(flat_raw(old))), 'Duplicate original record identity'
    assert ('NPC_',7) not in before
    # All copied references remain FalloutNV.esm references (master index zero).
    # Copy the entire original record, including its original header/flags.
    output = bytearray(); pos=0; inserted=0
    while pos < len(old):
        header=bytearray(old[pos:pos+24]); size=struct.unpack_from('<I',header,4)[0]
        if header[:4]==b'GRUP':
            body=old[pos+24:pos+size]
            if header[8:12]==b'NPC_' and struct.unpack_from('<I',header,12)[0]==0:
                body=player+body; inserted+=1
                struct.pack_into('<I',header,4,len(body)+24)
            output += header+body; pos+=size
        else:
            assert header[:4]==b'TES4' and pos==0
            body=bytearray(old[pos+24:pos+24+size])
            assert body[:4]==b'HEDR' and struct.unpack_from('<H',body,4)[0]==12
            count=struct.unpack_from('<I',body,10)[0]
            struct.pack_into('<I',body,10,count+1)  # Existing group; one added override.
            output += header+body; pos+=24+size
    assert inserted==1
    output=bytes(output)
    after={(k,f):r for k,f,r in flat_raw(output)}
    assert set(after)-set(before)=={('NPC_',7)} and not set(before)-set(after)
    assert after['NPC_',7]==player
    assert all(after[key]==value for key,value in before.items() if key!=('TES4',0))
    h1=bytearray(before['TES4',0]); h2=bytearray(after['TES4',0])
    struct.pack_into('<I',h1,34,count+1); assert h1==h2
    parsed=list(records(output))
    for k,f,fl,p in parsed: list(fields(p))
    masters=[v for t,v in fields(parsed[0][3]) if t=='MAST']
    assert masters==[v for t,v in fields(next(records(old))[3]) if t=='MAST']
    (OUT/'Staged/Data').mkdir(parents=True,exist_ok=True)
    (OUT/'Staged/Data/NVO.esm').write_bytes(output)
    audit=dict(baseline_sha256=sha(old),vanilla_sha256=sha(vanilla),staged_sha256=sha(output),
        staged_bytes=len(output),added_record='NPC_:00000007 Player',copied_record_sha256=sha(player),
        preserved_existing_records=len(before)-1,all_existing_non_header_records_byte_identical=True,
        header_change='HEDR record/group count +1 only',masters_unchanged=True,gmst_count=5,
        player_policy='Complete vanilla Player base record overrides RD. Character creation/background scripts still select the character. No runtime SetAV, inventory cleanup, or save edits.',
        compiled_scripts_changed=False,installed=False,geck_compiled=False,gameplay_tested=False)
    (OUT/'PLAYER-RECORD-AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
    return audit

GATE = '''if GetNVSEVersion < 6
    Return
elseif GetNVSEVersion == 6
    if GetNVSERevision < 3
        Return
    endif
endif
if IsPluginInstalled "JIP LN NVSE" == 0
    if IsPluginInstalled "JIP NVSE Plugin" == 0
        Return
    endif
endif
if IsPluginInstalled "JohnnyGuitarNVSE" == 0
    Return
endif
if IsPluginInstalled "ShowOffNVSE Plugin" == 0
    Return
endif
'''

def make_sources():
    dest=OUT/'Scripts'; dest.mkdir(exist_ok=True)
    boot=original('NVOCombatBootstrapScript','RD.esm')
    boot=boot.replace('float fQuestDelayTime\n','float fQuestDelayTime\nshort bReportMissing\n',1)
    boot=boot.replace('    set fQuestDelayTime to 1\n','    set fQuestDelayTime to 1\n    set bReportMissing to 0\n',1)
    boot=boot.replace('    if GetGameRestarted\n        set bChecked to 0','    if GetGameRestarted\n        set bReportMissing to 1\n        set bChecked to 0',1)
    # Preserve existing state/declaration order. New reporting flag is appended.
    quiet=normal((ROOT/'source/combat/step3c3/NVOCombatBootstrapScript-quiet.txt').read_bytes().decode())
    check=quiet[quiet.index('    if iNVSEMajor < 6'):quiet.index('\nEnd')]
    check=check.replace('    else\n        PrintC "NVO Combat: missing prerequisites. See the console lines above."\n','\n')
    check=check.replace('    if IsPluginInstalled "NVOCombatCore"\n        set bCorePresent to 1\n    endif',
        '    if IsPluginInstalled "NVOCombatCore"\n        set bCorePresent to 1\n    else\n        PrintC "NVO Combat: NVOCombatCore is missing. Native diagnostics are unavailable."\n    endif')
    guarded=[]
    for line in check.splitlines():
        if line.lstrip().startswith('PrintC '):
            indent=line[:len(line)-len(line.lstrip())]
            guarded += [indent+'if bReportMissing == 1', '    '+line, indent+'endif']
        else: guarded.append(line)
    boot=boot[:boot.index('    PrintC "NVO Combat: foundation packet 1 initialized."')]+'\n'.join(guarded)+'\n\nEnd\n'
    scripts={'NVOCombatBootstrapScript':boot}
    for name in ('ALTQscript','ALTStartQscript'):
        old=original(name)
        start=old.index('\t\t\tIf GetNVSEVersion < 6') if name=='ALTQscript' else old.index('\t\tIf GetNVSEVersion < 6')
        compat=old.index('ElseIf ismodloaded "Better Character Creation.esm"',start)
        # Keep the existing compatibility block and all gameplay below it intact.
        prefix=old[:start]; indent='\t\t\t' if name=='ALTQscript' else '\t\t'
        tail='If ismodloaded "Better Character Creation.esm"'+old[compat+len('ElseIf ismodloaded "Better Character Creation.esm"'):]
        new=prefix+indent+tail
        anchor='\t\tif getgamerestarted\n' if name=='ALTQscript' else 'Begin gamemode\n'
        gate_indent='\t\t' if name=='ALTQscript' else '\t'
        gate='\n'.join(gate_indent+line if line else '' for line in GATE.splitlines())+'\n'
        if name=='ALTQscript': new=new.replace(anchor,gate+'\n'+anchor,1)
        else: new=new.replace(anchor,anchor+gate+'\n',1)
        # Dependency notices have one owner: bootstrap. Compatibility notices stay
        # on the original once-per-process branches, now console-only.
        compat_end=new.index('\t\t\tSetPerkFlag WildWasteland' if name=='ALTQscript' else '\tIf bCustomMenu == 0')
        front,rest=new[:compat_end],new[compat_end:]
        front=front.replace('messageboxex ', 'PrintC ')
        new=front+rest
        # Gameplay bodies (including lambdas, variable declarations, registrations)
        # are verbatim apart from normalized CRCRLF line endings.
        old_marker=old.index('\t\t\tSetPerkFlag WildWasteland' if name=='ALTQscript' else '\tIf bCustomMenu == 0')
        assert rest==old[old_marker:]
        scripts[name]=new
    diffs=[]; evidence=[]
    for name,s in scripts.items():
        s=s.rstrip()+'\n'
        scripts[name]=s
        assert all(ord(c)<128 for c in s)
        # These are source checks, not a substitute for the user's GECK compiler.
        for n,line in enumerate(s.splitlines(),1):
            if not line.lstrip().startswith(';'):
                assert line.count('"')%2==0,(name,n,'quotes')
                if '"' in line: assert all(';' not in text for text in line.split('"')[1::2])
        original_source=original(name,'RD.esm' if name=='NVOCombatBootstrapScript' else 'NVO.esm')
        (dest/(name+'.txt')).write_bytes(s.replace('\n','\r\n').encode('ascii'))
        diffs.extend(difflib.unified_diff(original_source.splitlines(True),s.splitlines(True),fromfile='installed/'+name,tofile='prepared/'+name))
        evidence.append(dict(script=name,source_sha256=sha((dest/(name+'.txt')).read_bytes()),
            source_only=True,geck_compiled=False,full_replacement=True))
    (OUT/'SCRIPT-DIFF.txt').write_text(''.join(diffs))
    (OUT/'SOURCE-CHECKS.json').write_text(json.dumps(dict(scripts=evidence,gameplay_bodies_preserved=True,
        quiet_success=True,dependency_notices_owner='NVOCombatBootstrapScript',
        dependency_reporting='At first bootstrap execution per process only; presence state refreshes on each load.',
        compilation='Pending user GECK compile; source checks do not prove compilation.'),indent=2)+'\n')
    return scripts

def make_page(scripts):
    cards=[]
    for i,name in enumerate(('NVOCombatBootstrapScript','ALTQscript','ALTStartQscript'),1):
        cards.append(f'''<section><div class="row"><h2>{i}. {name}</h2><button type="button" data-copy="s{i}">Copy complete script</button></div>
<p>Open this existing Quest script. Replace its entire text, then save/compile.</p>
<details><summary>View complete script</summary><textarea id="s{i}" readonly spellcheck="false">{html.escape(scripts[name])}</textarea></details></section>''')
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NVO · Packet 3I · Startup repair</title><style>
:root{color-scheme:dark}body{margin:0;background:#101713;color:#e4ece6;font:17px/1.55 system-ui,sans-serif}main{max-width:950px;margin:auto;padding:32px 22px 60px}h1{font-size:32px;line-height:1.15}h2{font-size:21px;margin:0}.eyebrow{color:#b5d6ab;font-weight:650}section{background:#18221c;border:1px solid #3b5141;border-radius:12px;padding:23px;margin:20px 0}a{color:#baddaa}button{background:#c6e2b7;color:#142019;border:0;border-radius:7px;padding:12px 16px;font:700 15px system-ui;cursor:pointer}button:hover{background:#e0f4d7}.row{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap}textarea{box-sizing:border-box;width:100%;height:410px;margin-top:12px;background:#0d140f;color:#e4ece6;border:1px solid #59775e;padding:13px;font:13px/1.45 monospace;white-space:pre}code{overflow-wrap:anywhere}li{margin:9px 0}.note{color:#bdd0c3}#status{min-height:1.6em;color:#d9f4c9;position:sticky;bottom:0;background:#101713;padding:10px 0}details{margin-top:14px}summary{cursor:pointer}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:7px;border-bottom:1px solid #3b5141}@media(max-width:600px){main{padding:20px 12px}.row{display:block}button{margin-top:12px}h1{font-size:27px}}
</style></head><body><main><p class="eyebrow">NVO / PACKET 3I / GECK COMPILE PENDING</p>
<h1>Quiet startup. Clean Player baseline.</h1><p>Correct the saved startup scripts and override RD's inherited Player test values. Your health game settings stay intact. Native318 remains installed, with damage replacement disabled.</p>
<section><h2>First: apply the prepared Player record</h2><ol><li>Save and close GECK. Close New Vegas, Vortex and xEdit.</li>
<li>In this packet folder, double-click <strong>APPLY-PLAYER-BASELINE.cmd</strong>. It backs up the current files and replaces only NVO.esm with the prepared Player override.</li>
<li>If it reports newer/different edits, stop and tell me. Do not overwrite manually.</li></ol>
<button type="button" data-copy="folder">Copy packet folder path</button>
<textarea id="folder" hidden>C:\\Users\\regan\\Documents\\ChatGPT\\NVO\\release\\NVO-Combat-Packet-3I-Records</textarea>
<p class="note">Apply this before compiling the scripts below. The staged ESM still has the old compiled startup scripts until you compile and save.</p></section>
<section><h2>Then: compile these three existing scripts</h2><p>Open GECK Extender with <strong>NVO.esm active</strong>. RD.esm stays loaded as a master. Use <strong>Gameplay → Edit Scripts</strong>; all three remain Quest scripts.</p>
<p>Keep the existing <strong>NVOCombatBootstrapScriptQ</strong> quest and its script assignment. Do not create or rename a quest or script.</p></section>
''' + '\n'.join(cards) + '''
<section><h2>Save and stop at this checkpoint</h2><p>After all three scripts compile, save <strong>NVO.esm</strong> from the main GECK window. Reply <strong>“compiled and saved”</strong>, or send the error and script name.</p><p>I will check the saved records before the short startup/reload check. No firing test is needed.</p></section>
<details><summary>Player changes and remaining RD work</summary><p>The staged override copies the base-game Player record: base health100, SPECIAL5, fatigue200, speed100, zero skill offsets and original base inventory. Character creation/backgrounds still apply their choices. Existing saves can retain old values; 100 base health is not a promise of 100 displayed HP.</p><p>RD remains a master for its required references. Its other records and the Brahmin Baron extra-damage handler have a separate ownership plan. This packet does not activate coordinated damage.</p></details>
<p><a href="GECK-INSTRUCTIONS.md">Full instructions and reversal</a> · <a href="OWNERSHIP.md">Ownership plan</a> · <a href="PLAYER-RECORD-AUDIT.json">Record audit</a> · <a href="SCRIPT-DIFF.txt">Script changes</a></p>
<p id="status" role="status" aria-live="polite"></p></main><script>
document.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',async()=>{
 const field=document.getElementById(button.dataset.copy),status=document.getElementById('status');
 try { await navigator.clipboard.writeText(field.value); }
 catch(error) { const temporary=document.createElement('textarea');temporary.value=field.value;temporary.style.position='fixed';temporary.style.left='-10000px';document.body.appendChild(temporary);temporary.select();const ok=document.execCommand('copy');temporary.remove();if(!ok){if(field.closest('details'))field.closest('details').open=true;field.hidden=false;field.focus();field.select();status.textContent='Copy was blocked. Text selected: press Ctrl+C.';return;} }
 status.textContent=button.dataset.copy==='folder'?'Folder path copied. Paste it into File Explorer.':'Complete script copied. Paste over all text in the existing GECK script.';
}));</script></body></html>'''
    (OUT/'START-HERE.html').write_text(page,encoding='utf-8')

def main():
    OUT.mkdir(exist_ok=True); REL.mkdir(exist_ok=True)
    audit=make_player_copy(); scripts=make_sources(); make_page(scripts)
    for name in ('README.md','GECK-INSTRUCTIONS.md','OWNERSHIP.md','START-HERE.html','APPLY-PLAYER-BASELINE.ps1','APPLY-PLAYER-BASELINE.cmd'):
        # Human-readable instructions and helper templates are maintained beside
        # the generated artifacts; packaging happens after they are authored.
        if (OUT/name).exists(): shutil.copy2(OUT/name,REL/name)
    shutil.copytree(OUT/'Scripts',REL/'Scripts',dirs_exist_ok=True)
    shutil.copytree(OUT/'Staged',REL/'Staged',dirs_exist_ok=True)
    for name in ('PLAYER-RECORD-AUDIT.json','SOURCE-CHECKS.json','SCRIPT-DIFF.txt'):
        shutil.copy2(OUT/name,REL/name)
    shutil.copy2(ROOT/'CREDITS.md',REL/'CREDITS.md')
    manifest=dict(packet='3I',type='Record and GECK source preparation; native318 retained',
        baseline_nvo_sha256=EXPECTED_NVO,staged_nvo_sha256=audit['staged_sha256'],
        rd_sha256='9498ee5bee4119ec289b8f88af83e3bbd0ff2e2ec57e45809f3e18dd8b139bc3',
        workspace=str(ROOT),game_root=str(GAME),installed=False,geck_compiled=False,
        files=[dict(path=str(p.relative_to(REL)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
            for p in sorted(REL.rglob('*')) if p.is_file() and p.name!='PACKET.json'])
    (REL/'PACKET.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(str(REL)+'.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(REL.rglob('*')):
            if p.is_file(): z.write(p,REL.name+'/'+str(p.relative_to(REL)))
    print(json.dumps(audit,indent=2))

if __name__=='__main__': main()
