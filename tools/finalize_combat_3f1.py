"""Finalize the installed diagnostic-only packet and pending user checkpoint."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3f1'
RELEASE=ROOT/'release/NVO-Combat-Packet-3F1-Compiled'
GAME=Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
result=json.loads((PACKET/'INSTALL-3F1-result.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((RELEASE/'manifest.json').read_text())
assert result['status']=='installed' and result['packet']=='3F1' and result['version']==312
assert result['replaced']==2 and len(result['installed'])==2
assert {r['path']:r['sha256'] for r in result['installed']}=={r['path']:r['sha256'] for r in manifest['installed_files']}
for r in result['installed']:assert hashlib.sha256((GAME/r['path']).read_bytes()).hexdigest()==r['sha256']
assert not result['game_relaunched'] and not result['gameplay_tested']
note='New Vegas was already closed.' if not result['closed_processes'] else 'The installer closed the verified New Vegas process under existing permission.'
hashes='\n'.join(f'- `{r["path"]}` — `{r["sha256"]}`' for r in result['installed'])
receipt=f'''# Packet3F1 / build312 installed

Replaced only the native DLL and matching PDB. {result['protected_files_verified']} protected entries verified unchanged, including the3F ESP/INIs/kit, NVO.esm/RD.esm, other extenders, old kits and both activation files. {note} No assistant game launch, gameplay or GECK work.

Backup: `{result['backup']}`

{hashes}

To reverse: close New Vegas and restore **both** Data/NVSE/Plugins/NVOCombatCore.dll and NVOCombatCore.pdb from this backup's originals directory to the matching paths. Keep the3F ESP, INIs and existing NVOFlightKit3F.txt. This returns to311's diagnostic coverage, leaving3F profiles and the earlier cleanup intact.

The new header is0.3.12 /phase3F1 and GetPluginVersion should return312. Eleven profiles remain active. The compiled source preserves all flight/guard rules and eight assembly bridges. New bounded failure reports use the existing disk log and priority reserve; no console messages are added. The root cause of the movement failures and reported HP selection loss remain unresolved.

Follow START-HERE.html: one standard and one AP shot under the same long-distance missed-shot conditions, waiting10 seconds after each; load a test save once, manually selectHP, and one distant live-target HP VATS shot. Wait10 seconds, exit, and report which missed and the first two shots' aiming mode. Use the existing `bat NVOFlightKit3F` only if supplies are needed. No repeated full ammo cycle or stress test. The assistant will read the game-root NVOCombatCore.log before another launch.

Gameplay/diagnostic acceptance is pending. The plan and result are immutable transaction receipts; source, compiler output, PE/PDB identity and assembly evidence are bundled. The executed installer is tools/install_combat_3f1.ps1 in the workspace; the release copy is for audit.
'''
(PACKET/'INSTALL-3F1.md').write_text(receipt,encoding='utf-8')
for name in ('INSTALL-3F1.md','INSTALL-3F1-plan.json','INSTALL-3F1-result.json'):shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
manifest.update(status='Installed; user diagnostic check pending',installed_by_assistant=True,installation_receipt='Installation/INSTALL-3F1.md')
for p in (RELEASE/'manifest.json',PROJECT/'manifest.json',RELEASE/'Source/NVOCombatCore/manifest.json'):p.write_text(json.dumps(manifest,indent=2)+'\n')
checkpoint=f'''## Current combat checkpoint: 3F1 / native312 installed; missed-shot diagnostics pending

2026-09-15: user approved diagnostic-only packet and confirmed previously rejected projectiles missed their targets; aiming mode not established. Underlying3F identity check passes17/17, but3 long-flight displacement failures and missing post-loadHP observation remain. Native rebuilt312/0.3.12/phase3F1. Only FlightPhysics bounded diagnostic additions and Plugin/CMake version metadata changed;16 other source/header files byte-identical, all8 compiled naked bridges unchanged. Stripping marked diagnostics yields prior311 physics token stream. No new hooks, engine reads, records/configs, flight/tolerance/guard rules, ammo persistence or damage authority.

First16 displacement failures per loaded session emit4 compact priority disk rows: PHYSICS_REJECT_METRICS/MOTION/POSITION/CONTEXT. Includes separate vector/position failure flags, existing error/tolerance measurements, identities, lifetime/step/detail-cap flags, vectors, start/end/residual, velocity/age/travel and existing controller context. Maximum conservative line597bytes under766payload. Complete report/write-failure/omission counts in PHYSICS_DIAGNOSTIC_SUMMARY. Existing routine8lives/64entries/global reserve limits retained; console behaviour unchanged. No underlying physics or HP selection fix claimed.

Installed only DLL/PDB, protected {result['protected_files_verified']} entries. Backup {result['backup']}. {note} No assistant gameplay or GECK. Source/docs/evidence: source/combat/step3f1 and release/NVO-Combat-Packet-3F1-Compiled; page START-HERE.html. Current3F ESP/INIs and11 profiles unchanged; reuse bat NVOFlightKit3F. NVO/RD and prior cleanup intact.

USER CHECK: ordinaryHunting Rifle; repeat1standard .308 and1AP under same long-distance missed-shot conditions, wait10sec after each shot finishes, report aiming mode/misses without repeatedly forcing failures. Load test save once, wait3sec, manually selectHP and finish animation,1HP VATS at distant live target, wait10sec thenexit/report. No full ammo-cycle/video/stress repeat. HP persistence stays unresolved; manual selection avoids assuming it fixed. Read/archive game-root NVOCombatCore.log directly before another launch. Need actual failure measurements if reproduced, correct selection/creation identities and finalHP post-load context/free-flight. If no failure reproduces say so, not fixed. Ask before another packet or physics change; do not relax tolerances or enable damage authority.

'''
(PACKET/'CHECKPOINT-INSTALLED.md').write_text(checkpoint,encoding='utf-8')
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    old=p.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first,sep,rest=old.partition(b'\n');p.write_bytes(first+sep+b'\n'+checkpoint.encode()+rest)
for href in re.findall(r'href="([^"]+)"',(RELEASE/'START-HERE.html').read_text()):assert (RELEASE/href).is_file(),href
archive=ROOT/'release/NVO-Combat-Packet-3F1-Compiled.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(RELEASE).as_posix())
info=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
(PACKET/'RELEASE.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(dict(installed=True,version=312,backup=result['backup'],release=info,test_page=str(RELEASE/'START-HERE.html')),indent=2))
