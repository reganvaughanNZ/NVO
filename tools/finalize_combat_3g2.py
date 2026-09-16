"""Verify installed317 pair, publish receipt/checkpoint and release archive."""
from pathlib import Path
import hashlib,json,re,shutil,zipfile

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3g2'
RELEASE=ROOT/'release/NVO-Combat-Packet-3G2-Compiled'
GAME=Path('C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
result=json.loads((PACKET/'INSTALL-3G2-result.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((RELEASE/'manifest.json').read_text())
assert result['status']=='installed' and result['version']==317 and result['packet']=='3G2'
assert result['replaced']==2 and len(result['installed'])==2 and result['archived_removed']==0
assert not result['game_relaunched'] and not result['gameplay_tested']
assert {r['path']:r['sha256'] for r in result['installed']}=={r['path']:r['sha256'] for r in manifest['installed_files']}
for r in result['installed']:assert hashlib.sha256((GAME/r['path']).read_bytes()).hexdigest()==r['sha256']
hashes='\n'.join(f'- {r["path"]}: {r["sha256"]}' for r in result['installed'])
receipt=f'''# Packet3G2 / native317 installed

Replaced only NVOCombatCore.dll and its matching PDB. Verified {result['protected_files_verified']} protected entries unchanged. Closed processes: {len(result['closed_processes'])}. No assistant game launch, gameplay or GECK operation.

Backup: {result['backup']}

{hashes}

Reversal: close New Vegas and restore both files from this backup's originals/Data/NVSE/Plugins into the matching game folder. This restores native316. Keep current NVO.esm, NVOFlightPilot.esp, their masters, INIs, kit, activation and saves.

Expected header: NVOCombatCore0.3.17 / phase=3G2; plugin version317. Game-root NVOCombatCore.log contains IMPACT_HIT, IMPACT_HIT_MODEL, IMPACT_HIT_POSITION and IMPACT_HIT_SUMMARY. No new console message or GECK work. Follow START-HERE.html for three shots; user live confirmation remains pending. Flight, terrain and damage rules are unchanged.
'''
(PACKET/'INSTALL-3G2.md').write_text(receipt)
for name in ('INSTALL-3G2.md','INSTALL-3G2-plan.json','INSTALL-3G2-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
manifest.update(status='Installed; user317 diagnostic confirmation pending',installed_by_assistant=True,installation_receipt='Installation/INSTALL-3G2.md')
for p in (RELEASE/'manifest.json',PROJECT/'manifest.json',RELEASE/'Source/NVOCombatCore/manifest.json'):
    p.write_text(json.dumps(manifest,indent=2)+'\n')
for name in ('finalize_combat_3g2.py','audit_flight_capture.py'):
    shutil.copyfile(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
checkpoint=f'''## Current combat checkpoint:3G2 /native317 installed; live joined-hit test pending

2026-09-15: user approved continuation, suggested the316 VATS head aim may have struck torso, and requested Ultra review before damage. Preserve this as a hypothesis, not confirmed landing. Installed only DLL/PDB, build-2341-20217, zero compiler warnings/errors, matching PE32/PDB and expected2exports. Nine physics bridges and CopyObserver compiled bridge unchanged;16 baseline files byte-identical including model/drag/CurrentHit. {result['protected_files_verified']} protected entries unchanged. Backup: {result['backup']}. No game running/closed or assistant gameplay/GECK. See source/combat/step3g2/INSTALL-3G2.md and release/NVO-Combat-Packet-3G2-Compiled/START-HERE.html.

New internal HitQuery copies current-hit IDs, region, flags and position after existing target/process validation. ObserveHit checks active session/lifetime under physics lock and joins cached model against fresh guarded contact. No engine call, Track/game/hit-data writes or new hook. Existing observer->physics->logger ordering. New FlightImpactJoin.inl rejects mismatched identity/target/contact, multiple/unreadable/no-sample/late cases; logs hit_region/contact_region separately without choosing armour authority. Model status/speed/time cached once. Earlier-than-movement contacts now labelled with actual target when readable. Hit-query budget64/192rows, prior impact32lifetimes;416combined detail rows +3summaries/load, global limits unchanged. No new console message. All formats<=587bytes. Model/tolerances/flight/damage unchanged; version317/header0.3.17/phase3G2.

Offline replay of316 capture9a54c6410f44 preserves one808.438545m/s model and one unavailable off-chord result. Actual C++ join/cache with captured-read stubs checks separate regions, wrong identity/target, changed contact, late callback, untracked profile, early/multiple/missing reads, query cap/reset, prior model guards and32lifetime coverage. No live317 acceptance yet. Source provenance JIP GameProcess.h ActorHitData+10 and hooks.h CopyHitDataHook2286; ShowOff decoding.h ImpactData+24. Input is copied before original JIP tail-call, which copies region rather than resolving the observed upstream discrepancy. Source does not settle VATS intended-vs-physical landing.

USER CHECK: ordinary Hunting Rifle/standard .308.1 nearby rock outside VATS;2 live target head aim in VATS at previous farther distance;3 live target torso aim outside VATS at similar distance. Keep targets alive/replaced; kill not required.3s between impacts, at most1 replacement per missed check,20s after final then exit/report aim/mode/result (uncertainty okay). No reload/stress/long miss. Read/archive log before relaunch; audit helper collects IMPACT_HIT/MODEL/POSITION/SUMMARY. Review same-context identities, availability and separate regions. Ask before subsequent gameplay packet.

USER-AUTHORIZED ULTRA GATE: source/combat/PRE-DAMAGE-REVIEW.md. Status pending, not yet run; damage disabled. Before implementing damage, after live3G2 and foundation decisions, prepare exact current source/build/profile/evidence index, run one independent reviewer at ultra with minimal fresh context (user explicitly requested), then only affected fixes/deltas. No need to request permission again simply for this authorized review. Do not claim Ultra ran or change this task's setting silently. Review everything relevant to active combat, not every unused donor/archive. No damage activation until material findings resolved and explicit next-packet approval. Plan:1foundation,2hit observation,3flight/current317,4armour/damage,5wounds/medicine,6remainingweapon effects,7AI/morale,8background balance. Unit calibration, mass/energy, immediate-contact speed policy, region producers and actual pre-damage handoff unresolved. Preserve3F3 terrain/range acceptance; RD master removal and HP ammo persistence separate.
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
print(json.dumps(dict(version=317,protected=result['protected_files_verified'],backup=result['backup'],release=info,test_page=str(RELEASE/'START-HERE.html')),indent=2))
