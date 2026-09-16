"""Static inspection and package construction; never load the game or DLL."""
from pathlib import Path
import argparse,difflib,hashlib,inspect,json,re,shutil,subprocess
import package_combat_3b3a as pair
ROOT=Path(__file__).resolve().parents[1]
NATIVE=ROOT/'native/NVOCombatCore';PACKET=ROOT/'source/combat/step3h'
RELEASE=ROOT/'release/NVO-Combat-Packet-3H-Compiled'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
DUMPBIN=Path(r'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\HostX64\x86\dumpbin.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
def instructions(text,name):
    m=re.search(r'^\?'+name+r'@[^\n]*:\n(.*?)(?=^\?|\Z)',text,re.M|re.S);assert m,name
    result=[]
    for line in m[1].splitlines():
        row=re.match(r'^\s+[0-9A-F]{8}: ((?:[0-9A-F]{2} )*[0-9A-F]{2})(?:\s|$)',line)
        if row:result.append(row[1])
        elif re.fullmatch(r'\s+(?:[0-9A-F]{2} ?)+',line):result[-1]+=' '+line.strip()
    return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',required=True);args=ap.parse_args()
    assert not (PACKET/'INSTALL-3H-result.json').exists()
    build=(NATIVE/'out'/args.build).resolve();assert build.parent==NATIVE/'out'
    baseline=PACKET/'baseline-317';j=json.loads((baseline/'manifest.json').read_text())
    changed={'src/Plugin.cpp','src/NativeObserver.cpp','src/CurrentHit.cpp','src/DamageEvents.cpp','include/NativeObserver.hpp','BUILD.cmd','CMakeLists.txt'}
    diffs=[];unchanged=[]
    for f in j['files']:
        old=baseline/f['path'];new=NATIVE/f['path'];assert sha(old)==f['sha256'],f['path']
        if f['path'] not in changed:assert sha(new)==f['sha256'],f['path'];unchanged.append(f['path'])
        if old.read_bytes()!=new.read_bytes():diffs.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='native317/'+f['path'],tofile='native318/'+f['path']))
    for name in ('HitTransaction.cpp','HitTransactionGuards.inl'):
        diffs.append('\nNEW FILE: src/'+name+'\n'+(NATIVE/'src'/name).read_text())
    diffs.append('\nNEW FILE: include/HitTransaction.hpp\n'+(NATIVE/'include/HitTransaction.hpp').read_text())
    (PACKET/'SOURCE-DIFF.txt').write_text(''.join(diffs))
    scope=vars(pair).copy();exec(inspect.getsource(pair.inspect_pair).replace('0.3.4 | phase=3B3A','0.3.18 | phase=3H'),scope)
    evidence=scope['inspect_pair'](build)
    for name in ('HitTransaction','CurrentHit','FlightPhysics','NativeObserver','DamageEvents','Plugin'):
        out=subprocess.run([str(DUMPBIN),'/disasm',str(build/(name+'.obj'))],capture_output=True,check=True).stdout
        (build/(name+'-disassembly.txt')).write_bytes(out)
    physics=(NATIVE/'src/FlightPhysics.cpp').read_text()
    bridges=re.findall(r'__declspec\(naked\) void (\w+)\(\)',physics);assert len(bridges)==9
    old=(ROOT/'release/NVO-Combat-Packet-3G2-Compiled/build-evidence/FlightPhysics-disassembly.txt').read_text()
    new=(build/'FlightPhysics-disassembly.txt').read_text()
    for name in bridges:assert instructions(old,name)==instructions(new,name),name
    old=(ROOT/'release/NVO-Combat-Packet-3G2-Compiled/build-evidence/CurrentHit-disassembly.txt').read_text()
    assert instructions(old,'CopyObserver')==instructions((build/'CurrentHit-disassembly.txt').read_text(),'CopyObserver')
    replay=PACKET/'inspection';result=(replay/'results.txt').read_text()
    assert result.count('=pass')==6 and 'game_or_plugin_dll_loaded=false' in result
    assert not re.search(r'\b(?:warning|error) [A-Z]+\d+',(replay/'build.log').read_text(),re.I)
    raw=subprocess.run([str(DUMPBIN),'/disasm',str(replay/'replay.obj')],capture_output=True,check=True).stdout.decode().replace('\r\n','\n')
    asm=(build/'HitTransaction-disassembly.txt').read_text()
    for name in ['Entry'+str(i) for i in range(6)]+['EntryBridge','ReturnBridge']:
        assert instructions(raw,name)==instructions(asm,name),name
    bounds=[];src=(NATIVE/'src/HitTransaction.cpp').read_text()
    for fmt in re.findall(r'nvo::log::Write\("(HIT_TX[^"\n]*)"',src):
        maximum=re.sub(r'%(?:llu|lu|08X|02X|u|d|s|\.9g)',lambda m:{'%llu':'9'*20,'%lu':'9'*10,'%08X':'F'*8,'%02X':'F'*2,'%u':'9'*10,'%d':'-'+'9'*10,'%s':'x'*48,'%.9g':'x'*24}[m[0]],fmt)
        assert '%' not in maximum and len(maximum)<=766
        bounds.append(dict(row=fmt.split()[0],maximum_bytes=len(maximum)))
    replay_sources={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [NATIVE/'src/HitTransaction.cpp',NATIVE/'src/HitTransactionGuards.inl',NATIVE/'include/HitTransaction.hpp',replay/'replay.cpp']}
    js(PACKET/'REPLAY-RESULT.json',dict(results=result.splitlines(),sources=replay_sources,game_or_plugin_dll_loaded=False,compiled_bridges_match_dll_object=True))
    evidence.update(packet='3H',plugin_version=318,unchanged_sources=unchanged,compiled_physics_bridges_unchanged=bridges,
        copy_observer_bridge_unchanged=True,new_bridges_match_offline_probe=True,log_format_bounds=bounds,
        new_callsite_observers=6,damage_replacement=False,flight_or_record_changes=False,gameplay_tested=False)
    js(PACKET/'STATIC-CHECKS.json',evidence);js(build/'static-evidence.json',evidence)
    previous=json.loads((ROOT/'source/combat/step3g2/INSTALL-3G2-plan.json').read_text())
    installed=json.loads((ROOT/'source/combat/step3g2/INSTALL-3G2-result.json').read_text());assert installed['status']=='installed'
    deps={f['path']:f['sha256'] for f in previous['dependency_preconditions']};deps.update({f['path']:f['sha256'] for f in installed['installed']})
    for path,h in deps.items():assert sha(GAME/path)==h,path
    plan=dict(previous,packet='3H',version=318,files=[],dependency_preconditions=[dict(path=p,sha256=h) for p,h in deps.items()])
    for name in ('NVOCombatCore.dll','NVOCombatCore.pdb'):
        rel='Data/NVSE/Plugins/'+name;target=RELEASE/rel;copy(build/name,target)
        plan['files'].append(dict(path=rel,action='install',sha256=sha(GAME/rel),source=str(target),source_sha256=sha(target),log_may_change_until_game_exits=False))
    js(PACKET/'INSTALL-3H-plan.json',plan);pin=sha(PACKET/'INSTALL-3H-plan.json')
    installer=(ROOT/'tools/install_combat_3g2.ps1').read_text().replace('3G2','3H').replace('step3g2','step3h').replace('version -ne 317','version -ne 318').replace('version=317','version=318')
    installer=re.sub(r"-ne '[0-9a-f]{64}'","-ne '"+pin+"'",installer,count=1)
    assert pin in installer and 'version=317' not in installer
    (ROOT/'tools/install_combat_3h.ps1').write_text(installer)
    manifest=dict(packet='3H',version='0.3.18',plugin_version=318,status='Compiled; live diagnostic checkpoint pending',
        requires_existing_packet='3G2',build_output=str(build.relative_to(NATIVE)),native_rebuilt=True,
        installed_files=[dict(path=f['path'],sha256=f['source_sha256']) for f in plan['files']],installer_plan_sha256=pin,
        new_dependencies=[],new_callsite_observers=6,record_changes=0,configuration_changes=0,
        damage_replacement=False,gameplay_tested=False,installed_by_assistant=False)
    report=f"# Native318 / Packet3H build\n\nMSVC Win32 {build.name}; zero warnings/errors. Matching PE32 DLL/PDB and two expected exports. Nine physics bridges and the existing copy bridge unchanged. All eight new bridge/stub instruction sequences match the executable offline probe. No game or plugin DLL was loaded by that probe. Live acceptance is pending.\n\nDLL SHA256 {evidence['dll_sha256']}\n\nPDB SHA256 {evidence['pdb_sha256']}\n"
    (NATIVE/'BUILD-RESULT.md').write_text(report)
    for name in ('README.md','START-HERE.html'):copy(PACKET/name,NATIVE/name);copy(PACKET/name,RELEASE/name)
    js(NATIVE/'manifest.json',manifest);js(RELEASE/'manifest.json',manifest)
    for name in ('CONTRACT.md','IMPLEMENTATION.md','ENGINE-FINDINGS.json','STATIC-CHECKS.json','SOURCE-DIFF.txt','REPLAY-RESULT.json','INSTALL-3H-plan.json'):
        copy(PACKET/name,RELEASE/'Installation'/name)
    sources=[NATIVE/n for n in ('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','manifest.json','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md')]
    for folder in ('src','include','config','reference'):sources.extend(p for p in (NATIVE/folder).glob('*') if p.is_file())
    for p in sources:copy(p,RELEASE/'Source/NVOCombatCore'/p.relative_to(NATIVE))
    for p in baseline.rglob('*'):
        if p.is_file():copy(p,RELEASE/'Source/baseline-317'/p.relative_to(baseline))
    for name in ('BUILD-RESULT.md','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md'):copy(NATIVE/name,RELEASE/name)
    for name in ('build.log','toolchain.log','dll-details.txt','static-evidence.json','HitTransaction-disassembly.txt','CurrentHit-disassembly.txt','FlightPhysics-disassembly.txt','Plugin-disassembly.txt'):
        copy(build/name,RELEASE/'build-evidence'/name)
    for name in ('replay.cpp','RUN.cmd','results.txt','build.log'):copy(replay/name,RELEASE/'Source/probe'/name)
    for name in ('package_combat_3h.py','package_combat_3b3a.py','install_combat_3h.ps1','audit_flight_capture.py','audit_hit_transactions.py'):
        copy(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
    copy(ROOT/'tools/install_combat_3h.ps1',RELEASE/'Installation/install_combat_3h.ps1')
    print(json.dumps(dict(version=318,build=build.name,evidence=evidence,release=str(RELEASE),plan_sha256=pin),indent=2))
if __name__=='__main__':main()
