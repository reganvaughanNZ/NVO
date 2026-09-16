"""Prepare the bounded local-Z correction packet; workspace writes only."""
from pathlib import Path
import hashlib, json

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3c5'

def main():
    PACKET.mkdir(parents=True,exist_ok=True)
    p=PROJECT/'src/FlightPhysics.cpp'; s=p.read_text()
    start=s.find('// Bounded evidence of the actual dispatched implementation,')
    if start>=0:
        end=s.index('// phase 0:',start)
        s=s[:start]+s[end:]
        p.write_text(s,encoding='utf-8')
    p=PROJECT/'src/Plugin.cpp'; s=p.read_text()
    s=s.replace('kPluginVersion = 309; // 0.3.9, packet 3C4 controller request diagnostics',
                'kPluginVersion = 310; // 0.3.10, packet 3C5 guarded controller local-Z correction')
    s=s.replace('NVOCombatCore 0.3.9 | phase=3C4','NVOCombatCore 0.3.10 | phase=3C5')
    p.write_text(s,encoding='utf-8')
    p=PROJECT/'CMakeLists.txt';p.write_text(p.read_text().replace('VERSION 0.3.9','VERSION 0.3.10'),encoding='utf-8')
    capture=ROOT/'source/combat/step3c4/captures/2026-09-15-3C4-7e3ad3449a2c/controller-00C73170.bin'
    raw=capture.read_bytes()
    assert len(raw)==2048 and hashlib.sha256(raw).hexdigest()=='20a927ae6742fc61e6cdf8f0a52c945051a7a33cf743c1aa7c7a151627e0beac'
    assert raw[0xC73517-0xC73170:0xC7351D-0xC73170]==bytes.fromhex('D9EED95C2458')
    evidence=dict(packet='3C5',version=310,source_capture=str(capture.relative_to(ROOT)),
        sha256=hashlib.sha256(raw).hexdigest(),prefix_bytes=2048,prefix_fnv64='0193951146A4412C',
        hook_site='00C73517',original_bytes='D9EED95C2458',patch='CALL bridge + NOP',
        continuation='00C7351D',caller_return='0092FFEF (owned virtual-dispatch CALL)',
        frame='C73170 EBP -> generic movement EBP; [EBP+8] == paired request',
        stack='pre-patch ESP == align_down(C73170 EBP,16) - B0; local XYZ at ESP+50',
        fallback='FLDZ; FSTP [bridge entry ESP+5C]; RET through NOP',
        correction='Skip this reset only for a verified, already-copied private applied vector',
        no_new_engine_calls=True,damage_replacement=False,runtime_accepted=False,
        note='Prefix only, not whole function. Engine bytes are not shipped. Branch and actual flight require user validation.')
    (PROJECT/'reference/CONTROLLER-LOCAL-Z-CORRECTION.json').write_text(json.dumps(evidence,indent=2)+'\n')
    implementation='''# Packet 3C5 / 310 - guarded controller local-Z correction

Purpose: preserve the pilot projectile's calculated vertical movement at the controller operation that would otherwise zero it. This is a correction candidate; user flight verification remains required.

## Evidence and native change

The 309 log identifies virtual C8 of ProjectileListener vtable 01090594 as C73170. Both edited requests contain the intended local Z but actual displacement fits omission of that component. The hash-verified 2048-byte prefix shows conditional FLDZ/FSTP at C73517, after request XYZ is copied into a local vector. The precise reset branch was not directly observed in 309.

310 replaces those six bytes with CALL LocalZBridge + NOP. Arriving at that bridge directly observes the reset branch. The helper pairs the active private projectile, thread, controller and request with the existing enclosing movement observation. It checks the incoming C73170 frame, parent frame, owned virtual-call return, aligned local stack, saved vector pointer, exact vtable/target, timestep, unchanged rotation, collision-free identity and byte-identical submitted/request/working vectors. Flag bit 11 must be clear. No guessed meaning is assigned to engine modes or flags.

For an unchanged baseline, or any untracked/unsupported/rejected call, replay the original FLDZ/FSTP. The bridge's CALL adds four stack bytes, so fallback uses [ESP+5C], exactly the original [ESP+58]. For a verified applied pilot vector only, preserve the already-copied local vector by skipping this reset. No C++ write to controller, request, position, collision or damage fields is added. Both bridge outcomes restore GP registers, flags, x87/SSE/MXCSR and stack balance. The engine continues at C7351D through its original scaling, rotation and collision path.

The initial unchanged segment must both match actual displacement and visit the checked reset boundary before future flight edits become eligible. A guard failure stops subsequent edits for that lifetime; it cannot undo an already-submitted segment. Conditional paths that naturally skip the reset after an accepted baseline still undergo unchanged actual-displacement verification.

The existing caller-owned 12-byte movement input write, RK4 gravity/drag, two exact private combinations, tolerance, impact/destruction attribution and reload cleanup remain. Unknown equipment receives original reset behavior. Damage authority remains disabled. No armour, injury, VATS policy or broader projectile features are added.

Eight hook spans occupy four distinct pages. Existing transactional protection/flush/rollback and exact owned-byte normalization now include the six-byte reset span. The full 2048-byte captured controller prefix is fingerprinted before installation and each capture, alongside previous guards. This is not a full-function fingerprint. Raw controller-byte logging is retired because its identification is complete; evidence remains archived internally.

## User check

Keep NVO.esm and NVOFlightPilot.esp active. Load the prepared save and wait three seconds. Outside VATS, fire one private NVO Flight Hunting Rifle shot and one private NVO Flight 9mm Pistol shot, with their private ammunition, at the same distant solid wall or water tank. Pause between shots, exit normally, and report finished. God mode is fine. No extra reload, stress test, video or GECK edit is required.

Expected evidence: PHYSICS_LOCAL_Z baseline preserve=0/original_reset=1, applied preserve=1/original_reset=0 when the reset branch is reached; PHYSICS_ACTUAL matched=1 for baseline and multiple applied free-flight segments of both weapons; nonzero applied_verified, zero mismatches/unpaired/guard failures. Impact must still terminate flight through original collision handling. Merely arming, reaching the branch or skipping the reset is not physics acceptance.

The world scale and atmosphere remain fixed assumptions. This short check does not establish stress performance, reload/VATS acceptance of this new branch, broad compatibility or injury behavior. No assistant gameplay, DLL loading or GECK execution is performed.

## Installation and reversal

Install only the matching NVOCombatCore.dll/PDB pair after the allowlisted installer verifies hashes and creates its backup. No new dependencies or configuration files. See INSTALL-3C5.md for the actual receipt and backup. Close the game and restore both 309 files from that backup to reverse. Existing NVOFlightPhysics.ini enabled=0 disables the pilot for the next capture.

One packet at a time: review the user's next log before further work. The separate BALLISTX-main simulation library was not incorporated. Existing donor credits/notices remain.
'''
    (PACKET/'IMPLEMENTATION.md').write_text(implementation,encoding='utf-8')
    (PROJECT/'README.md').write_text(implementation,encoding='utf-8')
    p=PROJECT/'SDK-BOUNDARY.md'; data=p.read_bytes(); head=b'# Current packet: 3C5 / 310 guarded local-Z correction\n\n'
    if not data.startswith(head):
        p.write_bytes(head+b'See README.md. One guarded conditional-reset hook extends the private movement pilot. User physics acceptance pending. Historical boundaries below.\n\n'+data)
    style='body{max-width:850px;margin:40px auto;padding:0 24px;background:#121918;color:#e9f1e8;font:18px/1.6 system-ui}h1{line-height:1.2}code{background:#283530;padding:3px 7px}li{margin:12px 0}button{padding:9px 15px;font:inherit;cursor:pointer}aside{padding:18px;background:#20352c}a{color:#aad8a7}'
    copy_js="""async function copy(id,b){const t=document.getElementById(id).textContent;try{await navigator.clipboard.writeText(t);b.textContent='Copied'}catch(err){const a=document.createElement('textarea');a.value=t;document.body.append(a);a.select();b.textContent=document.execCommand('copy')?'Copied':'Select and copy';a.remove()}}"""
    html=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>NVO Combat 3C5</title><style>{style}</style>
