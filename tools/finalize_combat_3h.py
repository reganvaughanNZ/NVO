"""Verify installed318 and publish the reviewable receipt/checkpoint/archive."""
from pathlib import Path
import hashlib,json,re,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1];NATIVE=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3h';RELEASE=ROOT/'release/NVO-Combat-Packet-3H-Compiled'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
result=json.loads((PACKET/'INSTALL-3H-result.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((RELEASE/'manifest.json').read_text())
assert result['status']=='installed' and result['version']==318 and result['replaced']==2 and not result['archived_removed']
assert not result['game_relaunched'] and not result['gameplay_tested']
for f in result['installed']:
    assert hashlib.sha256((GAME/f['path']).read_bytes()).hexdigest()==f['sha256']
    assert hashlib.sha256((RELEASE/f['path']).read_bytes()).hexdigest()==f['sha256']
receipt=f'''# Packet3H / native318 installed

Installed only NVOCombatCore.dll and its matching PDB. {result['protected_files_verified']} protected entries remain byte-identical. No game was running or closed, and no assistant game launch, gameplay or GECK operation occurred.

Backup: {result['backup']}

DLL SHA256: {result['installed'][0]['sha256']}

PDB SHA256: {result['installed'][1]['sha256']}

Reversal: close New Vegas and restore both files from this backup's originals/Data/NVSE/Plugins to the matching game folder. That restores native317. ESM/ESP, profiles, activation and saves require no change.

Expected: native version318 / phase3H, HIT_TX_HOOK_READY, HIT_TX_READY and HIT_TX_BEGIN/STAGE/RETURN/SUMMARY in game-root NVOCombatCore.log. Readiness and call ordering still require the user's live check. Damage replacement remains disabled. Follow START-HERE.html for the ordinary shot, VATS shot and punch after one reload.
'''
(PACKET/'INSTALL-3H.md').write_text(receipt)
for name in ('INSTALL-3H.md','INSTALL-3H-plan.json','INSTALL-3H-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
manifest.update(status='Installed; user318 live diagnostic checkpoint pending',installed_by_assistant=True,installation_receipt='Installation/INSTALL-3H.md')
for p in (NATIVE/'manifest.json',RELEASE/'manifest.json',RELEASE/'Source/NVOCombatCore/manifest.json'):
    p.write_text(json.dumps(manifest,indent=2)+'\n')
# Package-local include paths for the optional offline probe; same observer source.
p=RELEASE/'Source/probe/replay.cpp';s=p.read_text().replace('../../../../native/NVOCombatCore/src/HitTransaction.cpp','../NVOCombatCore/src/HitTransaction.cpp');p.write_text(s)
p=RELEASE/'Source/probe/RUN.cmd';s=p.read_text().replace('..\\..\\..\\..\\native\\NVOCombatCore\\include','..\\NVOCombatCore\\include');p.write_text(s)
shutil.copyfile(ROOT/'tools/finalize_combat_3h.py',RELEASE/'Source/tools/finalize_combat_3h.py')
checkpoint=f'''## Current combat checkpoint: Packet3H / native318 installed; live call-scope check pending

2026-09-15: user approved the next diagnostic packet after completed Ultra317 audit. Prepared and installed native318, build-17670-10517, only DLL/PDB replaced. {result['protected_files_verified']} protected entries unchanged. Backup: {result['backup']}. No game running/closed, assistant gameplay, launch or GECK. Source/packet: source/combat/step3h. Test page: release/NVO-Combat-Packet-3H-Compiled/START-HERE.html. Previous native317 pair retained for reversal.

New HitTransaction.cpp/hpp and fingerprint include wrap six exact existing ITR HitMe call sites before the provider. Complete127-byte ITR thunk hashes normalized for ten relocations, recorded originals0089A760 and matching call targets required. Deferred-init installation only; all-protection acquisition, target recheck, original publication barrier, rollback and per-capture guards. Does not patch ITR DLL/vtables or implement damage. Eight new stub/bridge byte sequences match executable offline probe. Nine physics and CopyObserver bridge sequences unchanged. Eighteen baseline source/config files byte-identical, including model/geometry/tolerance/drag/flight/logging. PE32/matching PDB/two exports, zero warnings. DLL SHA256 {result['installed'][0]['sha256']}; PDB {result['installed'][1]['sha256']}.

New HIT_TX call IDs are monotonic process-wide, separate from projectile lifetimes. Entry snapshots0x64input plus verified identities and creation-ammo/lifetime before ITR. Existing pre-hit/pre-health callbacks attach scope-only; copy input requires exact pointer/identities/process for stronger label. Each native scope acknowledges provider return with committed_loss=unverified and no post-return pointer reads. It does NOT prove terminal health/limb application or causally identify all scoped health changes. TLS16 nested frames, per-thread, never cleared by reload. Overflow passes through without a continuation and taints enclosing scope. First64 detailed calls,8stage rows each,704detail maximum; counts/IDs/returns continue after detail/log exhaustion. NativeObserver adds identity lookup; C++copy/event notifications are before old diagnostic caps. No reverse lock edge. No game data/value, flight, profile, ESM/ESP, activation or save writes.

Offline probe passed six routes/unchanged inputs, actual x86stack/GPR/EFLAGS/DF/x87/SSE/MXCSR preservation,20nested calls with16frame cap,300calls beyond log cap with failed sink, suspended/inactive passthrough and80calls on two threads. Probe includes actual module/bridges with mock provider/forms/logging; it did not load DLL/game. Static bounded row max565bytes. This is not live runtime confirmation or a repeat whole Ultra review. See STATIC-CHECKS.json, REPLAY-RESULT.json, CONTRACT.md, IMPLEMENTATION.md.

USER CHECK: launch NVSE and load test save. Ordinary Hunting Rifle +standard .308, nearby living targets/clear path.1ordinary torsohit;2VATS head-selectedhit at short range; reload same save ONCE;3one punch on livingtarget. Fresh target afterkill,3s betweenhits, atmostone replacement ifmiss,20sfinalwait then normalexit. Existing bat NVOFlightKit3F ifkitneeded; copybutton onpage. No long-distance misses/stress. Read/archive log directly when user finishes; inspect HIT_TX_HOOK_READY/READY/BEGIN/DATA/STAGE/RETURN/SUMMARY. tools/audit_hit_transactions.py adds structured transaction audit to archivedcapture, alongside audit_flight_capture.py. Entry identity linkage and event order may be unavailable on unsupported/deferred routes; preserve evidence, do not claim application from counts. Ask before next packet after review.

ULTRA317 audit complete with gateHOLD (review/ULTRA-317-REVIEW.md and FINDINGS.json). This packet investigates finding317-01; it is not closed without live/source boundary evidence and true application contract. Actor impact-speed geometry, units/mass, region/VATS policy, fallbacks/admission and donor ownership remain open. RD actual noisy bootstrap/oldJIPchecks, Playerbase550/SPECIAL9/ReganGear and BrahminBaron separateDamageAV/Kill are a separate upcoming foundation repair. Preserve NVO's five user healthGMSTs; do not blindly remove RDmaster. Current native318damage OFF. Step3flight ->4armour/damage afterfindingclosure ->5wounds/medicine ->6otherweapons ->7AI/morale ->8backgroundbalance. Do not redo fullUltraaudit; review only futurefixes/newdamageaffectedcode.
'''
(PACKET/'CHECKPOINT-INSTALLED.md').write_text(checkpoint)
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    old=p.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first,sep,rest=old.partition(b'\n');p.write_bytes(first+sep+b'\n'+checkpoint.encode()+b'\n'+rest)
for href in re.findall(r'href="([^"]+)"',(RELEASE/'START-HERE.html').read_text()):assert (RELEASE/href).is_file(),href
for folder in ('src','include','config'):
    for p in (NATIVE/folder).glob('*'):
        if p.is_file():assert p.read_bytes()==(RELEASE/'Source/NVOCombatCore'/folder/p.name).read_bytes()
assert (RELEASE/'Source/NVOCombatCore/src/HitTransaction.cpp').is_file()
archive=RELEASE.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(RELEASE).as_posix())
info=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
(PACKET/'RELEASE.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(dict(version=318,protected=result['protected_files_verified'],backup=result['backup'],release=info,test_page=str(RELEASE/'START-HERE.html')),indent=2))
