"""Package4E offline authoring support; verify native/game files read-only."""
import hashlib,json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STEP=ROOT/'source/combat/step4e'
RELEASE=ROOT/'release/NVO-Combat-Packet-4E-Shared-Armour-Profiles'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p,root=None):return dict(path=(p.relative_to(root).as_posix() if root else str(p)),bytes=p.stat().st_size,sha256=sha(p))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)

snapshot=json.loads((ROOT/'source/combat/step4d/Evidence/SOURCE-SNAPSHOT.json').read_text())
for r in snapshot['files']:assert sha(ROOT/'native'/r['path'])==r['sha256'],r['path']
receipt=json.loads((ROOT/'source/combat/step4d/INSTALL-result.json').read_text(encoding='utf-8-sig'))
plan=json.loads((ROOT/'source/combat/step4d/Evidence/INSTALL-plan.json').read_text())
pinned=dict(plan['protected']);pinned.update({r['path']:r['sha256'] for r in receipt['installed']})
for name,digest in pinned.items():assert sha(GAME/name)==digest,name
assert not (GAME/'Data/RD.esm').exists()
assert (STEP/'generated/NVOArmourCoverage.tsv').read_bytes()==(GAME/'Data/NVSE/Plugins/NVOArmourCoverage.tsv').read_bytes()
native_result=(STEP/'checks/out/results.txt').read_text().strip()
assert 'PASS 19 checks' in native_result
assert not re.search(r'\b(?:warning|error) [A-Z]+\d+',(STEP/'checks/out/build.log').read_text(),re.I)

for name in ['README.md','DEPENDENCIES.md','START-HERE.html']:copy(STEP/name,RELEASE/name)
for directory in ['profiles','generated']:
    for p in (STEP/directory).iterdir():
        if p.is_file():copy(p,RELEASE/directory/p.name)
for name in ['resolve_armour_profiles.py','compile_armour_coverage.py','generate_combat_4c_fixtures.py','check_armour_profile_resolution.py']:
    copy(ROOT/'tools'/name,RELEASE/'Tools'/name)
for name in ['KeywordExportCheck.cpp','RUN-CHECK.cmd','SYNTHETIC-ONLY.json','SYNTHETIC-ONLY.tsv']:
    copy(STEP/'checks'/name,RELEASE/'checks'/name)
baseline=ROOT/'source/combat/step4d/Data/NVSE/Plugins/NVOArmourCoverage.tsv'
capture=ROOT/'source/combat/step4d/Evidence/LIVE-4D-20260917-010933.log'
for name,path in [('BASELINE-4D.tsv',baseline),('REFERENCE-4D.log',capture)]:copy(path,RELEASE/'Evidence'/name)
source_names=['NVOCombatCore/include/ArmourCoverageConfig.hpp','NVOCombatCore/src/ArmourCoverageConfig.cpp','NVOCombatModel/CoverageProfiles.hpp','NVOCombatModel/CoverageProfiles.cpp']
for name in source_names:copy(ROOT/'native'/name,RELEASE/'Source'/name)

