"""Verify the installed pair and publish the user checkpoint. No game launch."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3g'
RELEASE=ROOT/'release/NVO-Combat-Packet-3G-Compiled'
GAME=Path('C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
result=json.loads((PACKET/'INSTALL-3G-result.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((RELEASE/'manifest.json').read_text())
assert result['status']=='installed' and result['version']==315 and result['packet']=='3G'
assert result['replaced']==2 and len(result['installed'])==2 and result['archived_removed']==0
assert {r['path']:r['sha256'] for r in result['installed']}=={r['path']:r['sha256'] for r in manifest['installed_files']}
for r in result['installed']:assert hashlib.sha256((GAME/r['path']).read_bytes()).hexdigest()==r['sha256']
assert not result['game_relaunched'] and not result['gameplay_tested']
hashes='\n'.join(f'- {r["path"]}: {r["sha256"]}' for r in result['installed'])
receipt=f'''# Packet 3G / native 315 installed

Replaced only NVOCombatCore.dll and its matching PDB. Verified {result['protected_files_verified']} protected entries unchanged. No game was running during installation. No assistant launch, gameplay or GECK operation.

Backup: {result['backup']}

{hashes}

Rollback: close New Vegas and restore both files from the backup's originals/Data/NVSE/Plugins directory into the game's matching directory. This restores native 314. Keep the existing ESP/INIs/kit, NVO/RD masters, activation and saves.

Expected header: NVOCombatCore 0.3.15 / phase=3G. Plugin version: 315. New IMPACT_ rows are in the game-root NVOCombatCore.log. Follow START-HERE.html for a very close solid-object shot, normal live-target hit and farther live-target VATS hit. Flight/range/damage rules are unchanged; the prior terrain correction remains accepted. Collision geometry and candidate speed estimates await the user test.
'''
(PACKET/'INSTALL-3G.md').write_text(receipt)
for name in ('INSTALL-3G.md','INSTALL-3G-plan.json','INSTALL-3G-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
manifest.update(status='Installed; user collision-step and impact-speed diagnostic checkpoint pending',installed_by_assistant=True,installation_receipt='Installation/INSTALL-3G.md')
for p in (RELEASE/'manifest.json',PROJECT/'manifest.json',RELEASE/'Source/NVOCombatCore/manifest.json'):
    p.write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copyfile(PROJECT/'reference/IMPACT-SPEED-NOTES.md',RELEASE/'Source/NVOCombatCore/reference/IMPACT-SPEED-NOTES.md')
for name in ('finalize_combat_3g.py','audit_flight_capture.py'):
    shutil.copyfile(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
checkpoint=f'''## Current combat checkpoint: 3G / native 315 installed; impact-speed diagnostics pending

2026-09-15: user approved the next impact-speed diagnostic packet after accepting3F3 terrain/range results. Installed only DLL/PDB, build-24800-2378, zero compiler warnings/errors, matching PE32/PDB, nine compiled physics bridges unchanged. {result['protected_files_verified']} protected entries unchanged. Backup: {result['backup']}. No assistant game launch/gameplay/GECK. See source/combat/step3g/INSTALL-3G.md and release/NVO-Combat-Packet-3G-Compiled/START-HERE.html.

New private source FlightImpact.inl adds read-only collision-step observations at the existing BeforeAccounting contact branch and pairs later impact callbacks before existing retirement. Source guards prove that removing the include and four diagnostic calls yields native314 FlightPhysics.cpp exactly; headers, FlightPreview/range diagnostics, observer, timing, hit/damage and logger are unchanged. No new engine hook, no new console messages, no game/Track mutation by diagnostics. Existing terrain correction stays accepted; flight/penetration/damage behavior unchanged.

Source/log evidence: ShowOff dispatches impact after collision/damage and moves projectile position to first contact. Previous3F3 lifetime8 counts1740.10254 full-step units but position moves287.051876; Track.velocity at impact remains start-of-collision-step speed because collision steps skip acceptance. Record earlier start/expected/contact/position/accounting vectors, initial/proposed velocities, dt, profile inputs and target/region. First8 logged physics lifetimes only; max48 extra detail rows/load with first-callback dedup even when collision sample absent. IMPACT_SUMMARY reports optional read failures, unavailable/correlated cases, duplicates and log failures. Native315/header0.3.15/phase3G. All new formats <=587 bytes under766 limit.

Optional snapshots validate exact identity and guarded reads; masks31 collision /15 callback. Extra contact nodes are ambiguous. Candidate requires complete single-contact geometry inside proposed chord and matching actual/contact positions at existing tolerance, baseline verified and applied step, forward endpoint velocities.24 bounded bisection iterations use unchanged integrator on local velocity copies to infer partial time from projected progress. Result is model_estimate_only, speed_authority=0, contact_time_measured=0, units_calibrated=0; raw candidate values with candidate_valid=0 are not usable. Baseline contacts, unknown geometry, unavailable/changed contacts remain explicit. Candidate plus later contact correlation require gameplay review before any future interface uses speed. No cartridge mass/energy/armour authority yet.

USER CHECK: ordinary Hunting Rifle, standard .308.1 very close solid-object impact outside VATS;2 normal-distance live-target hit outside VATS;3 another live-target hit farther away in VATS. Clear shot paths; wait3s after impacts, at most1 replacement per missed check, then wait20s after final shot, exit/report hit-miss order. No reload/stress/long-miss cycle. Existing bat NVOFlightKit3F optional. Read/archive log before relaunch; use tools/audit_flight_capture.py to collect IMPACT records and correlate identities, then inspect geometry, model estimate and callback pairing explicitly. If unavailable, diagnose boundary representation from data; do not silently substitute last speed. Await user result and ASK before next packet.

Preserve3F3 accepted terrain/range findings and9-shot capture3130ae056efd. Unit calibration, first unchanged segment, exact contact-time interpretation, cartridge mass/energy, ammo-specific flight tuning, penetration/armour/wounds, RD master removal and HP selection persistence remain outstanding. Do not re-offer declined fixture or repeat already accepted terrain testing without new evidence.
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
print(json.dumps(dict(version=315,protected=result['protected_files_verified'],backup=result['backup'],release=info,test_page=str(RELEASE/'START-HERE.html')),indent=2))
