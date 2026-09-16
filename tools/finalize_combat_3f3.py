"""Verify the installed pair and publish the user checkpoint. No game launch."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3f3'
RELEASE=ROOT/'release/NVO-Combat-Packet-3F3-Compiled'
GAME=Path('C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
result=json.loads((PACKET/'INSTALL-3F3-result.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((RELEASE/'manifest.json').read_text())
assert result['status']=='installed' and result['version']==314 and result['packet']=='3F3'
assert result['replaced']==2 and len(result['installed'])==2 and result['archived_removed']==0
assert {r['path']:r['sha256'] for r in result['installed']}=={r['path']:r['sha256'] for r in manifest['installed_files']}
for r in result['installed']:assert hashlib.sha256((GAME/r['path']).read_bytes()).hexdigest()==r['sha256']
assert not result['game_relaunched'] and not result['gameplay_tested']
hashes='\n'.join(f'- {r["path"]}: {r["sha256"]}' for r in result['installed'])
receipt=f'''# Packet 3F3 / native 314 installed

Replaced only NVOCombatCore.dll and its matching PDB. Verified {result['protected_files_verified']} protected entries unchanged. No game was running during installation. No assistant launch, gameplay or GECK operation.

Backup: {result['backup']}

{hashes}

Rollback: close New Vegas and restore both files from the backup's originals/Data/NVSE/Plugins directory into the game's matching directory. This restores native 313. Keep the existing ESP/INIs/kit, NVO/RD masters, activation and saves.

Expected header: NVOCombatCore 0.3.14 / phase=3F3. Plugin version: 314. New FLIGHT_RANGE rows are in the game-root NVOCombatCore.log. Follow START-HERE.html for one hip-fired shot and the original distant VATS miss attempt. Flight/range/damage rules are unchanged; terrain-correction acceptance is still pending.
'''
(PACKET/'INSTALL-3F3.md').write_text(receipt)
for name in ('INSTALL-3F3.md','INSTALL-3F3-plan.json','INSTALL-3F3-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
manifest.update(status='Installed; user range/lifetime and terrain-correction checkpoint pending',installed_by_assistant=True,installation_receipt='Installation/INSTALL-3F3.md')
for p in (RELEASE/'manifest.json',PROJECT/'manifest.json',RELEASE/'Source/NVOCombatCore/manifest.json'):
    p.write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copyfile(PROJECT/'reference/FIRING-RANGE-NOTES.md',RELEASE/'Source/NVOCombatCore/reference/FIRING-RANGE-NOTES.md')
for name in ('finalize_combat_3f3.py','audit_flight_capture.py'):
    shutil.copyfile(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
checkpoint=f'''## Current combat checkpoint: 3F3 / native 314 installed; range diagnostics pending

2026-09-15: user approved the range diagnostic packet and will try to reproduce the original shot. Packet 3F3 replaces only DLL/PDB, build-15366-14296; zero MSVC warnings/errors, matching PE32/PDB, nine compiled physics bridges unchanged. {result['protected_files_verified']} protected entries unchanged. Backup: {result['backup']}. No assistant gameplay, GECK or game launch. See source/combat/step3f3/INSTALL-3F3.md and release/NVO-Combat-Packet-3F3-Compiled/START-HERE.html.

Corrected source interpretation: +0x14C is used by the passing-sound route, not the firing limit. Projectile +0xD4 is fRange in Stewie/ITR and initialized/multiplied by saved engine code 009BDD10..009BDDC0 using GMST fCombatIronSightsRangeMult at011CE5F4. Authenticated saved capture and source hashes are in ENGINE-FINDINGS.json. No universal VATS multiplier or exact destruction cause is asserted. Native reference/FIRING-RANGE-NOTES.md retains this finding for future work.

FlightPreview adds optional D4/C8/90 reads after existing identity checks, cached launch values, FLIGHT_RANGE at creation/first impact/destruction (32 sampled lifetimes, at most96 rows per load), and a summary of optional-read/log failures. No per-frame additions or new console messages. Zero/invalid fields require validity masks. Range reached is a numerical comparison only, with cause=unverified. All physics source, nine bridges, integrator, terrain correction, tolerances, observer/logger/timing, records, configs, damage and ammo effects remain unchanged. Optional read failures cannot gate tracking or movement. Plugin314/header0.3.14/phase3F3. New log formats bounded to689/284 bytes under766-byte limit.

USER CHECK: ordinary Hunting Rifle, standard .308. One hip-fired shot outside VATS without iron sights, wait15s, then original distant VATS miss attempt, wait15s after VATS ends. Up to2 more reproduction attempts if needed; then stop and report shot modes/hit-miss order. No required reload/ammo cycle. Existing bat NVOFlightKit3F is optional. Read/archive game-root log directly before relaunch. Reuse tools/audit_flight_capture.py for range-row identity and flight audit; inspect creation vs ending range and lifecycle, do not infer exact cause from range_reached alone. Terrain fix still UNEXERCISED as of prior captures; accept only with failed-query correction plus matching accounting. Await user's test, ASK before another packet. Fixture was declined: do not build/re-offer it. Preserve prior evidence/backups and later armour/contact-energy/unit-calibration/RD-master/HP-persistence work.
'''
(PACKET/'CHECKPOINT-INSTALLED.md').write_text(checkpoint)
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    old=p.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first,sep,rest=old.partition(b'\n');p.write_bytes(first+sep+b'\n'+checkpoint.encode()+b'\n'+rest)
for href in re.findall(r'href="([^"]+)"',(RELEASE/'START-HERE.html').read_text()):assert (RELEASE/href).is_file(),href
archive=RELEASE.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(RELEASE).as_posix())
info=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
(PACKET/'RELEASE.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(dict(version=314,protected=result['protected_files_verified'],backup=result['backup'],release=info,test_page=str(RELEASE/'START-HERE.html')),indent=2))
