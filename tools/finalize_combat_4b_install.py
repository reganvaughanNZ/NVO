"""Publish the install receipt and user checkpoint without rebuilding native code."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'source/combat/step4b'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4B-Guarded-Armour-Snapshot'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path, value): path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

receipt = json.loads((STEP / 'INSTALL-4B-result.json').read_text(encoding='utf-8-sig'))
assert receipt['status'] == 'installed' and receipt['version'] == 326
for row in receipt['installed']:
    assert sha(GAME / row['path']) == row['sha256'] == sha(RELEASE / row['path'])
assert not (GAME / 'Data/RD.esm').exists()

# Keep the prepared source snapshot and offline evidence historical and intact.
manifest = json.loads((STEP / 'manifest.json').read_text())
manifest.update(status='Installed; first live armour-reader checkpoint pending', installed_by_assistant=True,
                installed_files=receipt['installed'], installation_backup=receipt['backup'],
                protected_files_verified=receipt['protected_files_verified'],
                console_helpers='Two manually invoked test BAT text files. No automatic loader.', gameplay_tested=False)
write_json(STEP / 'manifest.json', manifest)
readme = (STEP / 'README.md').read_text(encoding='utf-8')
readme = readme.replace('- No game, GECK, ESM, ESP, INI, save, or installed DLL was changed.', '- Preparation made no game changes. Installation is recorded separately below.')
readme = readme.replace('The compiled packet is prepared but not installed. Installation and the short live checkpoint require a separate approval.', '''## Installed checkpoint

User approved installation. Native326 / NVO0.3.26 DLL and PDB are installed and hash verified, along with two optional console BAT text helpers. The installer verified53 protected files, including NVO.esm, the pilot ESP, configurations and activation lists. RD.esm remains absent. No process needed closing and the game was not launched.

Open START-HERE.html for the six-hit, one-reload test, copy buttons and reversal instructions. Runtime acceptance is pending; damage remains disabled. Helpers change test inventory/condition/health only when manually invoked by the user and are separate from the read-only native reader.

The original Source/NVOCombatCore snapshot and OFFLINE-CHECKS.json retain their preparation-time status deliberately. The top-level manifest and INSTALL-4B-result.json record the installed state.''')
(STEP / 'README.md').write_text(readme, encoding='utf-8')
(STEP / 'TEST-KIT-PROVENANCE.md').write_text('''# 4B test helper provenance

Forms read directly from installed FalloutNV.esm: Combat Armor00020420 (base health400, BMDT04); Combat Helmet00020426 (base health50, BMDT00000602); 9mm Pistol000E3778; standard9mm0008ED03; normal CrBloatFly0009189C. Raw rows are retained in TEST-FORMS.jsonl.

Local xNVSE source Commands_Inventory.cpp:2261-2277 verifies SetEquippedCurrentHealth takes current health followed by slot index. GameForms.h:909-920 defines body index2 and hair index1 (occupied by this helmet). Helpers use those indices and explicitly selected target context. Gameplay execution remains for the user; no success is inferred from generating these files.
''', encoding='utf-8')
shutil.copy2(STEP / 'USER-TEST.html', STEP / 'START-HERE.html')
for name in ['START-HERE.html','README.md','manifest.json','INSTALL-4B-plan.json','INSTALL-4B-result.json','TEST-KIT-PROVENANCE.md','TEST-FORMS.jsonl']:
    shutil.copy2(STEP / name, RELEASE / name)
snapshot = dict(packet='4B', prepared_not_installed=False, status='Installed; runtime test pending', files=[])
for path in sorted(RELEASE.rglob('*')):
    if path.is_file() and path.name != 'PACKAGE-SNAPSHOT.json':
        snapshot['files'].append(dict(path=path.relative_to(RELEASE).as_posix(), bytes=path.stat().st_size, sha256=sha(path)))
write_json(RELEASE / 'PACKAGE-SNAPSHOT.json', snapshot)
write_json(STEP / 'PACKAGE-SNAPSHOT.json', snapshot)
archive = Path(shutil.make_archive(str(RELEASE), 'zip', RELEASE.parent, RELEASE.name))
with zipfile.ZipFile(archive) as bundle:
    for row in snapshot['files']:
        assert hashlib.sha256(bundle.read(RELEASE.name + '/' + row['path'])).hexdigest() == row['sha256']
status = ROOT / 'STATUS.md'
heading = '''## Current checkpoint: Packet 4B native326 INSTALLED; live armour-reader checkpoint pending

User approved installation. NVO0.3.26 / native326 records bounded raw worn-ARMO snapshots at the existing exact CopyHitData scope. No new hooks; no model linkage, armour preview or damage authority. Character targets only; creatures skip the humanoid sample budget. Equip masks are not coverage, and no worn armour is not verified bare. All authorities remain HOLD.

Final offline reader452 checks passed; audited x86 DLL/PDB identities retained. Installed DLL/PDB plus manually invoked NVOArmourKit4B.txt and NVOArmourTarget4B.txt.53 protected files verified unchanged; RD.esm absent; no process closed or launched. Backup: backups/combat-install-4B-20260916-224741-c418db52. Receipt source/combat/step4b/INSTALL-4B-result.json. Source and preparation evidence remain frozen.

USER CHECK: living human, full Combat Armor+Helmet; torso hit; body condition200/400 then torso hit; remove helmet then head hit; unequip all then torso hit; one bloatfly hit; reload setup save then torso hit. Six landed hits, one reload, standard9mm, no VATS/video/stress. Read game-root NVOCombatCore.log after finished. Runtime performance/stress and all-actor consistency remain pending. Do not advance to4C or damage without review and user's next approval.

'''
old = status.read_bytes()
if heading.encode('utf-8') not in old:
    # Preserve mixed legacy encodings and line endings in the historical log.
    cut = old.index(b'\n') + 1
    status.write_bytes(old[:cut] + b'\n' + heading.encode('utf-8') + old[cut:])
write_json(STEP / 'DELIVERY-VERIFICATION.json', dict(installed_files_verified=len(receipt['installed']),
    zip_entries_verified=len(snapshot['files']), archive_sha256=sha(archive), gameplay_tested=False))
print(json.dumps(dict(installed_files_verified=4, protected_files_verified=receipt['protected_files_verified'],
    package_entries_verified=len(snapshot['files']), archive_sha256=sha(archive), page=str(RELEASE / 'START-HERE.html'))))
