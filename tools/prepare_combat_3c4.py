"""Prepare controller-diagnostic packet documentation; no game writes."""
from pathlib import Path
import hashlib, json

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3c4'

def main():
    style='body{max-width:850px;margin:40px auto;padding:0 24px;background:#121918;color:#e9f1e8;font:18px/1.6 system-ui}h1{line-height:1.2}code{background:#283530;padding:3px 7px}li{margin:12px 0}button{padding:9px 15px;font:inherit;cursor:pointer}aside{padding:18px;background:#20352c}a{color:#aad8a7}'
    copy_js="""async function copy(id,b){const t=document.getElementById(id).textContent;try{await navigator.clipboard.writeText(t);b.textContent='Copied'}catch(err){const a=document.createElement('textarea');a.value=t;document.body.append(a);a.select();b.textContent=document.execCommand('copy')?'Copied':'Select and copy';a.remove()}}"""
    start=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>NVO Combat 3C4</title><style>{style}</style>
<h1>NVO Combat · Packet 3C4</h1><p>Version <b>309</b>. Trace the controller's movement request before and after processing.</p>
<aside>This is a diagnostic packet. The previous vertical mismatch may recur. The log will identify the actual movement implementation and whether its input changes. Gravity acceptance remains pending.</aside>
<h2>Your check: two distant shots</h2><ol><li>Keep <b>NVO.esm</b> and <b>NVOFlightPilot.esp</b> active. Launch, load your prepared save, and wait three seconds.</li>
<li>If needed: <code id="kit">bat NVOFlightPilot</code> <button onclick="copy('kit',this)">Copy command</button></li>
<li>Outside VATS, fire <b>one NVO Flight - Hunting Rifle shot</b> and <b>one NVO Flight - 9mm Pistol shot</b> using their private ammunition at the same distant solid wall or water tank. Pause between shots.</li>
<li>Exit normally and report finished. I will read and archive <b>NVOCombatCore.log</b> directly from your game folder.</li></ol>
<p>God mode is fine. No extra reload, stress test, video, GECK change or manual transfer is required after the installation receipt confirms installation.</p>
<p>Optional version check: <code id="version">GetPluginVersion "NVOCombatCore"</code> <button onclick="copy('version',this)">Copy command</button> should return <b>309</b>.</p>
<h2>Reversal</h2><p>Close the game and restore the matching previous DLL/PDB from the backup in <a href="Installation/INSTALL-3C4.md">the installation receipt</a>. Existing <code>NVOFlightPhysics.ini</code> can disable the movement pilot with <code>enabled=0</code> for the next capture.</p>
<p><a href="README.md">Implementation details</a> · <a href="BUILD-RESULT.md">Build evidence</a>. No new console messages or dependencies are added.</p><script>{copy_js}</script></html>'''
    (PROJECT/'START-HERE.html').write_text(start,encoding='utf-8')
    (PROJECT/'README.md').write_bytes((PACKET/'IMPLEMENTATION.md').read_bytes())
    p=PROJECT/'SDK-BOUNDARY.md'; old=p.read_bytes()
    heading=b'# Current packet: 3C4 / 309 controller request diagnostics\n\n'
    if not old.startswith(heading):
        p.write_bytes(heading+b'See README.md. Three additional read-only controller observations retain the existing bounded movement pilot. No controller/object/damage writes. Gravity remains unaccepted. Historical boundaries below.\n\n'+old)
    capture=ROOT/'source/combat/step3c3/runtime-20260915-141533/movement-0092F260.bin'
    raw=capture.read_bytes()
    spans=[(0x92FFEA,'8B82C8000000FFD0'),(0x92FFD4,'E8870B3400'),(0x92FFFB,'E8B0040000')]
    for address,hex_bytes in spans:
        expected=bytes.fromhex(hex_bytes)
        assert raw[address-0x92F260:address-0x92F260+len(expected)]==expected
    evidence=dict(packet='3C4',reference_capture=str(capture.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),
        new_observer_spans=[dict(address=f'{a:08X}',original_bytes=h) for a,h in spans],
        new_gameplay_writes=False,physics_accepted=False,request='generic EBP-208',argument_frame='generic saved EBX',
        target_capture=dict(maximum_unique_targets_per_process=2,bytes_per_target=2048,game_executable_image_only=True),
        note='Static original-byte validation only; no game execution or captured code distribution.')
    (PROJECT/'reference/CONTROLLER-REQUEST-DIAGNOSTICS.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print('Prepared 3C4 documents and verified three new spans against the archived runtime bytes.')

if __name__=='__main__': main()
