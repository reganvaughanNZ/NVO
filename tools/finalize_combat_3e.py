"""Record the installed 3E update and its user checkpoint; no game execution."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'source/combat/step3e'
RELEASE = ROOT/'release/NVO-Combat-Packet-3E-Update'
GAME = Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
result = json.loads((PACKET/'INSTALL-3E-result.json').read_text(encoding='utf-8-sig'))
manifest = json.loads((RELEASE/'manifest.json').read_text())
assert result['status'] == 'installed' and result['packet'] == '3E' and result['version'] == 311
assert result['replaced'] == 2 and len(result['installed']) == 3
assert {r['path']:r['sha256'] for r in result['installed']} == {r['path']:r['sha256'] for r in manifest['installed_files']}
for row in result['installed']:
    assert hashlib.sha256((GAME/row['path']).read_bytes()).hexdigest() == row['sha256']
assert not result['game_relaunched'] and not result['gameplay_tested']
process_note = 'New Vegas was already closed.' if not result['closed_processes'] else 'The installer closed the verified New Vegas process under existing permission.'
file_list = '\n'.join(f'- `{r["path"]}` - SHA256 `{r["sha256"]}`' for r in result['installed'])
receipt = f'''# Packet 3E installed - three standard-ammunition profiles

Installed the approved preview INI, expanded private-projectile ESP and new console kit. Two existing files replaced and one kit added. {result['protected_files_verified']} protected entries verified unchanged, including NVO.esm, the native DLL/PDB, other extenders, physics INI, older kits and activation. {process_note} No assistant game launch, gameplay or GECK work.

Backup: `{result['backup']}`

Installed hashes:

{file_list}

To reverse, close the game, restore **Data/NVOFlightPilot.esp** and **Data/NVSE/Plugins/NVOFlightPreview.ini** from this backup's `originals` directory into the matching game paths, then remove the newly added game-root **NVOFlightKit3E.txt**. Restore both members of the record/config pair. Keep the existing DLL, physics INI, older kits and NVO.esm. This returns to the accepted 3D1 configuration. Logs and preimage hashes are also backed up.

The DLL remains build311 /0.3.11 and its header still says phase3D. There is no new native build. Nine loaded profiles and private projectile IDs080A..080C identify3E. All18 native source/header files match the3D source snapshot. All seven ordinary mappings/clones passed static checks; previous ten complete private records and six profile sections are preserved. Damage replacement remains disabled.

Run `bat NVOFlightKit3E` inside the game after loading your prepared save and waiting three seconds. It supplies the canonical 10mm Pistol, .357 Magnum Revolver and .44 Magnum Revolver plus100 standard rounds each. Follow START-HERE.html: one shot from each at distant scenery, one reload, then one .44 shot in VATS at a distant live enemy. No previous-weapon retest required.

Gameplay acceptance is pending. INSTALL-3E-plan.json and INSTALL-3E-result.json are immutable transaction records. The installer copy in this release is an audit copy; the executed script is in the workspace tools directory.
'''
(PACKET/'INSTALL-3E.md').write_text(receipt,encoding='utf-8')
for name in ('INSTALL-3E.md','INSTALL-3E-plan.json','INSTALL-3E-result.json'):
    shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
manifest.update(status='Installed; user gameplay check pending',installation_receipt='Installation/INSTALL-3E.md')
(RELEASE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copyfile(Path(__file__),RELEASE/'Source/tools/finalize_combat_3e.py')
checkpoint = f'''## Current combat checkpoint: 3E / native311 installed; three standard-ammo profiles await user check

2026-09-15: user said continue as planned after asking about special ammunition. Continued the approved standard-calibre expansion: ordinary10mm Pistol0000434F/ammo00004241/source0002CD5F/private080A; .357 Magnum Revolver0008F216/ammo0008ED02/source0008F20C/private080B; .44 Magnum Revolver0008F215/ammo0002937E/source0003BF0C/private080C. All seven regular weapon/source mappings and clone contracts statically audited, new ammo membership/no projectile override verified, donor weapon/cartridge rows explicit. Three private PROJs appended; ten previous full private records and six profile sections preserved. Nine profiles total including two legacy private pairs. Existing DLL311/0.3.11 phase3D,18 source/header files unchanged. No native rebuild, new hooks, damage authority or special-ammo implementation.

Installed ESP+preview INI and new NVOFlightKit3E.txt (two replacements,one new);{result['protected_files_verified']} protected entries unchanged. Backup {result['backup']}. {process_note} No assistant gameplay or GECK. See source/combat/step3e/INSTALL-3E.md,RECORD-AUDIT.json,STATIC-CHECKS.json and IMPLEMENTATION.md. Release release/NVO-Combat-Packet-3E-Update/START-HERE.html. ESP SHA39802a9f7c702f3fc1d74b2703ea019c4a6f835945a4add13d8d5cf18d276249; preview SHA9e344ee367774454e16e5cc37a9ffd2487de1f3fbf7f83bdeb6a0aec11d5b4d3; kit SHAbc3c0e83e840c8fd18b84a6783a1b3d8638ef87d798ed97d5a27f34ce88d3a9a. Old transaction/release files retained. Update requires accepted3D1.

Next USER check: NVO.esm+NVOFlightPilot.esp active, prepared save,wait3s,bat NVOFlightKit3E supplies the canonical three guns and100 standard rounds each. Roughly100m unobstructed scenery/same successful3D1 distance: one10mm,one.357,one.44 outsideVATS. Reload once,wait3s,one.44 VATS shot at a distant live enemy with clear line of fire. Exit/report; archive/read game-root NVOCombatCore.log directly before another launch. Need all three exact selections corroborated by actual creation/ammo, edited free-flight matches, clean reload and linked final actor hit. VATS context is user-reported. No repeat of accepted3D1 weapons needed; gameplay acceptance pending. Ask before next packet.

Special-ammo direction retained: exact loaded round supplies cartridge variant; weapon supplies barrel/launch conditions. Explicitly handle penetration/secondary effects through later coordinated damage ownership, avoid double vanilla/NVO modifiers; unknown combinations retain existing behaviour. Proposed future focused standard/AP/HP comparison for one weapon, not implemented here. Precise contact-energy, unit calibration and initial unchanged segment remain pilot limitations before armour/physiology authority.

'''
(PACKET/'CHECKPOINT-INSTALLED.md').write_text(checkpoint,encoding='utf-8')
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    old = p.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first,sep,rest = old.partition(b'\n');p.write_bytes(first+sep+b'\n'+checkpoint.encode()+rest)
archive = ROOT/'release/NVO-Combat-Packet-3E-Update.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(RELEASE).as_posix())
archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
(PACKET/'RELEASE.json').write_text(json.dumps(dict(archive=str(archive),sha256=archive_hash,bytes=archive.stat().st_size),indent=2)+'\n')
print(json.dumps(dict(installed=True,packet='3E',native_version=311,backup=result['backup'],
                      zip_sha256=archive_hash,zip_bytes=archive.stat().st_size,test_page=str(RELEASE/'START-HERE.html')),indent=2))
