"""Record installation and package user instructions without launching the game."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'source/combat/step3f'
RELEASE = ROOT/'release/NVO-Combat-Packet-3F-Update'
GAME = Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
result = json.loads((PACKET/'INSTALL-3F-result.json').read_text(encoding='utf-8-sig'))
manifest = json.loads((RELEASE/'manifest.json').read_text())
assert result['status'] == 'installed' and result['packet'] == '3F' and result['version'] == 311
assert result['replaced'] == 2 and len(result['installed']) == 3
assert {r['path']:r['sha256'] for r in result['installed']} == {r['path']:r['sha256'] for r in manifest['installed_files']}
for row in result['installed']:
    assert hashlib.sha256((GAME/row['path']).read_bytes()).hexdigest() == row['sha256']
assert not result['game_relaunched'] and not result['gameplay_tested']
process_note = 'New Vegas was already closed.' if not result['closed_processes'] else 'The verified New Vegas process was closed under existing user permission.'
file_list = '\n'.join(f'- `{r["path"]}` — SHA256 `{r["sha256"]}`' for r in result['installed'])
receipt = f'''# Packet 3F installed — Hunting Rifle standard/AP/HP checkpoint

Installed the preview INI, private-projectile ESP and new console kit: two replacements and one new file. {result['protected_files_verified']} protected entries verified unchanged, including NVO.esm/RD.esm, native DLL/PDB, other retained NVSE files, physics INI, older kits and both activation files. {process_note} No assistant game launch, gameplay or GECK work.

Backup: `{result['backup']}`

{file_list}

To reverse: close New Vegas, restore **Data/NVOFlightPilot.esp** and **Data/NVSE/Plugins/NVOFlightPreview.ini** from this backup's `originals` directory to the matching game paths, then remove the new game-root **NVOFlightKit3F.txt**. Restore both files together. Keep the existing DLL, physics INI, older kits, NVO.esm and RD.esm. This returns to accepted 3E and does not undo the separate unused-file cleanup.

Native build311 /0.3.11/phase3D stays unchanged. Eleven loaded profiles and private projectiles080D/080E identify3F. The previous13 complete private records and9 profiles are preserved. All18 native source/header files match the accepted3D source snapshot. NVO damage replacement remains disabled. AP/HP flight inputs deliberately match standard .308 for an identity checkpoint; no claim of variant ballistic calibration.

Run `bat NVOFlightKit3F` in the game console after loading your prepared save and waiting three seconds. Fire standard → AP → HP → standard outside VATS at distant scenery. Select HP, finish switching, make a test save and load that save once. Wait three seconds, confirm HP and fire one HP VATS shot at a distant live target. Exit and report completion or any miss/selection change. Full instructions are in START-HERE.html and README.md. Gameplay acceptance is pending.

The plan/result are immutable transaction records. The release's installer copy is for audit; the executed workspace script is tools/install_combat_3f.ps1.
'''
(PACKET/'INSTALL-3F.md').write_text(receipt,encoding='utf-8')
for name in ('INSTALL-3F.md','INSTALL-3F-plan.json','INSTALL-3F-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
manifest.update(status='Installed; user gameplay check pending',installation_receipt='Installation/INSTALL-3F.md')
(RELEASE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
checkpoint = f'''## Current combat checkpoint: 3F / native311 installed; .308 ammo-identity check pending

2026-09-15: user approved the proposed one-weapon standard/AP/HP packet after 3E passed. Ordinary Hunting Rifle00004333 uses source0008F20A. Standard ammo0006B53C stays on private0807/profile hunting-rifle. AP0013E442 -> new080D/profile hunting-rifle-ap; HP0013E443 -> new080E/profile hunting-rifle-hp. Added two private PROJs and two exact profiles, preserving all13 previous private records and9 profiles, total11. Both added profiles deliberately share accepted standard .308 tuning (G7 BC.209, maximum1012, barrel22, peak2.1, muzzle849.770992366 m/s). This checks identity and flight; variant tuning/calibration is future work. Native DLL/PDB/18 source files unchanged, build311/phase3D expected. No armour, damage authority or donor conversion scripts added. No stock WEAP/AMMO/AMEF changes. AP existing DT-15 and damage*.95, HP DT*3 and damage*1.75 retained by engine.

Installed two replacements (ESP + previewINI), new NVOFlightKit3F.txt; {result['protected_files_verified']} protected entries unchanged. Backup {result['backup']}. {process_note} No assistant gameplay/GECK. Source and checks: source/combat/step3f/RECORD-AUDIT.json, STATIC-CHECKS.json, IMPLEMENTATION.md, INSTALL-3F.md. Test page release/NVO-Combat-Packet-3F-Update/START-HERE.html. Prior3E acceptance and unused-file cleanup remain intact. RD.esm retained pending separately requested reference migration.

USER CHECK: prepared save, wait3s, bat NVOFlightKit3F (ordinary rifle +40 each of standard/AP/HP). At distant scenery outsideVATS: standard -> AP -> HP -> standard, one shot each, confirm label and let switch finish. Then selectHP, save, load that save once, wait3s, confirmHP and one HP VATS shot at distant live target. Report misses, unexpected ammo change, extra shots or setup loads. Exit before reporting. Read/archive root NVOCombatCore.log directly before another launch. Need all three correct selector/creation ammo+private pairs, matching edited free-flight, clean reset and linked final HP actor hit. VATS is user context; miss alone is not flight failure. No video/stress/old-weapon retest. Ask before next packet after review. Unit calibration, initial unchanged segment and contact-energy/collision limitations remain before armour authority.

'''
(PACKET/'CHECKPOINT-INSTALLED.md').write_text(checkpoint,encoding='utf-8')
for path in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    old=path.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first, sep, rest=old.partition(b'\n');path.write_bytes(first+sep+b'\n'+checkpoint.encode()+rest)
# Every local page link must point to a packaged file before delivery.
import re
for href in re.findall(r'href="([^"]+)"',(RELEASE/'START-HERE.html').read_text()):
    assert (RELEASE/href).is_file(), ('Broken page link',href)
archive=ROOT/'release/NVO-Combat-Packet-3F-Update.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted(RELEASE.rglob('*')):
        if path.is_file():z.write(path,path.relative_to(RELEASE).as_posix())
info=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
(PACKET/'RELEASE.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(dict(installed=True,packet='3F',native_version=311,backup=result['backup'],
                     zip=info,test_page=str(RELEASE/'START-HERE.html')),indent=2))
