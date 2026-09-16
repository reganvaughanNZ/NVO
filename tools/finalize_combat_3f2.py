"""Verify installation and record the next user checkpoint; never launch the game."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3f2'
RELEASE=ROOT/'release/NVO-Combat-Packet-3F2-Compiled'
GAME=Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
result=json.loads((PACKET/'INSTALL-3F2-result.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((RELEASE/'manifest.json').read_text())
assert result['status']=='installed' and result['packet']=='3F2' and result['version']==313
assert result['replaced']==2 and len(result['installed'])==2
assert {r['path']:r['sha256'] for r in result['installed']}=={r['path']:r['sha256'] for r in manifest['installed_files']}
for row in result['installed']:
    assert hashlib.sha256((GAME/row['path']).read_bytes()).hexdigest()==row['sha256']
assert not result['game_relaunched'] and not result['gameplay_tested']
hashes='\n'.join(f'- `{r["path"]}`: `{r["sha256"]}`' for r in result['installed'])
receipt=f'''# Packet3F2 / native313 installed

Replaced only the DLL and matching PDB. Verified {result['protected_files_verified']} protected entries unchanged. Closed processes: {len(result['closed_processes'])}, under the user's existing permission. No assistant launch, gameplay or GECK operation.

Backup: `{result['backup']}`

{hashes}

Rollback: close New Vegas and restore both files from the backup's originals/Data/NVSE/Plugins directory to the game's matching directory. This restores native312. Keep current3F ESP/INIs/kit and NVO/RD masters; no load-order or save changes are required.

New header0.3.13 / phase3F2; GetPluginVersion returns313. Terrain query correction and following accounting must be observed before accepting the gameplay fix. No change to damage authority, ammo tuning or HP save persistence. Follow START-HERE.html for the short VATS miss/reload/HP check.
'''
(PACKET/'INSTALL-3F2.md').write_text(receipt)
for name in ('INSTALL-3F2.md','INSTALL-3F2-plan.json','INSTALL-3F2-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
manifest.update(status='Installed; user terrain-correction checkpoint pending',installed_by_assistant=True,
                installation_receipt='Installation/INSTALL-3F2.md')
for p in (RELEASE/'manifest.json',PROJECT/'manifest.json',RELEASE/'Source/NVOCombatCore/manifest.json'):
    p.write_text(json.dumps(manifest,indent=2)+'\n')
checkpoint=f'''## Current combat checkpoint: 3F2 / native313 installed; failed-terrain correction pending

2026-09-15: user clarified3F1 shot3 was a VATS miss and approved continuing. Preserved capture77ebadbd30fd and its review; VATS context added to capture metadata/REVIEW-1. Read-only running-engine captures under source/combat/step3f2 establish: terrain query004572E0 writes default -2048 and can returnfalse, generic movement00930150 ignores AL and raises candidate Z if height minus Z >30. Previous57.27-unit raise is consistent; actual failed-query/corrected-accounting correlation is still the gameplay checkpoint. On-disk code differs and was excluded. Engine binary captures not distributed.

Native313/0.3.13/phase3F2 adds one guarded CALL wrapper at00930150. Original query executes once; successful results unchanged. Verified private applied steps with accepted baseline, same frame/thread/controller, no contact, failed default query, >30 threshold and matching candidate use candidate Z as the checked stack height result. Independent accounting guard/tolerance unchanged. Original8 bridges/integrator/16 other files unchanged. New query/default/threshold fingerprints and expanded protect/flush/rollback coverage on same existing page. No damage authority/records/config/ammo or HP persistence changes. Normal character movement takes an immediate original-function path.

Compiled and statically inspected build-5269-6975, zero warnings/errors, matching PE32/PDB,9 bridges. Installed only DLL/PDB, {result['protected_files_verified']} protected entries unchanged; backup {result['backup']}. No assistant gameplay/GECK. PHYSICS_TERRAIN_READY, REJECT_DEFAULT, REJECT_DEFAULT_VERIFIED and SUMMARY are disk diagnostics; REJECT_DEFAULT rejects the invalid default, not the track. Logs detail first16 corrections/16 verifications per load; counts continue. Existing PHYSICS_REJECT is actual failure. No new console spam.

USER CHECK: repeat same distant Hunting Rifle standard .308 VATS miss setup, one shot then wait15s after VATS. Up to2 additional tries if it hits, do not indefinitely force misses. Load test save once, wait3s, manually selectHP and one farther live-target VATS shot. Wait15s, exit, report. Existing bat NVOFlightKit3F optional. Read/archive log directly before relaunch. Need exact terrain-correction and matching accounting correlation, clean lifecycle, finalHP identity/hit; if no path reproduces, do not call fix proven. Await user result; ask before another packet. RD master removal, unit calibration, initial unchanged segment, contact-energy and HP persistence remain separate.

Reusable offline helper tools/inspect_runtime_capture.py verifies hashes and disassembles only saved engine-code ranges without execution. Read-only capture helpers are saved alongside. Reuse confirmed addresses/hashes/evidence rather than repeating exploratory searches.

'''
(PACKET/'CHECKPOINT-INSTALLED.md').write_text(checkpoint)
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    old=p.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first,sep,rest=old.partition(b'\n');p.write_bytes(first+sep+b'\n'+checkpoint.encode()+rest)
for href in re.findall(r'href="([^"]+)"',(RELEASE/'START-HERE.html').read_text()):
    assert (RELEASE/href).is_file(),href
archive=RELEASE.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(RELEASE).as_posix())
info=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
(PACKET/'RELEASE.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(dict(version=313,backup=result['backup'],protected=result['protected_files_verified'],
    release=info,test_page=str(RELEASE/'START-HERE.html')),indent=2))
