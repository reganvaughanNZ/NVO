"""Inspect and package build311. No DLL execution or game writes."""
from pathlib import Path
import argparse, hashlib, inspect, json, re, shutil, subprocess, zipfile
import package_combat_3b3a as previous
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3d'
GAME=Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
DUMP=Path(r'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/HostX64/x86/dumpbin.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not (PACKET/'INSTALL-3D-result.json').exists(), 'Do not overwrite installed transaction preimages'
    parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
    build=(PROJECT/'out'/args.build).resolve();assert build.parent==(PROJECT/'out').resolve()
    scope=vars(previous).copy()
    exec(inspect.getsource(previous.inspect_pair).replace('0.3.4 | phase=3B3A','0.3.11 | phase=3D'),scope)
    evidence=scope['inspect_pair'](build)
    prior=ROOT/'release/NVO-Combat-Packet-3C5-Compiled/Source/NVOCombatCore'
    unchanged=('CurrentHit.cpp','DamageEvents.cpp','FlightTiming.cpp','NativeLog.cpp')
    for name in unchanged:assert (prior/'src'/name).read_bytes()==(PROJECT/'src'/name).read_bytes(),name
    old=(prior/'src/FlightPhysics.cpp').read_text();new=(PROJECT/'src/FlightPhysics.cpp').read_text()
    bridges=re.findall(r'__declspec\(naked\) void (\w+)\(\)',old)
    for name in bridges:
        pattern=r'__declspec\(naked\) void '+name+r'\(\)\n\{.*?\n\}'
        assert re.search(pattern,old,re.S)[0]==re.search(pattern,new,re.S)[0],name
    for begin,end in [('bool Guard()','const char* ReadConfig()'),('    const double vectorError=','    t->pending=false;')]:
        a=old[old.index(begin):];a=a[:a.index(end)]
        b=new[new.index(begin):];b=b[:b.index(end)]
        assert a==b,begin
    # Same integrator stages and arithmetic; only BC/drag lookup comes from Track.
    def normalized(s):
        s=s[s.index('double Cd('):s.index('// Engine source direction:')]
        for a,b in [('unsigned profile','const Track& profile'),('unsigned dragModel','const Track& profile'),
                    ('profile ?','dragModel == 7 ?'),('gConfig.bc[profile]','profile.ballisticCoefficient'),
                    ('Cd(speed/gConfig.sound,profile)','Cd(speed/gConfig.sound,profile.dragModel)')]:s=s.replace(a,b)
        return s
    assert normalized(old)==normalized(new),'Integrator arithmetic unexpectedly changed'
    outputs=[]
    for module in ('FlightPhysics','FlightPreview','NativeObserver'):
        for option,suffix in [('/disasm','disassembly'),('/symbols','symbols')]:
            name=f'{module}-{suffix}.txt';outputs.append(name)
            (build/name).write_bytes(subprocess.run([str(DUMP),option,str(build/(module+'.obj'))],capture_output=True,check=True).stdout)
    dis=(build/'FlightPhysics-disassembly.txt').read_text()
    body=re.search(r'^\?LocalZBridge@[^\n]+:\n(.*?)(?=\n\?)',dis,re.M|re.S)[1]
    assert body.count('fxrstor')==2 and body.count('ret')==2 and 'fstp        dword ptr [esp+5Ch]' in body
    assert '[esp+58h]' not in body
    obs=(build/'NativeObserver-disassembly.txt').read_text()
    pre=re.search(r'^\?OnPreCreate@[^\n]+:\n(.*?)(?=\n\?)',obs,re.M|re.S)[1]
    assert '+20h]' in pre and 'SelectProjectile' in pre,'Native result API call offset not found'
    evidence.update(unchanged_modules=list(unchanged),unchanged_assembly_bridges=bridges,
        new_native_hook_sites=0,stock_record_overrides=0,per_lifetime_coefficients=True,
        explicit_profile_count=6,gameplay_tested=False)
    (build/'static-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    (PROJECT/'BUILD-RESULT.md').write_text(f'''# Build311 / Packet3D

Win32 MSVC build `{build.name}`: zero warnings/errors, two NVSE exports, matching DLL/PDB GUID {evidence['codeview_pdb_guid']} age{evidence['pdb_age']}.

DLL SHA256 {evidence['dll_sha256']}

PDB SHA256 {evidence['pdb_sha256']}

Static record/source/assembly/PE inspection only; no DLL execution, game launch or gameplay test. Existing physics bridges, guards and numerical tolerance retained. New per-shot selection uses ShowOff's public event; no new native hook site. Runtime selection, automatic fire and5.56 acceptance await the user.
''')
    release=ROOT/'release/NVO-Combat-Packet-3D-Compiled';release.mkdir(parents=True,exist_ok=True)
    copies={f'Data/NVSE/Plugins/{n}':build/n for n in ('NVOCombatCore.dll','NVOCombatCore.pdb')}
    copies.update({f'Data/NVSE/Plugins/{n}':PACKET/n for n in ('NVOFlightPreview.ini','NVOFlightPhysics.ini')})
    copies['Data/NVOFlightPilot.esp']=PACKET/'NVOFlightPilot.esp';copies['NVOFlightKit.txt']=PACKET/'NVOFlightKit.txt'
    for relative,source in copies.items():
        target=release/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    installed=[dict(path=relative,sha256=sha(release/relative)) for relative in copies]
    manifest=dict(packet='3D',version='0.3.11',plugin_version=311,status='Compiled; awaiting user gameplay check',
        build_output=str(build.relative_to(PROJECT)),installed_files=installed,stock_overrides=0,private_projectiles_added=4,
        old_private_records_preserved=6,damage_replacement=False,new_dependencies=[],new_native_hooks=0,
        selection_method='ShowOff:OnPreProjectileCreate, native form result',physics_scope='six explicit profiles',
        shared_record_writes=False,assistant_gameplay_tested=False,config_schema=2,baseline_segments_per_lifetime=1,
        active_physics_capacity=128,detail_lifetimes_per_capture=8)
    (PROJECT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    names=('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','manifest.json','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md')
    sources=[PROJECT/name for name in names]
    for folder in ('include','src','config','reference'):sources+=sorted(p for p in (PROJECT/folder).glob('*') if p.is_file())
    for source in sources:
        target=release/'Source/NVOCombatCore'/source.relative_to(PROJECT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    for name in ('README.md','START-HERE.html','BUILD-RESULT.md','manifest.json','THIRD-PARTY-NOTICES.md','CREDITS-BALLISTX.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt'):shutil.copyfile(PROJECT/name,release/name)
    (release/'build-evidence').mkdir(exist_ok=True)
    for name in outputs+['static-evidence.json','build.log','toolchain.log','dll-details.txt']:shutil.copyfile(build/name,release/'build-evidence'/name)
    (release/'Installation').mkdir(exist_ok=True)
    for name in ('IMPLEMENTATION.md','RECORD-AUDIT.json','SOURCE-PROVENANCE.json'):shutil.copyfile(PACKET/name,release/'Installation'/name)
    shutil.copyfile(ROOT/'tools/install_combat_3d.ps1',release/'Installation/install_combat_3d.ps1')
    oldplan=json.loads((ROOT/'source/combat/step3c5/INSTALL-3C5-plan.json').read_text())
    plan={**oldplan,'packet':'3D','version':311,'files':[],'created':'2026-09-15'}
    plan['protected_assets']=[p for p in oldplan['protected_assets'] if p not in copies]
    for relative in copies:
        p=GAME/relative;source=release/relative
        plan['files'].append(dict(path=relative,action='install',sha256=sha(p) if p.exists() else None,
            source=str(source),source_sha256=sha(source),log_may_change_until_game_exits=False))
    (PACKET/'INSTALL-3D-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    with zipfile.ZipFile(ROOT/'release/NVO-Combat-Packet-3D-Source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sources:z.write(p,'native/NVOCombatCore/'+p.relative_to(PROJECT).as_posix())
        for name in ('prepare_combat_3d.py','prepare_combat_3b2.py','inspect_plugin.py','document_combat_3d.py','package_combat_3d.py','package_combat_3b3a.py','install_combat_3d.ps1'):
            z.write(ROOT/'tools'/name,'tools/'+name)
        for name in ('RECORD-AUDIT.json','SOURCE-PROVENANCE.json','IMPLEMENTATION.md'):z.write(PACKET/name,'packet/'+name)
    print(json.dumps(dict(release=str(release),install_files=len(copies),**evidence),indent=2))
if __name__=='__main__':main()
