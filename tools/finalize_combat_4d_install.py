"""Publish the verified 4D installation and user checkpoint. Never launch the game."""
import hashlib,json,shutil,zipfile,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STEP=ROOT/'source/combat/step4d'
RELEASE=ROOT/'release/NVO-Combat-Packet-4D-Armour-Identity'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
receipt=json.loads((STEP/'INSTALL-result.json').read_text(encoding='utf-8-sig'))
assert receipt['status']=='installed' and receipt['native_version']==327
for row in receipt['installed']:
    assert sha(GAME/row['path'])==row['sha256']==sha(RELEASE/row['path'])
assert not (GAME/'Data/RD.esm').exists()
backup=Path(receipt['backup'])
before=json.loads((backup/'before.json').read_text(encoding='utf-8-sig'))
for path,digest in before['protected'].items():assert sha(Path(path))==digest,path
for row in before['before']:
    if row['existed']:assert sha(backup/'originals'/row['path'])==row['sha256']
page=(STEP/'START-HERE.html').read_text(encoding='utf-8')
page=page.replace('Prepared, not installed · NVO 0.3.27 / native327.','Installed · NVO 0.3.27 / native327. Live test pending.')
page=page.replace('The packet proposes three installed files: the DLL, its matching PDB and one coverage configuration file. Installation awaits your approval. Your current native326 installation remains in place.',f'The DLL, matching PDB and coverage configuration are installed and hash-verified. {receipt["protected_files_verified"]} other files were verified unchanged, including NVO.esm, flight settings and activation lists. The game has not been launched.')
page=page.replace('After installation · four landed hits, one reload','Your test · four landed hits, one reload').replace('These instructions are ready for the next checkpoint.','The installation is ready for this checkpoint.')
page=page.replace('No installation backup exists yet.',f'Backup: <code>{backup.relative_to(ROOT)}</code> in the NVO workspace.')
page=page.replace('<a href="Evidence/INSTALL-plan.json">Proposed installation</a>','<a href="Evidence/INSTALL-result.json">Installation receipt</a>')
(STEP/'START-HERE.html').write_text(page,encoding='utf-8')
readme=(STEP/'README.md').read_text(encoding='utf-8')
readme=readme.replace('Prepared only. NVO 0.3.27 / native 327 has not been installed or playtested.','Installed with approval. NVO 0.3.27 / native327 is hash-verified; the user live checkpoint is pending. The assistant has not launched the game or run a gameplay test.')
readme=readme.replace('The proposed installation changes exactly three paths','The completed installation changed exactly three paths')
readme=readme.replace('## After installation is separately approved','## User checkpoint')
readme=readme.replace('No backup/install receipt exists yet because this release is prepared only.',f'Backup: {backup.relative_to(ROOT)}. Receipt: Evidence/INSTALL-result.json. The existing TSV was absent before installation.')
readme=readme.replace('Installed files were read only. No game launch, GECK use or live custom-armour test occurred.',f'Those preparation checks were read only. The subsequent three-file installation verified {receipt["protected_files_verified"]} other files unchanged, retained RD absence and backed up native326. Vortex was left running; no process was closed. No game launch, GECK use or live custom-armour test occurred.')
(STEP/'README.md').write_text(readme,encoding='utf-8')
for name in ['README.md','START-HERE.html']:shutil.copy2(STEP/name,RELEASE/name)
for folder in [STEP/'Evidence',RELEASE/'Evidence']:shutil.copy2(STEP/'INSTALL-result.json',folder/'INSTALL-result.json')
frozen=STEP/'Evidence/PREPARATION-MANIFEST.json'
if not frozen.exists():shutil.copy2(RELEASE/'MANIFEST.json',frozen)
shutil.copy2(frozen,RELEASE/'Evidence/PREPARATION-MANIFEST.json')
shutil.copy2(ROOT/'tools/install_combat_4d.ps1',STEP/'Evidence/INSTALLER-USED.ps1')
manifest=dict(packet='4D',prepared_only=False,status='Installed; user live test pending',native_version=327,backup=str(backup),files=[])
for p in sorted(RELEASE.rglob('*')):
    if p.is_file() and p.name!='MANIFEST.json':manifest['files'].append(dict(path=p.relative_to(RELEASE).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
write(RELEASE/'MANIFEST.json',manifest)
archive=RELEASE.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file():z.write(p,str(Path(RELEASE.name)/p.relative_to(RELEASE)))
with zipfile.ZipFile(archive) as z:
    for row in manifest['files']:assert hashlib.sha256(z.read(RELEASE.name+'/'+row['path'])).hexdigest()==row['sha256']
for link in re.findall(r'href="([^"]+)"',page):
    if not link.startswith(('http:','https:','#')):assert (RELEASE/link).is_file(),link
prior=json.loads((STEP/'PACKAGE.json').read_text())
write(STEP/'PACKAGE.json',dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,prepared_only=False,status=manifest['status'],prepared_archive_sha256=prior.get('prepared_archive_sha256',prior['sha256'])))
status=ROOT/'STATUS.md';previous=status.read_bytes()
heading=f'''## Current checkpoint: Packet 4D native327 INSTALLED; user classification test pending

User approved installation. NVO0.3.27 DLL/PDB and NVOArmourCoverage.tsv installed with verified hashes; native326 pair backed up. {receipt['protected_files_verified']} unrelated files verified unchanged, including NVSE files, NVO.esm, pilotESP, configurations and activation lists. RD absent. No game/GECK launch or process close. Vortex stayed open; deployed DLL/PDB were unlinked before copying to preserve possible source hardlinks. The earlier installer preflight stopped before any changes because Vortex was present; only the successful transaction is recorded.

Backup: {backup.relative_to(ROOT)}. Receipt: source/combat/step4d/INSTALL-result.json. Source and offline preparation evidence remain frozen. All coverage/damage/stagger authorities remain0; runtime acceptance pending.

USER CHECK: existing4B armour kit and living human test target; full body/helmet torso hit; remove helmet torso hit; unequip all torso hit; reload separately saved setup and torso hit. Four landed hits, one reload, standard9mm, no VATS/video/stress or GECK. Read game-root NVOCombatCore.log after user reports finished. Do not advance to another packet or enable damage before reviewing the result and obtaining the user's next approval. Page: release/NVO-Combat-Packet-4D-Armour-Identity/START-HERE.html.

'''
if heading.splitlines()[0].encode() not in previous:
    cut=previous.index(b'\n')+1;status.write_bytes(previous[:cut]+b'\n'+heading.encode('utf-8')+previous[cut:])
write(STEP/'DELIVERY-VERIFICATION.json',dict(installed_hashes_verified=3,protected_files_verified=len(before['protected']),backup_verified=True,archive_entries_verified=len(manifest['files']),archive_sha256=sha(archive),gameplay_tested=False))
print(json.dumps(dict(installed=3,protected=len(before['protected']),archive_entries=len(manifest['files']),page=str(RELEASE/'START-HERE.html'),backup=str(backup))))
