"""Assemble the approved 4D packet. Read-only against the game installation."""
import hashlib, json, re, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path
import package_combat_3b2 as pe_reader

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'native/NVOCombatCore'
MODEL=ROOT/'native/NVOCombatModel'
BUILD=CORE/'out/build-12967-23444'
STEP=ROOT/'source/combat/step4d'
EVIDENCE=STEP/'Evidence'
RELEASE=ROOT/'release/NVO-Combat-Packet-4D-Armour-Identity'
OLD=ROOT/'release/NVO-Combat-Packet-4B-Guarded-Armour-Snapshot/Source/NVOCombatCore'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
REFS=Path(r'C:\Users\regan\Desktop\NVO Mod References (Open Source)\NVSE-master (1)\NVSE-master\nvse\nvse')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p,root=None):return dict(path=str(p.relative_to(root) if root else p),bytes=p.stat().st_size,sha256=sha(p))
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def files(root):
    return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file() and not any(x.startswith('out') or x=='__pycache__' for x in p.relative_to(root).parts)}
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)

def main():
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    # Reuse the existing byte-level PE/export/PDB inspector with this build banner.
    text=Path(pe_reader.__file__).read_text()
    begin=text.index('def inspect_pair(');end=text.index('\n\ndef main():',begin)
    function=text[begin:end].replace('0.3.2 | phase=3B2','0.3.27 | phase=4D')
    scope=vars(pe_reader).copy();exec(function,scope);binary=scope['inspect_pair'](BUILD)
    details=(BUILD/'dll-details.txt').read_text(errors='replace')
    imports=re.findall(r'^\s{4}([^\s]+\.dll)\s*$',details,re.I|re.M)
    assert [x.lower() for x in imports]==['kernel32.dll'],imports
    binary['imports']=imports
    write(EVIDENCE/'BINARY-IDENTITY.json',binary)
    old,current=files(OLD),files(CORE)
    diff=[]
    for name in sorted(set(old)|set(current)):
        status='added' if name not in old else 'removed' if name not in current else 'unchanged' if sha(old[name])==sha(current[name]) else 'changed'
        diff.append(dict(path=name,status=status,old_sha256=sha(old[name]) if name in old else None,new_sha256=sha(current[name]) if name in current else None))
    assert {r['path'] for r in diff if r['status']=='changed'}=={'BUILD.cmd','CMakeLists.txt','src/Plugin.cpp','src/ArmourSnapshot.cpp'}
    assert not any(r['status']=='removed' for r in diff)
    expected_added={f'{folder}/{name}.{ext}' for folder,ext in [('include','hpp'),('src','cpp')] for name in ['ArmourOrigin','ArmourCoverageConfig','ArmourCoverage']}
    expected_added|={'tests/ArmourCoverageTests.cpp','tests/ArmourCoverageIntegrationTests.cpp','tests/RUN-ARMOUR-COVERAGE-CHECKS.cmd','tests/RUN-ARMOUR-COVERAGE-INTEGRATION.cmd'}
    assert {r['path'] for r in diff if r['status']=='added'}==expected_added
    old_armour=(OLD/'src/ArmourSnapshot.cpp').read_text()
    new_armour=(CORE/'src/ArmourSnapshot.cpp').read_text()
    for line in ['#include "ArmourCoverage.hpp"\n','        nvo::armour::coverage_log::Begin(session);\n','    nvo::armour::coverage_log::Suspend(reason);\n','    nvo::armour::coverage_log::Observe(permit.session, permit.ordinal, scope.id, snapshot);\n']:
        assert new_armour.count(line)==1;new_armour=new_armour.replace(line,'')
    assert old_armour==new_armour,'Existing snapshot logic changed beyond four diagnostic integration lines'
    write(EVIDENCE/'SOURCE-DIFF.json',dict(baseline=str(OLD),current=str(CORE),changes=diff,existing_snapshot_logic_verified=True))
    frozen=ROOT/'release/NVO-Combat-Packet-4C-Coverage-Profiles'
    write(EVIDENCE/'SOURCE-SNAPSHOT.json',dict(roots=[str(CORE),str(MODEL)],files=[record(p,ROOT/'native') for root in (CORE,MODEL) for p in files(root).values()]))
    checks={
        'origin_config_prepared':(CORE/'tests/out/coverage-results.txt','PASS 83 checks'),
        'production_integration':(CORE/'tests/out/coverage-integration-results.txt','production-integration fixture checks'),
        'pure_classifier_and_recorded_replay':(MODEL/'out-coverage/results.txt','PASS 53 checks; 76 captured snapshots; 10000 deterministic repetitions'),
    }
    results={}
    for key,(path,expected) in checks.items():
        text=path.read_text();assert expected in text and 'FAIL' not in text
        results[key]=dict(result=text.strip().splitlines()[-1],source=record(path))
        copy(path,EVIDENCE/(key+'-results.txt'))
    # Authoring validation is rerun here; this does not execute any game code.
    import subprocess,sys
    validation=subprocess.run([sys.executable,str(ROOT/'tools/check_combat_4c_profiles.py')],capture_output=True,text=True)
    assert validation.returncode==0,validation.stdout+validation.stderr
    (EVIDENCE/'authoring-results.txt').write_text(validation.stdout,encoding='utf-8')
    results['authoring']=validation.stdout.strip()
    oldplan=json.loads((ROOT/'source/combat/step4b/stress/INSTALL-plan.json').read_text())
    protected=dict(oldplan['protected']);protected.update({r['path']:r['sha256'] for r in oldplan['files']})
    for name,digest in protected.items():assert sha(GAME/name)==digest,'Installed file changed: '+name
    assert not (GAME/'Data/RD.esm').exists()
    config_rel='Data/NVSE/Plugins/NVOArmourCoverage.tsv'
    assert not (GAME/config_rel).exists(),'Existing custom configuration needs preservation/review'
    write(EVIDENCE/'INSTALLED-BASELINE.json',dict(captured_utc=datetime.now(timezone.utc).isoformat(),packet_installed=False,files=[record(GAME/name) for name in protected],rd_absent=True,coverage_config_absent=True))
    write(EVIDENCE/'LAYOUT-PROVENANCE.json',dict(sources=[record(REFS/name) for name in ['GameData.h','GameData.cpp','GameForms.cpp']],runtime='FNV x86 standard loaded-mod table, guarded by existing validated runtime/JIP layout',offsets={'DataHandlerSlot':'0x011C3F2C','loadedModCount':'0x218','loadedMods':'0x21C','ModInfo.name':'0x20 length260','ModInfo.modIndex':'0x40C'},form_identity='GetModIndex uses FormID high byte; low24 bits local ID; FF unresolved',scope='Owning-plugin identity only. No winning-override or asset fingerprint verification.'))
    (STEP/'profiles').mkdir(exist_ok=True)
    copy(ROOT/'source/combat/step4c/profiles/armour-coverage.json',STEP/'profiles/armour-coverage.json')
    from compile_armour_coverage import compile_profiles
    compile_profiles(STEP/'profiles/armour-coverage.json',STEP/config_rel)
    for root,label in [(CORE,'NVOCombatCore'),(MODEL,'NVOCombatModel')]:
        for name,path in files(root).items():copy(path,RELEASE/'Source'/label/name)
    for name in ['README.md','CUSTOM-ARMOUR.md','TITANS-ASSESSMENT.md','START-HERE.html','custom-armour.tsv.example']:
        copy(STEP/name,RELEASE/name)
    copy(STEP/'profiles/armour-coverage.json',RELEASE/'profiles/armour-coverage.json')
    copy(STEP/config_rel,RELEASE/config_rel)
    for name in ['NVOCombatCore.dll','NVOCombatCore.pdb']:copy(BUILD/name,RELEASE/'Data/NVSE/Plugins'/name)
    for name in ['compile_armour_coverage.py','generate_combat_4c_fixtures.py','check_combat_4c_profiles.py']:copy(ROOT/'tools'/name,RELEASE/'Tools'/name)
    for name in ['build.log','dll-details.txt','toolchain.log']:copy(BUILD/name,EVIDENCE/name)
    for name in ['coverage-build.log','coverage-integration-build.log']:copy(CORE/'tests/out'/name,EVIDENCE/name)
    write(EVIDENCE/'VALIDATION.json',dict(packet='4D',state='PREPARED_NOT_INSTALLED',native_version=327,build=str(BUILD),binary=binary,checks=results,unchanged_installed_files=len(protected),existing_hook_flight_reader_sources_unchanged=True,existing_snapshot_only_four_added_lines=True,new_engine_hooks=0,damage_replacement=False,stagger_writes=False,armour_authority=False,shadow_adapter_linked=False,game_launched=False,live_custom_armour_validated=False,limits='Offline and prior recorded evidence only. Live session identity/config integration still pending. Timing under stress not measured.'))
    install_files=[]
    for name in ['Data/NVSE/Plugins/NVOCombatCore.dll','Data/NVSE/Plugins/NVOCombatCore.pdb',config_rel]:
        install_files.append(dict(path=name,source=str(RELEASE/name),sha256=sha(RELEASE/name),previous_sha256=protected.get(name)))
    write(EVIDENCE/'INSTALL-plan.json',dict(packet='4D',prepared_only=True,native_version=327,game_root=str(GAME),files=install_files,protected={k:v for k,v in protected.items() if k not in {r['path'] for r in install_files}},requires_game_closed=True,backup_required_before_install=True,esm_changes=False,rd_required=False,gameplay_damage_enabled=False))
    for path in EVIDENCE.iterdir():
        if path.is_file():copy(path,RELEASE/'Evidence'/path.name)
    write(RELEASE/'MANIFEST.json',dict(packet='4D',prepared_only=True,files=[record(p,RELEASE) for p in sorted(RELEASE.rglob('*')) if p.is_file() and p.name!='MANIFEST.json']))
    archive=RELEASE.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(RELEASE.rglob('*')):
            if p.is_file():z.write(p,str(Path(RELEASE.name)/p.relative_to(RELEASE)))
    write(STEP/'PACKAGE.json',dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,prepared_only=True))
    status=ROOT/'STATUS.md';previous=status.read_bytes()
    marker=b'## Current checkpoint: Packet 4D armour identity and coverage diagnostics PREPARED'
    if marker not in previous:
        first,rest=previous.split(b'\n',1)
        entry='''\n\n## Current checkpoint: Packet 4D armour identity and coverage diagnostics PREPARED

User approved preparation with custom armour support. Native327/NVO0.3.27 compiled; NOT installed. Exact owning-plugin/local-ID resolution uses guarded double-read loaded-mod names refreshed per session. Bounded loose NVOArmourCoverage.tsv validates once per activation and maps the existing complete raw snapshots to explicit authored extents. Unknown gear, origins, record-mask drift or malformed config hold classification. All coverage/damage/stagger authorities remain0; ShadowAdapter and ArmourModel are not linked. No new engine hooks. The existing snapshot implementation differs by exactly four integration lines, with raw reader, hook and flight sources unchanged.

83 origin/parser/prepared-catalogue checks and31 production integration-fixture checks passed;53 classifier checks,76 recorded snapshots,10,000-repeat checks and21 authoring checks passed. DLL/PDB identity/exports/imports statically verified.14 installed files still match native326 baseline; RD absent. No game/GECK activity or install. Only two provisional Combat Armor/Helmet profiles ship. Future custom gear mapping needs verified new record IDs and separate live review. No performance timing or live4D claim.

Release: release/NVO-Combat-Packet-4D-Armour-Identity; preparation/evidence: source/combat/step4d. NEXT ask before installing the three reviewed files, then user's four-hit/one-reload check. The user suggested Titans of the New West; donor assessment recorded, no code/assets installed or included. Keep one hit result coordinating future damage and stagger, and prevent overlapping donor effects.
'''
        status.write_bytes(first+entry.encode('utf-8')+rest)
    print(json.dumps(dict(prepared=str(RELEASE),archive_sha256=sha(archive),binary=binary,installed_files_verified=len(protected)),indent=2))

if __name__=='__main__':main()
