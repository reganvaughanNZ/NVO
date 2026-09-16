"""Verify installed316 pair, publish receipt/checkpoint and release archive."""
from pathlib import Path
import hashlib,json,re,shutil,zipfile

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3g1'
RELEASE=ROOT/'release/NVO-Combat-Packet-3G1-Compiled'
GAME=Path('C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
result=json.loads((PACKET/'INSTALL-3G1-result.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((RELEASE/'manifest.json').read_text())
assert result['status']=='installed' and result['version']==316 and result['packet']=='3G1'
assert result['replaced']==2 and len(result['installed'])==2 and result['archived_removed']==0
assert not result['game_relaunched'] and not result['gameplay_tested']
assert {r['path']:r['sha256'] for r in result['installed']}=={r['path']:r['sha256'] for r in manifest['installed_files']}
for r in result['installed']:assert hashlib.sha256((GAME/r['path']).read_bytes()).hexdigest()==r['sha256']
hashes='\n'.join(f'- {r["path"]}: {r["sha256"]}' for r in result['installed'])
receipt=f'''# Packet3G1 / native316 installed

Replaced only NVOCombatCore.dll and its matching PDB. Verified {result['protected_files_verified']} protected entries unchanged. Closed processes: {len(result['closed_processes'])}. No assistant game launch, gameplay or GECK operation.

Backup: {result['backup']}

{hashes}

Reversal: close New Vegas and restore both files from this backup's originals/Data/NVSE/Plugins into the matching game folder. This restores native315. Keep current NVO.esm, NVOFlightPilot.esp, their masters, INIs, kit, activation and saves.

Expected header: NVOCombatCore0.3.16 / phase=3G1; plugin version316. Game-root NVOCombatCore.log contains IMPACT_BOUNDARY, IMPACT_MODEL, IMPACT_CALLBACK and IMPACT_COVERAGE_SUMMARY. No new console message or GECK work. Follow START-HERE.html for three shots; user live confirmation remains pending. Flight, terrain and damage rules are unchanged.
'''
(PACKET/'INSTALL-3G1.md').write_text(receipt)
for name in ('INSTALL-3G1.md','INSTALL-3G1-plan.json','INSTALL-3G1-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
manifest.update(status='Installed; user316 diagnostic confirmation pending',installed_by_assistant=True,installation_receipt='Installation/INSTALL-3G1.md')
for p in (RELEASE/'manifest.json',PROJECT/'manifest.json',RELEASE/'Source/NVOCombatCore/manifest.json'):
    p.write_text(json.dumps(manifest,indent=2)+'\n')
for name in ('finalize_combat_3g1.py','audit_flight_capture.py'):
    shutil.copyfile(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
checkpoint=f'''## Current combat checkpoint:3G1 / native316 installed; awaiting user test

2026-09-15: approved3G1 prepared, compiled and installed only DLL/PDB (build-30541-23708). Zero compiler warnings/errors, matching PE32/PDB, two expected NVSE exports and all nine compiled physics bridges unchanged. {result['protected_files_verified']} protected entries unchanged. Backup: {result['backup']}. No game running at installation; no assistant gameplay/GECK. See source/combat/step3g1/INSTALL-3G1.md and release/NVO-Combat-Packet-3G1-Compiled/START-HERE.html.

FlightImpactModel.inl separates earlier full endpoint/accounting checks from contact-chord validation. Existing tolerances and24-iteration partial-time model unchanged. All six eligible captured3G impacts yield model estimates; baseline shots1/2 stay engine_baseline_contact. Pure model and actual cache replay compiled with captured engine-read stubs: seven invalid-input guards, later lifetimes through32, omission beyond32, duplicate/missing/unpaired callbacks and reset pass. See replay/REPLAY-RESULT.json (source hashes and capture018ec6d9b0b6). This is offline evidence, not live316 acceptance.

ImpactEnroll adds one diagnostic call in the accepted Track path. Removing it reproduces native315 FlightPhysics.cpp exactly;17 other baseline files byte-identical. Independent32 accepted-lifetime cache survives retirement until load reset; at most224 extra detail rows/load plus2 summaries, with explicit omitted and baseline counts. Heavy frame detail remains8lifetimes/64steps. New IMPACT_BOUNDARY and IMPACT_COVERAGE_SUMMARY. Existing guarded optional reads/callback correlation, no game/Track writes, no hook/range/flight/damage change or new console output. Version316/header0.3.16/phase3G1. All formats <=587 bytes.

USER CHECK: ordinary Hunting Rifle, standard .308;1 very close solid object outside VATS;2 living target outside VATS at roughly distance of previous final successful headshot (farther than previous baseline shot2);3 living target at similar distance using VATS. Another target if dead. Clear line of sight; wait3s between impacts, at most1 replacement per missed check,20s after final then normal exit/report. No reload/stress/long miss or extra shots to test limit. Existing bat NVOFlightKit3F optional. Read/archive log before relaunch; audit_flight_capture.py now includes boundary/coverage rows. Review candidate geometry, callback pairing and baseline handling; ASK before next packet.

Preserve3F3 terrain/range acceptance and3G review (actor hits2/5/10, final critical head user-reported VATS kill; last2 outside old detail cap). First unchanged segment, physical unit calibration, mass/energy and pre-damage integration remain unresolved before armour authority. ShowOff impact callbacks follow damage; no exact contact timestamp measured. Damage and speed authority remain0. RD master removal and HP selection persistence are separate. Do not re-offer declined fixture or repeat terrain repro without new evidence.
'''
(PACKET/'CHECKPOINT-INSTALLED.md').write_text(checkpoint)
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    old=p.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first,sep,rest=old.partition(b'\n');p.write_bytes(first+sep+b'\n'+checkpoint.encode()+b'\n'+rest)
for href in re.findall(r'href="([^"]+)"',(RELEASE/'START-HERE.html').read_text()):assert (RELEASE/href).is_file(),href
for p in (PROJECT/'src').glob('*'):
    if p.is_file():assert p.read_bytes()==(RELEASE/'Source/NVOCombatCore/src'/p.name).read_bytes()
archive=RELEASE.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(RELEASE).as_posix())
info=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
(PACKET/'RELEASE.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(dict(version=316,protected=result['protected_files_verified'],backup=result['backup'],release=info,test_page=str(RELEASE/'START-HERE.html')),indent=2))
