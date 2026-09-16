"""Build evidence and guarded native-pair installer; no game execution."""
from pathlib import Path
import argparse, difflib, inspect, json, re, subprocess
import package_combat_3b3a as pair
from package_combat_3h import sha, js, copy, instructions, DUMPBIN
ROOT=Path(__file__).resolve().parents[1]
NATIVE=ROOT/'native/NVOCombatCore';PACKET=ROOT/'source/combat/step3k'
RELEASE=ROOT/'release/NVO-Combat-Packet-3K-Compiled'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',required=True);args=ap.parse_args()
    assert not (PACKET/'INSTALL-3K-result.json').exists()
    build=(NATIVE/'out'/args.build).resolve();assert build.parent==NATIVE/'out'
    baseline=PACKET/'baseline-318';frozen=json.loads((baseline/'manifest.json').read_text())
    changed={'src/Plugin.cpp','src/HitTransaction.cpp','include/HitTransaction.hpp','src/FlightPreview.cpp','BUILD.cmd','CMakeLists.txt'}
    unchanged=[];diffs=[]
    for row in frozen['files']:
        old=baseline/row['path'];new=NATIVE/row['path'];assert sha(old)==row['sha256']
        if row['path'] not in changed:assert sha(new)==row['sha256'],row['path'];unchanged.append(row['path'])
        if old.read_bytes()!=new.read_bytes():
            diffs.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='native318/'+row['path'],tofile='native319/'+row['path']))
    for relative in ('src/ActorValueObserver.cpp','src/ActorValueGuards.inl','include/ActorValueObserver.hpp'):
        diffs.append('\nNEW FILE: '+relative+'\n'+(NATIVE/relative).read_text())
    (PACKET/'SOURCE-DIFF.txt').write_text(''.join(diffs))
    scope=vars(pair).copy();exec(inspect.getsource(pair.inspect_pair).replace('0.3.4 | phase=3B3A','0.3.19 | phase=3K'),scope)
    evidence=scope['inspect_pair'](build)
    for name in ('ActorValueObserver','HitTransaction','FlightPhysics','CurrentHit','Plugin'):
        raw=subprocess.run([str(DUMPBIN),'/disasm',str(build/(name+'.obj'))],capture_output=True,check=True).stdout
        (build/(name+'-disassembly.txt')).write_bytes(raw)
    old=ROOT/'release/NVO-Combat-Packet-3H-Compiled/build-evidence'
    preserved=[]
    for module,names in (
        ('FlightPhysics',re.findall(r'__declspec\(naked\) void (\w+)\(\)',(NATIVE/'src/FlightPhysics.cpp').read_text())),
        ('CurrentHit',['CopyObserver']),
        ('HitTransaction',['EntryBridge','ReturnBridge']+['Entry'+str(i) for i in range(6)])):
        before=(old/(module+'-disassembly.txt')).read_text();after=(build/(module+'-disassembly.txt')).read_text()
        for name in names:assert instructions(before,name)==instructions(after,name),name;preserved.append(module+'::'+name)
    probe=PACKET/'inspection'
    for basename,expected in (('results.txt',8),('hit-results.txt',6)):
        text=(probe/basename).read_text();assert text.count('=pass')==expected and 'game_or_plugin_dll_loaded=false' in text
    for basename in ('build.log','hit-build.log'):
        assert not re.search(r'\b(?:warning|error) [A-Z]+\d+',(probe/basename).read_text(),re.I)
    raw=subprocess.run([str(DUMPBIN),'/disasm',str(probe/'replay.obj')],capture_output=True,check=True).stdout.decode().replace('\r\n','\n')
    actual=(build/'ActorValueObserver-disassembly.txt').read_text()
    for name in ('EntryBridge','ReturnBridge'):assert instructions(raw,name)==instructions(actual,name),name
    bounds=[]
    for fmt in re.findall(r'nvo::log::Write\("(AV_APPLY[^"\n]*)"',(NATIVE/'src/ActorValueObserver.cpp').read_text()):
        maximum=re.sub(r'%(?:llu|lu|08X|u|s|\.9g)',lambda m:{'%llu':'9'*20,'%lu':'9'*10,'%08X':'F'*8,'%u':'9'*10,'%s':'x'*48,'%.9g':'x'*24}[m[0]],fmt)
        assert '%' not in maximum and len(maximum)<=766
        bounds.append(dict(row=fmt.split()[0],maximum_bytes=len(maximum)))
    assert 'Flight test kit: bat NVOFlightKit' not in (NATIVE/'src/FlightPreview.cpp').read_text()
    evidence.update(packet='3K',version=319,unchanged_sources=unchanged,preserved_compiled_bridges=preserved,
        new_bridges_match_offline_probe=True,probe_engine_reads='mocked; live read values pending user checkpoint',
        offline_checks=14,log_format_bounds=bounds,gameplay_tested=False,damage_replacement=False,
        record_changes=False,flight_changes=False)
    js(PACKET/'STATIC-CHECKS.json',evidence)
    js(PACKET/'REPLAY-RESULT.json',dict(results=(probe/'results.txt').read_text().splitlines(),
        hit_results=(probe/'hit-results.txt').read_text().splitlines(),
        sources={p.relative_to(ROOT).as_posix():sha(p) for p in [NATIVE/'src/ActorValueObserver.cpp',NATIVE/'src/ActorValueGuards.inl',NATIVE/'src/HitTransaction.cpp',probe/'replay.cpp',probe/'hit-replay.cpp']},
        actual_bridge_instruction_match=True,engine_reads_mocked=True,gameplay_tested=False))
    previous=json.loads((ROOT/'source/combat/step3h/INSTALL-3H-plan.json').read_text())
    oldpair=json.loads((ROOT/'source/combat/step3h/INSTALL-3H-result.json').read_text())
    assert oldpair['status']=='installed'
    deps={row['path']:row['sha256'] for row in previous['dependency_preconditions']}
    deps.update({row['path']:row['sha256'] for row in oldpair['installed']})
    deps['Data/NVO.esm']='fb25c3c6362c3ef0c5a3f9d67625aa433dfe8379c2bb77fc7d492800b4dc5e4d'
    for relative,h in deps.items():assert sha(GAME/relative)==h,relative
    assert not (GAME/'Data/RD.esm').exists()
    plan=dict(previous,packet='3K',version=319,created='2026-09-16',files=[],
        protected_assets=[p for p in previous['protected_assets'] if p!='Data/RD.esm'],
        dependency_preconditions=[dict(path=p,sha256=h) for p,h in deps.items()],required_absent=['Data/RD.esm'])
    for name in ('NVOCombatCore.dll','NVOCombatCore.pdb'):
        relative='Data/NVSE/Plugins/'+name;target=RELEASE/relative;copy(build/name,target)
        plan['files'].append(dict(path=relative,action='install',sha256=sha(GAME/relative),source=str(target),source_sha256=sha(target),log_may_change_until_game_exits=False))
    js(PACKET/'INSTALL-3K-plan.json',plan);pin=sha(PACKET/'INSTALL-3K-plan.json')
    installer=(ROOT/'tools/install_combat_3h.ps1').read_text().replace('3H','3K').replace('step3h','step3k').replace('version -ne 318','version -ne 319').replace('version=318','version=319')
    installer=re.sub(r"-ne '[0-9a-f]{64}'","-ne '"+pin+"'",installer,count=1)
    installer=installer.replace("'NVOFlightKit3F.txt'))", "'NVOFlightKit3F.txt', 'Data/NVO.esm'))")
    installer=installer.replace('$nvoClosed = @()',"if (Test-Path -LiteralPath (Join-Path $nvoGame 'Data\\RD.esm')) { throw 'RD.esm must remain absent.' }\n\n$nvoClosed = @()")
    (ROOT/'tools/install_combat_3k.ps1').write_text(installer)
    manifest=dict(packet='3K',version='0.3.19',plugin_version=319,status='Compiled; installation and gameplay checkpoint pending',
        installed_files=[dict(path=f['path'],sha256=f['source_sha256']) for f in plan['files']],
        native_rebuilt=True,installed_by_assistant=False,gameplay_tested=False,damage_replacement=False,
        record_changes=0,configuration_changes=0,new_dependencies=[],build_output=str(build.relative_to(NATIVE)))
    (NATIVE/'BUILD-RESULT.md').write_text(f'# Packet 3K / Native319\n\nMSVC Win32, zero warnings/errors. 14 offline checks passed with mocked engine reads. Existing bridge instructions unchanged; new bridges match the offline executable. Live damage measurements await user testing.\n\nDLL SHA256 {evidence["dll_sha256"]}\n\nPDB SHA256 {evidence["pdb_sha256"]}\n')
    for name in ('README.md','START-HERE.html'):copy(PACKET/name,NATIVE/name);copy(PACKET/name,RELEASE/name)
    js(NATIVE/'manifest.json',manifest);js(RELEASE/'manifest.json',manifest)
    for name in ('CONTRACT.md','PROVIDER-FINDINGS.json','ENGINE-GUARDS.json','STATIC-CHECKS.json','SOURCE-DIFF.txt','REPLAY-RESULT.json','INSTALL-3K-plan.json'):
        copy(PACKET/name,RELEASE/'Installation'/name)
    sources=[NATIVE/n for n in ('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','manifest.json','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md')]
    for folder in ('src','include','config','reference'):sources.extend(p for p in (NATIVE/folder).glob('*') if p.is_file())
    for p in sources:copy(p,RELEASE/'Source/NVOCombatCore'/p.relative_to(NATIVE))
    for name in ('BUILD-RESULT.md','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md'):copy(NATIVE/name,RELEASE/name)
    for name in ['build.log','toolchain.log','dll-details.txt']+[m+'-disassembly.txt' for m in ('ActorValueObserver','HitTransaction','FlightPhysics','CurrentHit','Plugin')]:
        copy(build/name,RELEASE/'build-evidence'/name)
    for name in ('replay.cpp','hit-replay.cpp','RUN.cmd','RUN-HIT.cmd','results.txt','hit-results.txt','build.log','hit-build.log'):copy(probe/name,RELEASE/'Source/probe'/name)
    for name in ('package_combat_3k.py','package_combat_3h.py','package_combat_3b3a.py','install_combat_3k.ps1','prepare_combat_3k.py','make_health_guards_3k.py','read_health_route_runtime.ps1','inspect_health_route_capture.py'):
        copy(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
    copy(ROOT/'tools/install_combat_3k.ps1',RELEASE/'Installation/install_combat_3k.ps1')
    print(json.dumps(dict(build=build.name,release=str(RELEASE),dll_sha256=evidence['dll_sha256'],offline_checks=14,plan_sha256=pin),indent=2))
if __name__=='__main__':main()