# Verify the delivered authoring tool is usable after extraction, with no workspace-relative imports.
check=subprocess.run([sys.executable,str(RELEASE/'Tools/check_armour_profile_resolution.py')],capture_output=True,text=True)
assert check.returncode==0,check.stdout+check.stderr
assert 'PASS 54 ' in check.stdout
copy(RELEASE/'Evidence/RESOLUTION-CHECKS.json',STEP/'Evidence/RESOLUTION-CHECKS.json')
(STEP/'Evidence/RESOLUTION-CHECKS.txt').write_text(check.stdout,encoding='utf-8')
for name in ['results.txt','build.log','toolchain.log']:copy(STEP/'checks/out'/name,STEP/'Evidence'/('NATIVE-'+name))
ref=Path(r'C:\Users\regan\Desktop\NVO Mod References (Open Source)\JIP-LN-NVSE-main\functions_jip\jip_fn_miscellaneous.h')
archive=Path(r'C:\Users\regan\Desktop\NVO Mod References (Open Source)\KEYWORDS-83088-1-01-1695964898 (1).7z')
verification=dict(packet='4E',status='PREPARED_OFFLINE',new_runtime_dependencies=[],runtime_version_unchanged=327,game_files_changed=False,game_launched=False,geck_required=False,playtest_required_for_identical_export=False,live_keyword_import=False,keyword_framework_installed=False,donor_implementation_copied=False,installed_files_verified=len(pinned),native_source_files_unchanged=len(snapshot['files']),rd_absent=True,shipped_runtime_file=record(STEP/'generated/NVOArmourCoverage.tsv'),installed_runtime_same_bytes=True,authoring_checks=check.stdout.strip(),native_consumer_checks=native_result,replayed_4d_rows=5,native_consumer_sources=[record(ROOT/'native'/p) for p in source_names],donor_source_read=record(ref),keyword_archive_reference=record(archive),archive_contents_reviewed=False,limitations=['NVO authoring tags only; no live JIP/KEYWORDS lookup or automatic mod discovery.','Custom fixture IDs are synthetic and not installed.','No material strength, hit-surface authority, damage or stagger implementation.','No runtime stress benchmark for expanded catalogues.'])
write(STEP/'Evidence/VERIFICATION.json',verification)
write(STEP/'Evidence/INSTALLED-BASELINE.json',dict(files=[record(GAME/name) for name in pinned],read_only=True))
for p in (STEP/'Evidence').iterdir():
    if p.is_file():copy(p,RELEASE/'Evidence'/p.name)
for link in re.findall(r'href="([^"]+)"',(RELEASE/'START-HERE.html').read_text(encoding='utf-8')):
    if not link.startswith(('http:','https:','#')):assert (RELEASE/link).is_file(),link
write(RELEASE/'MANIFEST.json',dict(packet='4E',status='PREPARED_OFFLINE_NO_INSTALL_NEEDED',runtime_unchanged=327,files=[record(p,RELEASE) for p in sorted(RELEASE.rglob('*')) if p.is_file() and p.name!='MANIFEST.json' and '__pycache__' not in p.parts]))
bundle=RELEASE.with_suffix('.zip')
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RELEASE.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:z.write(p,str(Path(RELEASE.name)/p.relative_to(RELEASE)))
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    for r in json.loads((RELEASE/'MANIFEST.json').read_text())['files']:
        assert hashlib.sha256(z.read(RELEASE.name+'/'+r['path'])).hexdigest()==r['sha256']
write(STEP/'PACKAGE.json',dict(path=str(bundle),sha256=sha(bundle),bytes=bundle.stat().st_size,status=verification['status']))
status=ROOT/'STATUS.md';old=status.read_bytes()
heading='''## Current checkpoint: Packet4E shared armour-profile authoring PREPARED

User approved4E and asked about dependencies. Delivered original NVO offline authoring resolver: reusable definitions, NVO_ selecting/metadata tags, exact plugin/local-ID bindings and explicit record exceptions. Conflicting selecting tags always reject export, even with an exception. Typo/duplicate/missing data reject before touching TSV. No live JIP/KEYWORDS import, private-container access, donor code copy, new runtime dependency, DLL build/install or GECK change. A future live framework adapter is separate work.

54 resolution/export checks and19 checks through unchanged native327 parser/classifier pass.5 pinned4D item rows preserved. Current output is byte-identical to installed4D TSV; all native source snapshot files and15 installed files verified unchanged; RD absent. No new playtest needed because runtime and exported bytes did not change. Synthetic custom IDs are offline fixtures only. All coverage/damage/stagger authority remains0.

Release: release/NVO-Combat-Packet-4E-Shared-Armour-Profiles. Source/evidence: source/combat/step4e. NEXT ask before explicit material-response definitions and target-profile boundaries in disabled preview. Do not install identical outputs or require another4D repeat. Keep actual hit surface, anatomy, layering, modifier ownership and authoritative contact-energy gates.

'''
if heading.splitlines()[0].encode() not in old:
    cut=old.index(b'\n')+1;status.write_bytes(old[:cut]+b'\n'+heading.encode()+old[cut:])
print(json.dumps(dict(packet=str(RELEASE),checks=73,native_sources_unchanged=len(snapshot['files']),installed_files_unchanged=len(pinned),new_runtime_dependencies=0,game_activity=False,zip_sha256=sha(bundle))))