<h1>NVO Combat - Packet 3C5</h1><p>Version <b>310</b>. Preserve calculated bullet drop through the movement controller.</p>
<aside>This correction needs your flight check. The log compares intended movement with actual movement; reaching the new hook alone does not count as success.</aside>
<h2>Your check: two distant shots</h2><ol><li>Keep <b>NVO.esm</b> and <b>NVOFlightPilot.esp</b> active. Launch, load your prepared save, and wait three seconds.</li>
<li>If needed: <code id="kit">bat NVOFlightPilot</code> <button onclick="copy('kit',this)">Copy command</button></li>
<li>Outside VATS, fire <b>one NVO Flight - Hunting Rifle shot</b> and <b>one NVO Flight - 9mm Pistol shot</b> using their private ammunition at the same distant solid wall or water tank. Pause between shots.</li>
<li>Exit normally and report finished. I will read and archive <b>NVOCombatCore.log</b> directly from your game folder.</li></ol>
<p>God mode is fine. No extra reload, stress test, video, GECK change or manual transfer is required after the <a href="Installation/INSTALL-3C5.md">installation receipt</a> confirms installation.</p>
<p>Optional version check: <code id="version">GetPluginVersion "NVOCombatCore"</code> <button onclick="copy('version',this)">Copy command</button> should return <b>310</b>.</p>
<h2>Reversal</h2><p>Close the game and restore both version 309 files from the backup in the installation receipt. Existing <code>NVOFlightPhysics.ini</code> can disable the pilot with <code>enabled=0</code> for the next capture.</p>
<p><a href="README.md">Implementation details</a> - <a href="BUILD-RESULT.md">Build evidence</a>. No new console notices or dependencies.</p><script>{copy_js}</script></html>'''
    (PROJECT/'START-HERE.html').write_text(html,encoding='utf-8')
    print('Prepared 3C5 docs and source identity; original reset bytes match the archived controller prefix.')

if __name__=='__main__': main()
