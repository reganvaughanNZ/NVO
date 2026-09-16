"""Verify the completed two-file transaction and record the next user checkpoint."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3d1'
RELEASE = ROOT / 'release/NVO-Combat-Packet-3D1-Update'
GAME = Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
result = json.loads((PACKET / 'INSTALL-3D1-result.json').read_text(encoding='utf-8-sig'))
manifest = json.loads((RELEASE / 'manifest.json').read_text())
assert result['status'] == 'installed' and result['packet'] == '3D1' and result['version'] == 311
assert result['replaced'] == 2 and len(result['installed']) == 2
assert {r['path']: r['sha256'] for r in result['installed']} == {r['path']: r['sha256'] for r in manifest['installed_files']}
for row in result['installed']:
    assert hashlib.sha256((GAME / row['path']).read_bytes()).hexdigest() == row['sha256']
assert not result['game_relaunched'] and not result['gameplay_tested']
process_note = ('New Vegas was already closed.' if not result['closed_processes']
                else 'The installer closed the verified New Vegas process under the existing permission.')
receipt = f'''# Packet 3D1 installed - records/configuration update for build 311

Installed the two approved files and verified their hashes. {result['protected_files_verified']} protected entries, including the native DLL/PDB, NVO.esm, other extenders, physics configuration, existing kit and activation files, verified unchanged. {process_note} No assistant game launch, gameplay or GECK work.

Backup: `{result['backup']}`

Replaced files:

- `Data/NVOFlightPilot.esp` - SHA256 `0cb272358e7d7a8cd73eee8e4e5f2ab670ba5933bf5652e2351b972545415e74`
- `Data/NVSE/Plugins/NVOFlightPreview.ini` - SHA256 `fb1e590397deeb074d84286fd99a1232e5566a93ec2f75975e79cc0c4cff81a7`

To reverse this update, close the game and restore **both** files from this backup's `originals` directory into their matching paths below the game root. This returns to packet 3D, including its known SMG mapping error. No new game files were added. Keep the existing DLL and physics INI. The backup also contains logs and original hashes.

The DLL remains build311 / 0.3.11 and its log header still says phase3D. Verify this update by its file hashes and the SMG profile source `0017A2C6`; do not expect a new plugin version. Native code was not recompiled. All18 current native source/header files match the 3D release snapshot.

The source audit confirms four weapon-to-projectile mappings and all four private clone contracts. Only private PROJ01000808 changed; all ten other parsed records, including TES4, remain unchanged. One configuration value changed, plus the packet comment. Damage replacement is disabled.

Follow START-HERE.html: regular SMG short burst and one shot from each rifle at a farther unobstructed solid target, then one reload and a distant live-target Service Rifle VATS shot. The pistol result remains accepted. Gameplay acceptance of this correction is pending.

INSTALL-3D1-plan.json and INSTALL-3D1-result.json are immutable transaction records. The archived installer script is for audit; the executed copy is in the workspace tools directory.
'''
(PACKET / 'INSTALL-3D1.md').write_text(receipt, encoding='utf-8')
for name in ('INSTALL-3D1.md', 'INSTALL-3D1-plan.json', 'INSTALL-3D1-result.json'):
    shutil.copyfile(PACKET / name, RELEASE / 'Installation' / name)
manifest['status'] = 'Installed; user gameplay check pending'
manifest['installation_receipt'] = 'Installation/INSTALL-3D1.md'
(RELEASE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
shutil.copyfile(Path(__file__), RELEASE / 'Source/tools/finalize_combat_3d1.py')
checkpoint = f'''## Current combat checkpoint: 3D1 / native311 installed; corrected SMG and rifle follow-up pending

2026-09-15: user approved preparation and installation of the correction following the 3D review. Installed only preview INI and pilot ESP; no native rebuild. Four stock weapon DNAM-to-source mappings independently audited; engine source identity separated from donor cartridge key. SMG now matches actual FalloutNV.esm:17A2C6 while retaining standard9mm donor row08F20F tuning. Private PROJ01000808 regenerated from17A2C6, preserving actual model/other fields except private names and existing physical-flight flags/gravity/speed changes. All other10 parsed records and every other config value preserved. Full source/mapping/clone evidence: source/combat/step3d1/RECORD-AUDIT.json and IMPLEMENTATION.md. Old3D preparer/release retained for history; use3D1 tool for correction, do not rerun3D.

Native DLL remains311 /0.3.11, log phase3D expected; source_projectile0017A2C6 in SMG profile distinguishes update. Native18 source/header files identical to3D release; no C++/assembly or hook/tolerance changes. ESP SHA0cb272358e7d7a8cd73eee8e4e5f2ab670ba5933bf5652e2351b972545415e74; preview SHAfb1e590397deeb074d84286fd99a1232e5566a93ec2f75975e79cc0c4cff81a7. Two files replaced;{result['protected_files_verified']} protected entries unchanged. Backup {result['backup']}. {process_note} No assistant gameplay or GECK work. Receipt source/combat/step3d1/INSTALL-3D1.md. Update release release/NVO-Combat-Packet-3D1-Update/START-HERE.html. NVO.esm+NVOFlightPilot.esp remain active; existing bat NVOFlightKit unchanged. Damage replacement0.

Next USER check: prepared save, wait3s; regular weapons with standard ammo. About4x farther than prior scenery target (~100m if practical) with clear line of fire: short~3-roundSMG burst, one Hunting Rifle, one Service Rifle, outsideVATS. Reload once, wait3s, one Service Rifle VATS shot at distant live enemy with clear shot; report if no suitable target. Exit/report, assistant archives game-root NVOCombatCore.log before another launch. Need corrected SMG selections corroborated by create/ammo, edited free-flight matches, clean automatic lifetimes, reload and live-actor evidence. Do not infer VATS mode from log alone. Pistol pass and older310 private-rifle regression retained. Ask before a subsequent packet after reviewing results. No broader weapon/damage authority acceptance yet.

'''
(PACKET / 'CHECKPOINT-INSTALLED.md').write_text(checkpoint, encoding='utf-8')
for path in (ROOT / 'STATUS.md', ROOT / 'source/combat/README.md'):
    old = path.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first, sep, rest = old.partition(b'\n')
        path.write_bytes(first + sep + b'\n' + checkpoint.encode() + rest)
archive = ROOT / 'release/NVO-Combat-Packet-3D1-Update.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for path in sorted(RELEASE.rglob('*')):
        if path.is_file():
            z.write(path, path.relative_to(RELEASE).as_posix())
archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
(PACKET / 'RELEASE.json').write_text(json.dumps(dict(archive=str(archive), sha256=archive_hash,
                                                    bytes=archive.stat().st_size), indent=2) + '\n')
print(json.dumps(dict(installed=True, packet='3D1', native_version=311, backup=result['backup'],
                      zip_sha256=archive_hash, zip_bytes=archive.stat().st_size,
                      test_page=str(RELEASE / 'START-HERE.html')), indent=2))
