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
PACKET = ROOT/'source/combat/step3f3'
BASE = PACKET/'baseline-313'
RELEASE = ROOT/'release/NVO-Combat-Packet-3F3-Compiled'
GAME = Path('C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
DUMPBIN = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/HostX64/x86/dumpbin.exe')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,d): p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
    assert not (PACKET/'INSTALL-3F3-result.json').exists()
    build=(PROJECT/'out'/args.build).resolve();assert build.parent==(PROJECT/'out').resolve()
    baseline=json.loads((BASE/'manifest.json').read_text())
    for r in baseline['files']:assert sha(BASE/r['path'])==r['sha256']
    unchanged=[]
    for r in baseline['files']:
        if r['path'] not in ('src/FlightPreview.cpp','src/Plugin.cpp','CMakeLists.txt'):
            assert sha(PROJECT/r['path'])==r['sha256'],r['path'];unchanged.append(r['path'])
    assert len(unchanged)==17
    old=(BASE/'src/FlightPreview.cpp').read_text();new=(PROJECT/'src/FlightPreview.cpp').read_text()
    assert old[old.index('bool SnapshotOf('):old.index('void Skip(')] == new[new.index('bool SnapshotOf('):new.index('RangeObservation ReadRange(')]
    for start,end in [('nvo::observer::FormResult* nvo::flight::SelectProjectile','void nvo::flight::EmitNotice'),('const char* LoadConfig','bool SnapshotOf')]:
        assert old[old.index(start):old.index(end)]==new[new.index(start):new.index(end)]
    helper=new[new.index('RangeObservation ReadRange('):new.index('void Skip(')]
    assert not re.search(r'\b(?:WriteBytes|WriteVector|VirtualProtect|RunScriptLine|memcpy)\s*\(',helper)
    assert all(f'ReadAt(projectile, {o}' in helper for o in ('0xD4','0xC8','0x90'))
    assert 'ReadAt(projectile, 0x14C' not in new
    bounds=[]
    for fmt in re.findall(r'nvo::log::Write\("(FLIGHT_RANGE[^"\n]*)"',new):
        # Positive floats are bounded by snapshot/read validation; even a ratio
        # against the smallest positive float fits the conservative 24 characters.
        maximum=re.sub(r'%(?:llu|08X|u|s|\.9g)',lambda m:{'%llu':'9'*20,'%08X':'F'*8,'%u':'9'*10,'%s':'x'*32,'%.9g':'x'*24}[m.group()],fmt)
        assert '%' not in maximum and len(maximum)<=766,(len(maximum),fmt)
        bounds.append(dict(row=fmt.split()[0],maximum_bytes=len(maximum)))
    assert len(bounds)==2
    (PACKET/'SOURCE-DIFF.txt').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='baseline-313/FlightPreview.cpp',tofile='native-314/FlightPreview.cpp')))
    scope=vars(pe_inspector).copy()
    exec(inspect.getsource(pe_inspector.inspect_pair).replace('0.3.4 | phase=3B3A','0.3.14 | phase=3F3'),scope)
    evidence=scope['inspect_pair'](build)
    for name in ('FlightPhysics','FlightPreview','Plugin'):
        data=subprocess.run([str(DUMPBIN),'/disasm',str(build/(name+'.obj'))],capture_output=True,check=True).stdout
        (build/(name+'-disassembly.txt')).write_bytes(data)
    dis=(build/'FlightPhysics-disassembly.txt').read_text()
    prior=(ROOT/'release/NVO-Combat-Packet-3F2-Compiled/build-evidence/FlightPhysics-disassembly.txt').read_text()
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
    assert 'mov         dword ptr [eax+8],13Ah' in (build/'Plugin-disassembly.txt').read_text()
    evidence.update(packet='3F3',plugin_version=314,unchanged_sources=unchanged,compiled_bridges_unchanged=bridges,
        log_format_bounds=bounds,new_hooks=0,range_reads_optional=True,range_offset='D4',range_or_flight_rules_changed=False,damage_replacement=False,gameplay_tested=False)
    js(PACKET/'STATIC-CHECKS.json',evidence);js(build/'static-evidence.json',evidence)
    previous=json.loads((ROOT/'source/combat/step3f2/INSTALL-3F2-plan.json').read_text())
    installed=json.loads((ROOT/'source/combat/step3f2/INSTALL-3F2-result.json').read_text(encoding='utf-8-sig'));assert installed['status']=='installed'
    dependencies={r['path']:r['sha256'] for r in previous['dependency_preconditions']}
    dependencies.update({r['path']:r['sha256'] for r in installed['installed']})
    for path,expected in dependencies.items():assert sha(GAME/path)==expected,path
    plan=dict(previous,packet='3F3',version=314,files=[],dependency_preconditions=[dict(path=p,sha256=h) for p,h in dependencies.items()])
    for name in ('NVOCombatCore.dll','NVOCombatCore.pdb'):
        rel='Data/NVSE/Plugins/'+name;target=RELEASE/rel;copy(build/name,target)
        plan['files'].append(dict(path=rel,action='install',sha256=sha(GAME/rel),source=str(target),source_sha256=sha(target),log_may_change_until_game_exits=False))
    js(PACKET/'INSTALL-3F3-plan.json',plan);pin=sha(PACKET/'INSTALL-3F3-plan.json')
    installer=(ROOT/'tools/install_combat_3f2.ps1').read_text().replace('3F2','3F3').replace('step3f2','step3f3').replace('version -ne 313','version -ne 314').replace('version=313','version=314')
    installer=installer.replace('820d8bd88a16488557dd437db4dac712f6782a6062f5e03dc68e97a48f10ee9c',pin)
    assert pin in installer and '3F2' not in installer and '313' not in installer
    (ROOT/'tools/install_combat_3f3.ps1').write_text(installer,encoding='utf-8')
    manifest=dict(packet='3F3',version='0.3.14',plugin_version=314,status='Compiled; user diagnostic checkpoint pending',
        requires_existing_packet='3F2',build_output=str(build.relative_to(PROJECT)),native_rebuilt=True,
        installed_files=[dict(path=r['path'],sha256=r['source_sha256']) for r in plan['files']],installer_plan_sha256=pin,
        new_dependencies=[],new_native_hooks=0,record_changes=0,configuration_changes=0,range_or_flight_rules_changed=False,
        max_extra_detail_rows_per_load=96,damage_replacement=False,gameplay_tested=False,installed_by_assistant=False)
    report=f"# Native 314 / Packet 3F3 build\n\nMSVC Win32 {build.name}; zero warnings/errors. Matching PE32 DLL/PDB; two expected NVSE exports; all nine physics bridges unchanged. Range telemetry only; no new hook or flight/damage rule change. Gameplay acceptance pending.\n\nDLL SHA256 {evidence['dll_sha256']}\n\nPDB SHA256 {evidence['pdb_sha256']}\n"
    (PROJECT/'BUILD-RESULT.md').write_text(report)
    for name in ('README.md','START-HERE.html'):copy(PACKET/name,PROJECT/name);copy(PACKET/name,RELEASE/name)
    js(PROJECT/'manifest.json',manifest);js(RELEASE/'manifest.json',manifest)
    for name in ('IMPLEMENTATION.md','ENGINE-FINDINGS.json','STATIC-CHECKS.json','SOURCE-DIFF.txt','INSTALL-3F3-plan.json'):
        copy(PACKET/name,RELEASE/'Installation'/name)
    for p in BASE.rglob('*'):
        if p.is_file():copy(p,RELEASE/'Source/baseline-313'/p.relative_to(BASE))
    source_names=('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','manifest.json','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md')
    sources=[PROJECT/n for n in source_names]
    for folder in ('include','src','config','reference'):sources.extend(p for p in (PROJECT/folder).glob('*') if p.is_file())
    for p in sources:copy(p,RELEASE/'Source/NVOCombatCore'/p.relative_to(PROJECT))
    for name in ('BUILD-RESULT.md','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md'):copy(PROJECT/name,RELEASE/name)
    for name in ('build.log','toolchain.log','dll-details.txt','static-evidence.json','FlightPhysics-disassembly.txt','FlightPreview-disassembly.txt','Plugin-disassembly.txt'):copy(build/name,RELEASE/'build-evidence'/name)
    for name in ('package_combat_3f3.py','package_combat_3b3a.py','install_combat_3f3.ps1','audit_flight_capture.py'):copy(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
    copy(ROOT/'tools/install_combat_3f3.ps1',RELEASE/'Installation/install_combat_3f3.ps1')
    print(json.dumps(dict(version=314,build=build.name,unchanged_bridges=9,log_bounds=bounds,plan_sha256=pin,release=str(RELEASE)),indent=2))

if __name__=='__main__':main()
