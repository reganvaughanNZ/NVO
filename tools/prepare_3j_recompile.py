"""Complete copyable sources which retain original externally used variable slots.

Reserved declarations fill historical gaps when GECK compiles a fresh copy. If
an existing script is edited, its existing variable indices must still be checked
after compilation; source order alone is not accepted as proof.
"""
from pathlib import Path
import json, re, html
from verify_combat_3i import parse, variables

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'source/combat/step3j'
REL=ROOT/'release/NVO-Combat-Packet-3J-RD-Free'
OUT=PACK/'recompile'
OUT.mkdir(exist_ok=True)
records=parse((REL/'Data/NVO.esm').read_bytes())
decl=re.compile(r'^(\s*)(short|long|int|float|ref|string_var|array_var)\s+(\w+)\s*(?:=.*)?$',re.I)
cards=[];audit=[]
for name in ('ALTQscript','ALTStartQscript'):
    base=next(r for r in records if r['edid']==name)
    slots=variables(base['parts']);oldsource=(REL/'Scripts'/f'{name}.txt').read_text(encoding='ascii')
    output=[];seen={};index=0;reserved=[]
    for line in oldsource.splitlines():
        match=decl.fullmatch(line)
        if match:
            indent,kind,var=match.groups();target=slots[var.lower()][0]
            assert target>index,(name,var,target,index)
            while index+1<target:
                index+=1;reserved.append(index)
                output.append(f'{indent}int nvoReservedSlot{index}')
            index+=1;assert index==target
            seen[var.lower()]=(index,1 if kind.lower() in ('short','long','int','string_var','array_var') else 0)
        # xNVSE also registers newly typed inline-lambda parameters in the
        # parent table. The existing iSetupChoice is introduced this way.
        for kind,var in re.findall(r'\{\s*(int|float|ref|string_var|array_var)\s+(\w+)\s*\}',line,re.I):
            if var.lower() not in seen:
                index+=1
                assert slots[var.lower()][0]==index,(name,var,index)
                seen[var.lower()]=(index,1 if kind.lower() in ('int','string_var','array_var') else 0)
        output.append(line)
    assert seen==slots,(name,seen,slots)
    assert all(f'nvoReservedSlot{i}'.lower() not in oldsource.lower() for i in reserved)
    result='\n'.join(output)+'\n'
    # Apart from unused declarations, the full supplied source is unchanged.
    stripped='\n'.join(line for line in output if not re.match(r'\s*int nvoReservedSlot\d+\s*$',line))+'\n'
    assert stripped==oldsource.replace('\r\n','\n')
    (OUT/f'{name}.txt').write_bytes(result.replace('\n','\r\n').encode('ascii'))
    audit.append(dict(script=name,original_variable_slots=slots,reserved_slots=reserved,maximum_original_slot=index,
        executable_source_unchanged=True,geck_compile_pending=True))
    cards.append(f'''<section><h2>{html.escape(name)}</h2><button onclick="copyScript('{name}',this)">Copy complete replacement</button>
    <a href="{name}.txt">Open text</a><details><summary>Show source</summary><textarea id="{name}" readonly>{html.escape(result)}</textarea></details></section>''')
(OUT/'SOURCE-AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NVO — finish the two script compiles</title>
<style>:root{color-scheme:dark}body{max-width:850px;margin:40px auto;padding:0 24px;background:#10191b;color:#e7eeeb;font:17px/1.6 system-ui}h1{font-size:30px;line-height:1.25}h2{font-size:22px}section,.notice{padding:22px;background:#18282b;border:1px solid #36504c;border-radius:10px;margin:24px 0}li{margin:12px 0}a{color:#a9e9d0}button{padding:14px 20px;font:600 16px system-ui;background:#a9e9d0;color:#10271d;border:0;border-radius:6px;margin:0 12px 12px 0;cursor:pointer}textarea{box-sizing:border-box;width:100%;height:300px;background:#0b1215;color:#e7eeeb;font:13px/1.4 monospace;padding:12px}details{margin-top:15px}</style>
<h1>Finish the two Alternative Start scripts</h1>
<p>RD removal is intact. Your saved file has the requested code in three duplicate script records, while the linked originals still hold the old code. The bootstrap copy is usable; leave it alone.</p>
<div class="notice">These two replacements preserve the variable positions used by other records, including character setup and background perks. The extra <code>nvoReservedSlot</code> declarations are intentional. Do not remove them.</div>
<ol><li>Load <b>NVO.esm as the active file</b> in GECK Extender.</li>
<li>Open <b>Gameplay → Edit Scripts</b>, then use the script editor's <b>Script → Open</b> list to open <b>ALTQscript</b> exactly. Choose the original name without <b>DUPLICATE</b>. Do not choose <b>New</b>.</li>
<li>In its code area press <b>Ctrl+A</b>, use the matching Copy button below, paste, then compile/save the script. Keep <b>Script Type: Quest</b>.</li>
<li>Repeat for the original <b>ALTStartQscript</b> using its own button.</li>
<li>Save NVO.esm in the main GECK window, close GECK and reply <b>saved</b>. I will verify the variable positions and reconnect the compiled code to the original records if GECK has made further copies.</li></ol>
<p>No new quest, manual linking, Recompile All or gameplay test is needed. Leave NVOCombatBootstrapScript alone; I already have its usable compiled copy.</p>
'''+''.join(cards)+'''
<script>async function copyScript(id,b){let t=document.getElementById(id);try{await navigator.clipboard.writeText(t.value);b.textContent='Copied';}catch(e){t.closest('details').open=true;t.focus();t.select();b.textContent=document.execCommand('copy')?'Copied':'Press Ctrl+C';}}</script></html>'''
(OUT/'START-HERE.html').write_text(page,encoding='utf-8')
print(json.dumps(dict(path=str(OUT/'START-HERE.html'),scripts=audit),indent=2))
