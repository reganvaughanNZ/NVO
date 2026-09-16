"""Static packet inspection and preparation only; never execute/load the DLL."""
from pathlib import Path
import argparse
import difflib
import hashlib
import inspect
import json
import re
import shutil
import subprocess
import package_combat_3b3a as pe_inspector

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT/'native/NVOCombatCore'
PACKET = ROOT/'source/combat/step3g2'
BASE = PACKET/'baseline-316'
RELEASE = ROOT/'release/NVO-Combat-Packet-3G2-Compiled'
GAME = Path('C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
DUMPBIN = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/HostX64/x86/dumpbin.exe')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,d): p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
    assert not (PACKET/'INSTALL-3G2-result.json').exists()
    build=(PROJECT/'out'/args.build).resolve();assert build.parent==(PROJECT/'out').resolve()
    baseline=json.loads((BASE/'manifest.json').read_text())
    for r in baseline['files']:assert sha(BASE/r['path'])==r['sha256']
    unchanged=[]
    for r in baseline['files']:
        if r['path'] not in ('src/FlightPhysics.cpp','src/FlightImpact.inl','src/NativeObserver.cpp','include/FlightPhysics.hpp','src/Plugin.cpp','CMakeLists.txt'):
            assert sha(PROJECT/r['path'])==r['sha256'],r['path'];unchanged.append(r['path'])
    assert len(unchanged)==16
    old=(BASE/'src/FlightPhysics.cpp').read_text();new=(PROJECT/'src/FlightPhysics.cpp').read_text()
    added='void nvo::physics::ObserveHit(void* p,const HitQuery& query) noexcept\n{\n    const ErrorGuard error; const Lock lock;\n    if (!gActive.load() || query.session!=gSession || !query.lifetime) return;\n    ImpactHit(Find(p,query.lifetime),query);\n}\n'
    assert new.replace(added,'')==old, 'Existing physics changed'
    observer=(PROJECT/'src/NativeObserver.cpp').read_text()
    block='        if (life) {\n            const nvo::physics::HitQuery query{gSession,gContexts,life->serial,\n                carrier.id,source.id,target.id,weapon.id,ammo,data.region,data.flags,\n                {data.position[0],data.position[1],data.position[2]}};\n            nvo::physics::ObserveHit(data.carrier,query);\n        }\n'
    assert observer.replace('#include "FlightPhysics.hpp"\n','').replace(block,'')==(BASE/'src/NativeObserver.cpp').read_text()
    header=(PROJECT/'include/FlightPhysics.hpp').read_text()
    assert re.sub(r'// Diagnostic input copied.*?void ObserveHit[^;]*;\n','',header,flags=re.S)==(BASE/'include/FlightPhysics.hpp').read_text()
    helper=(PROJECT/'src/FlightImpact.inl').read_text()
    model=(PROJECT/'src/FlightImpactModel.inl').read_text()
    join=(PROJECT/'src/FlightImpactJoin.inl').read_text()
    for text in (helper,model,join):
        assert not re.search(r'\b(?:WriteBytes|WriteVector|VirtualProtect|RunScriptLine|memcpy|Reject)\s*\(',text)
    assert 'ImpactCollision(const Track& t,const float* delta)' in helper
    assert 'ImpactEvent(const Track& t,bool destroyed)' in helper
    assert 'ImpactEnroll(const Track& t)' in helper and 'kImpactLives=32' in helper
    assert 't.logged' not in helper and 'collisionCaptured' in helper
    assert 'i<24' in model and 'Vec velocity=r.before;' in model
    assert 'm.endpointMatches && m.accountingMatches' in model
    assert 'm.offChord<=r.tolerance' in model and 'm.modelGap<=r.tolerance' in model
    replay=json.loads((PACKET/'replay/REPLAY-RESULT.json').read_text())
    for path,expected in replay['sources'].items():assert sha(ROOT/path)==expected,path
    assert sum(r.get('candidate',0) for r in replay['results'])==1
    assert replay['results'][-1]['cache_and_join_checks'] and not replay['dll_or_game_loaded']
    bounds=[]
    for fmt in re.findall(r'nvo::log::Write\("(IMPACT_[^"\n]*)"',helper+join):
        maximum=re.sub(r'%(?:llu|08X|u|d|s|\.9g)',lambda m:{'%llu':'9'*20,'%08X':'F'*8,'%u':'9'*10,'%d':'-'+'9'*10,'%s':'x'*48,'%.9g':'x'*24}[m.group()],fmt)
        assert '%' not in maximum and len(maximum)<=766,(len(maximum),fmt)
        bounds.append(dict(row=fmt.split()[0],maximum_bytes=len(maximum)))
    assert len(bounds)==14
    diffs=[]
    for r in baseline['files']:
        prior=(BASE/r['path']).read_text();current=(PROJECT/r['path']).read_text()
        if prior!=current:diffs.extend(difflib.unified_diff(prior.splitlines(True),current.splitlines(True),fromfile='native317/'+r['path'],tofile='native317/'+r['path']))
    (PACKET/'SOURCE-DIFF.txt').write_text(''.join(diffs)+'\nNEW FILE: FlightImpactJoin.inl\n'+join)
    scope=vars(pe_inspector).copy()
    exec(inspect.getsource(pe_inspector.inspect_pair).replace('0.3.4 | phase=3B3A','0.3.17 | phase=3G2'),scope)
    evidence=scope['inspect_pair'](build)
    for name in ('FlightPhysics','FlightPreview','NativeObserver','CurrentHit','Plugin'):
        data=subprocess.run([str(DUMPBIN),'/disasm',str(build/(name+'.obj'))],capture_output=True,check=True).stdout
        (build/(name+'-disassembly.txt')).write_bytes(data)
    dis=(build/'FlightPhysics-disassembly.txt').read_text()
    prior=(ROOT/'release/NVO-Combat-Packet-3G1-Compiled/build-evidence/FlightPhysics-disassembly.txt').read_text()
    physics=(PROJECT/'src/FlightPhysics.cpp').read_text()
    bridges=re.findall(r'__declspec\(naked\) void (\w+)\(\)',physics)
    def instructions(text,name):
        match=re.search(r'^\?'+re.escape(name)+r'@[^\n]*:\n(.*?)(?=^\?|\Z)',text,re.M|re.S);assert match,name
        result=[]
        for line in match[1].splitlines():
            row=re.match(r'^\s+[0-9A-F]{8}: ((?:[0-9A-F]{2} )*[0-9A-F]{2})(?:\s|$)',line)
            if row:result.append(row[1])
            elif re.fullmatch(r'\s+(?:[0-9A-F]{2} ?)+',line):result[-1]+=' '+line.strip()
        return result
    assert len(bridges)==9
    for name in bridges:assert instructions(prior,name)==instructions(dis,name),name
    old_current=subprocess.run([str(DUMPBIN),'/disasm',str(PROJECT/'out/build-30541-23708/CurrentHit.obj')],capture_output=True,check=True).stdout.decode().replace('\r\n','\n')
    assert instructions(old_current,'CopyObserver')==instructions((build/'CurrentHit-disassembly.txt').read_text(),'CopyObserver')
    assert 'mov         dword ptr [eax+8],13Dh' in (build/'Plugin-disassembly.txt').read_text()
    evidence.update(packet='3G2',plugin_version=317,unchanged_sources=unchanged,compiled_bridges_unchanged=bridges,
        log_format_bounds=bounds,new_hooks=0,impact_reads_optional=True,contact_speed_authority=False,range_or_flight_rules_changed=False,damage_replacement=False,gameplay_tested=False)
    js(PACKET/'STATIC-CHECKS.json',evidence);js(build/'static-evidence.json',evidence)
    previous=json.loads((ROOT/'source/combat/step3g1/INSTALL-3G1-plan.json').read_text())
    installed=json.loads((ROOT/'source/combat/step3g1/INSTALL-3G1-result.json').read_text(encoding='utf-8-sig'));assert installed['status']=='installed'
    dependencies={r['path']:r['sha256'] for r in previous['dependency_preconditions']}
    dependencies.update({r['path']:r['sha256'] for r in installed['installed']})
    for path,expected in dependencies.items():assert sha(GAME/path)==expected,path
    plan=dict(previous,packet='3G2',version=317,files=[],dependency_preconditions=[dict(path=p,sha256=h) for p,h in dependencies.items()])
    for name in ('NVOCombatCore.dll','NVOCombatCore.pdb'):
        rel='Data/NVSE/Plugins/'+name;target=RELEASE/rel;copy(build/name,target)
        plan['files'].append(dict(path=rel,action='install',sha256=sha(GAME/rel),source=str(target),source_sha256=sha(target),log_may_change_until_game_exits=False))
    js(PACKET/'INSTALL-3G2-plan.json',plan);pin=sha(PACKET/'INSTALL-3G2-plan.json')
    installer=(ROOT/'tools/install_combat_3g1.ps1').read_text().replace('3G1','3G2').replace('step3g1','step3g2').replace('version -ne 316','version -ne 317').replace('version=316','version=317')
    installer=re.sub(r"-ne '[0-9a-f]{64}'", "-ne '"+pin+"'", installer, count=1)
    assert pin in installer and 'version=316' not in installer
    (ROOT/'tools/install_combat_3g2.ps1').write_text(installer,encoding='utf-8')
    manifest=dict(packet='3G2',version='0.3.17',plugin_version=317,status='Compiled; user diagnostic checkpoint pending',
        requires_existing_packet='3G1',build_output=str(build.relative_to(PROJECT)),native_rebuilt=True,
        installed_files=[dict(path=r['path'],sha256=r['source_sha256']) for r in plan['files']],installer_plan_sha256=pin,
        new_dependencies=[],new_native_hooks=0,record_changes=0,configuration_changes=0,range_or_flight_rules_changed=False,
        max_extra_detail_rows_per_load=416,damage_replacement=False,gameplay_tested=False,installed_by_assistant=False)
    report=f"# Native 317 / Packet 3G2 build\n\nMSVC Win32 {build.name}; zero warnings/errors. Matching PE32 DLL/PDB; two expected NVSE exports; all nine physics bridges unchanged. Collision-step observations and non-authoritative model estimates only; no new hook or flight/damage rule change. Gameplay acceptance pending.\n\nDLL SHA256 {evidence['dll_sha256']}\n\nPDB SHA256 {evidence['pdb_sha256']}\n"
    (PROJECT/'BUILD-RESULT.md').write_text(report)
    for name in ('README.md','START-HERE.html'):copy(PACKET/name,PROJECT/name);copy(PACKET/name,RELEASE/name)
    copy(PACKET/'PRE-DAMAGE-REVIEW.md',RELEASE/'PRE-DAMAGE-REVIEW.md')
    js(PROJECT/'manifest.json',manifest);js(RELEASE/'manifest.json',manifest)
    for name in ('IMPLEMENTATION.md','ENGINE-FINDINGS.json','STATIC-CHECKS.json','SOURCE-DIFF.txt','INSTALL-3G2-plan.json'):
        copy(PACKET/name,RELEASE/'Installation'/name)
    for p in BASE.rglob('*'):
        if p.is_file():copy(p,RELEASE/'Source/baseline-316'/p.relative_to(BASE))
    source_names=('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','manifest.json','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md')
    sources=[PROJECT/n for n in source_names]
    for folder in ('include','src','config','reference'):sources.extend(p for p in (PROJECT/folder).glob('*') if p.is_file())
    for p in sources:copy(p,RELEASE/'Source/NVOCombatCore'/p.relative_to(PROJECT))
    for name in ('BUILD-RESULT.md','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md'):copy(PROJECT/name,RELEASE/name)
    for name in ('build.log','toolchain.log','dll-details.txt','static-evidence.json','FlightPhysics-disassembly.txt','FlightPreview-disassembly.txt','Plugin-disassembly.txt','CurrentHit-disassembly.txt','NativeObserver-disassembly.txt'):copy(build/name,RELEASE/'build-evidence'/name)
    for name in ('package_combat_3g2.py','package_combat_3b3a.py','install_combat_3g2.ps1','audit_flight_capture.py','replay_impact_3g1.py'):copy(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
    for name in ('REPLAY-RESULT.json','results.jsonl','replay.cpp','build.log','RUN.cmd'):
        copy(PACKET/'replay'/name,RELEASE/'build-evidence/replay'/name)
    copy(ROOT/'tools/install_combat_3g2.ps1',RELEASE/'Installation/install_combat_3g2.ps1')
    print(json.dumps(dict(version=317,build=build.name,unchanged_bridges=9,log_bounds=bounds,plan_sha256=pin,release=str(RELEASE)),indent=2))

if __name__=='__main__':main()
