"""Prepare packet documentation and a quiet bootstrap candidate. No game writes."""
from pathlib import Path
import hashlib, html, json

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3c3'

source=(ROOT/'source/combat/step1/NVOCombatBootstrapScript.txt').read_text(encoding='utf-8-sig')
source=source.replace('    PrintC "NVO Combat: foundation packet 1 initialized."\n','')
source=source.replace('        PrintC "NVO Combat: native plugin detected. Damage hooks remain disabled."\n','')
source=source.replace('    else\n        PrintC "NVO Combat: native plugin not installed. Expected for packet 1."\n','')
source=source.replace('        PrintC "NVO Combat: prerequisite plugins detected. Version audit is in the packet."\n','')
source=source.replace('    PrintC "NVO Combat: packet 1 does not change combat."\n','')
(PACKET/'NVOCombatBootstrapScript-quiet.txt').write_text(source,encoding='utf-8')
copy_js='''async function copy(id,b){const e=document.getElementById(id),t=e.value||e.textContent;try{await navigator.clipboard.writeText(t);b.textContent='Copied'}catch(err){const a=document.createElement('textarea');a.value=t;document.body.append(a);a.select();b.textContent=document.execCommand('copy')?'Copied':'Select and copy';a.remove()}}'''
style='body{max-width:850px;margin:40px auto;padding:0 24px;background:#121918;color:#e9f1e8;font:18px/1.6 system-ui}h1{line-height:1.2}code{background:#283530;padding:3px 7px}li{margin:12px 0}button{padding:9px 15px;font:inherit;cursor:pointer}aside{padding:18px;background:#20352c}a{color:#aad8a7}textarea{width:100%;height:480px;font:14px/1.5 Consolas,monospace}'
quiet=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>NVO quiet startup script</title><style>{style}</style>
<h1>Quiet successful reloads</h1><p>This complete replacement removes the old Packet 1 success messages. Dependency checks and missing-dependency warnings remain. It does not change native physics.</p>
<aside>Prepared for your existing working <b>NVOCombatBootstrapScript</b>. The game Data/NVO.esm inspected during this review does not contain that record. Use this only if the existing script is present in your working GECK file. If it is absent, report one exact repeating NVO console line so we can locate its source. Do not create another bootstrap quest.</aside>
<ol><li>Back up your working ESM. Open the existing script; retain its Quest script type and quest attachment.</li><li>Replace its entire source with the text below, compile, then save your working ESM.</li><li>When that updated file is installed, successful checks should print no Packet 1 success block. You can perform this separately from the native two-shot diagnostic.</li></ol>
<button onclick="copy('source',this)">Copy complete script</button><textarea id="source" readonly>{html.escape(source)}</textarea><p>Reversal: restore your working ESM backup, or recompile the previous complete Packet 1 source. No game file has been modified automatically by this page.</p><script>{copy_js}</script></html>'''
(PACKET/'COPY-QUIET-STARTUP.html').write_text(quiet,encoding='utf-8')

start=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>NVO Combat 3C3</title><style>{style}</style>
<h1>NVO Combat · Packet 3C3</h1><p>Version <b>308</b>. Locate the vertical movement loss found in the last test.</p>
<aside>This adds movement-boundary diagnostics. The gravity mismatch may still appear; that is useful evidence. Gravity/drag acceptance remains pending.</aside>
<h2>Your check: two distant shots</h2><ol><li>Keep <b>NVO.esm</b> and <b>NVOFlightPilot.esp</b> active. Launch, load your prepared save, and wait three seconds.</li><li>If needed, enter <code id="kit">bat NVOFlightPilot</code> <button onclick="copy('kit',this)">Copy command</button></li><li>Outside VATS, fire <b>one NVO Flight - Hunting Rifle shot</b> and <b>one NVO Flight - 9mm Pistol shot</b> using their private ammunition at the same distant wall/water tank. Pause between shots.</li><li>Exit and tell me you finished. I will read and archive <b>NVOCombatCore.log</b> directly.</li></ol>
<p>God mode is fine. No extra reload, VATS, stress test, video or GECK change is required for this check.</p>
<p>Optional version check: <code id="version">GetPluginVersion "NVOCombatCore"</code> <button onclick="copy('version',this)">Copy command</button> should return <b>308</b>.</p>
<h2>Console note</h2><p><a href="COPY-QUIET-STARTUP.html">Complete quiet-startup script with copy button</a> is prepared for your existing working bootstrap record. It has not been compiled into your ESM. Its installed source needs confirming; native two-shot testing can proceed separately.</p>
<h2>Reversal</h2><p>With the game closed, restore the previous matching DLL/PDB from the backup in <code>source/combat/step3c3/INSTALL-3C3.md</code>. Existing <code>NVOFlightPhysics.ini</code> can disable the movement pilot with <code>enabled=0</code> for the next capture.</p><p><a href="README.md">Details</a> · <a href="BUILD-RESULT.md">Build evidence</a></p><script>{copy_js}</script></html>'''
(PROJECT/'START-HERE.html').write_text(start,encoding='utf-8')
implementation=(PACKET/'IMPLEMENTATION.md').read_text(encoding='utf-8')
(PROJECT/'README.md').write_text(implementation,encoding='utf-8')
p=PROJECT/'SDK-BOUNDARY.md'
old=p.read_bytes()
heading=b'# Current packet: 3C3 / 308 movement-boundary diagnostics\n\n'
if not old.startswith(heading):
    p.write_bytes(heading+b'See README.md and source/combat/step3c3/IMPLEMENTATION.md. Two added CALL observers only read pending movement arguments and candidate positions. Existing 3C2 movement write and mismatch limits remain; gravity is not accepted. Historical boundaries below.\n\n'+old)

captures=[]
for name in ('runtime-20260915-141533','runtime-20260915-141903'):
    f=PACKET/name/'manifest.json'
    captures.append(dict(path=str(f.relative_to(ROOT)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
evidence=dict(packet='3C3',capture_manifests=captures,
    new_observer_calls=[dict(address='00930475',original='00575830',bytes='E8 B6 53 C4 FF'),dict(address='0092F5DC',original='00440460',bytes='E8 7F 0E B1 FF')],
    generic_body_guard=dict(address='0092F260',size='123C',normalized_fnv64='DEFD795E42FB0C4E'),
    new_boundary_gameplay_writes=False,physics_correction_accepted=False,
    hypothesis='Discarded input local Z fits all four 307 failures; exact executing route remains unproven.',
    note='No captured executable bytes are distributed. Only address/stack/hash metadata is copied.')
(PROJECT/'reference/FLIGHT-BOUNDARY-DIAGNOSTICS.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
template=Path(r'C:\Users\regan\Desktop\NVO Mod References (Open Source)\NVSE-Plugins-main')
inventory=[dict(file=n,sha256=hashlib.sha256((template/n).read_bytes()).hexdigest()) for n in ('README.md','LICENSE')]
(ROOT/'reference/NVSE-PLUGINS-TEMPLATE-REVIEW.json').write_text(json.dumps(dict(source=str(template),reviewed=inventory,code_copied=False,installed=False),indent=2)+'\n',encoding='utf-8')
print('Prepared documentation, quiet bootstrap candidate and reference metadata; no game writes.')
