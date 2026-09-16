"""Record the completed 3D install and make the distributable archive."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'source/combat/step3d'
RELEASE=ROOT/'release/NVO-Combat-Packet-3D-Compiled'
result=json.loads((PACKET/'INSTALL-3D-result.json').read_text(encoding='utf-8-sig'))
assert result['status']=='installed' and result['version']==311 and len(result['installed'])==6
manifest=json.loads((RELEASE/'manifest.json').read_text())
evidence=json.loads((RELEASE/'build-evidence/static-evidence.json').read_text())
assert {r['path']:r['sha256'] for r in result['installed']}=={r['path']:r['sha256'] for r in manifest['installed_files']}
receipt=f'''# Packet3D / build311 installed

Installed six approved files; five replaced and one new kit file. {result['protected_files_verified']} protected entries, including NVO.esm, other extenders and activation, verified unchanged. New Vegas was already closed. No assistant game launch, gameplay or GECK work.

Backup: `{result['backup']}`

With the game closed, restore these five files from the backup's `originals` directory to the same relative paths below the game root:

- Data/NVSE/Plugins/NVOCombatCore.dll
- Data/NVSE/Plugins/NVOCombatCore.pdb
- Data/NVSE/Plugins/NVOFlightPreview.ini
- Data/NVSE/Plugins/NVOFlightPhysics.ini
- Data/NVOFlightPilot.esp

Remove the new game-root NVOFlightKit.txt to complete reversal. Do not mix the old DLL with schema2 INIs. The backup also preserves logs and original hashes. The original six private records remain unchanged in the expanded ESP; no stock forms or NVO.esm were overridden.

Build {manifest['build_output']}, zero compiler warnings/errors. PE32 x86, exactly NVSEPlugin_Query and NVSEPlugin_Load, matching PDB GUID {evidence['codeview_pdb_guid']} age{evidence['pdb_age']}.

DLL SHA256 {evidence['dll_sha256']}

PDB SHA256 {evidence['pdb_sha256']}

Run `bat NVOFlightKit` after loading a test save and waiting three seconds. Follow START-HERE.html for the four-weapon checkpoint and one reload/Service Rifle VATS shot. Native damage replacement remains disabled. Runtime acceptance is pending; a successful installation is not a gameplay pass.

INSTALL-3D-plan.json and INSTALL-3D-result.json record the exact transaction. Do not regenerate pre-install hashes after installation.
'''
(PACKET/'INSTALL-3D.md').write_text(receipt,encoding='utf-8')
for name in ('INSTALL-3D.md','INSTALL-3D-plan.json','INSTALL-3D-result.json'):shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
archive=ROOT/'release/NVO-Combat-Packet-3D-Compiled.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(RELEASE).as_posix())
zipsha=hashlib.sha256(archive.read_bytes()).hexdigest()
checkpoint=f'''## Current combat checkpoint: 3D / 311 installed; four regular weapons await user check

2026-09-15: user approved expanding to ordinary9mm Pistol, Hunting Rifle,9mm SMG and Service Rifle with standard9mm/.308/5.56, and requested a kit batch. Built and installed311/0.3.11. See source/combat/step3d/README.md, IMPLEMENTATION.md, RECORD-AUDIT.json, SOURCE-PROVENANCE.json and INSTALL-3D.md. Uses ShowOff:OnPreProjectileCreate native form return to select one of four private projectile bases for exact weapon/equipped-ammo/original-projectile matches. No stock WEAP/AMMO/PROJ override; no NVO.esm edits. Appends PROJ806..809 to existing NVOFlightPilot.esp, old six records byte-identical. Both activation files unchanged. No new native hook site; old movement bridges/guards/tolerances unchanged. Physics BC/model now per lifetime from schema2 profiles (six including old private pairs). Cached projectile-list/form/84-byte-DATA validation; main-thread-only selection; strict equipped process branch, no default-ammo guess. Unknown/unavailable selection returns original. Actual creation must confirm the selected base/ammo before NVO tracks it. Other event handlers/dynamic state not generally certified. New selector correctness awaits gameplay.

Build native/NVOCombatCore/{manifest['build_output']}: zero warnings/errors, PE32x86, two exports, matching PDB GUID{evidence['codeview_pdb_guid']} age1. DLL SHA{evidence['dll_sha256']}, PDB SHA{evidence['pdb_sha256']}. CurrentHit/DamageEvents/FlightTiming/NativeLog source-identical to310. Six install files: DLL/PDB, both flight INIs, expanded NVOFlightPilot.esp and new game-root NVOFlightKit.txt. Five replaced, one created; {result['protected_files_verified']} protected entries unchanged. Backup {result['backup']}. Game already closed, no assistant launch/test/GECK. Compiled ZIP SHA{zipsha}. Old310 accepted regression remains archived separately.

Next USER checkpoint: keep NVO.esm+NVOFlightPilot.esp active; load prepared save, wait3s, `bat NVOFlightKit` grants ordinary four guns and standard ammo (3009mm,100.308,2005.56). Outside VATS, far solid target: one pistol, one hunting rifle, one service rifle, then short~3-roundSMG burst. Reload original save once, wait3s, regrant if needed, one distant live-target Service Rifle VATS shot. Exit/report; assistant reads and archives game-root NVOCombatCore.log before another launch. Need FLIGHT_SELECTOR_READY ready1, FLIGHT_SELECT matching actual created private base/actual ammo, meaningful verified free-flight segments, clean automatic lifetimes and reload, no guard/tracking faults. No video/stress/GECK needed. Do not infer success from selection return or compilation. Damage replacement disabled; contact-energy/calibration/initial unchanged segment remain limitations. Ask before another packet after reviewing results.

'''
(PACKET/'CHECKPOINT-INSTALLED.md').write_text(checkpoint,encoding='utf-8')
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    old=p.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first,sep,rest=old.partition(b'\n');p.write_bytes(first+sep+b'\n'+checkpoint.encode()+rest)
print(json.dumps(dict(installed=True,version=311,backup=result['backup'],zip_sha256=zipsha,zip_bytes=archive.stat().st_size,
                      test_page=str(RELEASE/'START-HERE.html')),indent=2))
