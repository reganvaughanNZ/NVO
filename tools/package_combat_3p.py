"""Package the scoped creation diagnostic. Does not run/load/install the DLL."""
from pathlib import Path
import argparse, difflib, hashlib, inspect, json, re, shutil, subprocess
import package_combat_3b3a as pair
ROOT=Path(__file__).resolve().parents[1]
NATIVE=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3p'
RELEASE=ROOT/'release/NVO-Combat-Packet-3P-Spawn-Boundary'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
ap=argparse.ArgumentParser();ap.add_argument('--build',required=True);args=ap.parse_args()
build=(NATIVE/'out'/args.build).resolve();assert build.parent==NATIVE/'out'
assert not (PACKET/'INSTALL-3P-result.json').exists()
baseline=json.loads((PACKET/'BASELINE.json').read_text())
allowed={'src/Plugin.cpp','src/NativeObserver.cpp','BUILD.cmd','CMakeLists.txt','THIRD-PARTY-NOTICES.md'}
unchanged=[];diff=[]
for name,h in baseline['native_sources'].items():
    old=PACKET/'baseline/native320'/name;new=NATIVE/name
    assert sha(old)==h
    if name.replace('\\','/') not in allowed:assert sha(new)==h,name
    if sha(new)==h:unchanged.append(name)
    elif new.suffix in ('.cpp','.hpp','.txt','.cmd','.md'):
        diff.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='native320/'+name,tofile='native321/'+name))
(PACKET/'SOURCE-DIFF.txt').write_text(''.join(diff))
for name,h in baseline['game_files'].items():assert sha(GAME/name)==h,name
assert not (GAME/'Data/RD.esm').exists()
scope=vars(pair).copy()
exec(inspect.getsource(pair.inspect_pair).replace('0.3.4 | phase=3B3A','0.3.21 | phase=3P'),scope)
evidence=scope['inspect_pair'](build)
tests=(NATIVE/'tests/out/checks.txt').read_text();assert 'PASS 19 checks' in tests
# Disassemble the FINAL binary, not the first build with earlier diagnostics.
dumpbin=Path(r'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\HostX64\x86\dumpbin.exe')
out=subprocess.run([str(dumpbin),'/disasm',str(build/'NVOCombatCore.dll')],check=True,capture_output=True).stdout.decode(errors='replace')
(PACKET/'native321-disassembly-local.txt').write_text(out)
lines=out.splitlines(); selected=[]
for start,line in enumerate(lines):
    if (line.startswith('?Forward@spawn@') or line=="`anonymous namespace'::Wrapper:"):
        end=start+1
        while end<len(lines) and (lines[end].startswith(' ') or not lines[end]):end+=1
        selected.extend(lines[start:end])
assembly='\n'.join(selected);assert '?Forward@spawn@' in assembly and "::Wrapper:" in assembly
forward=assembly.split("`anonymous namespace'::Wrapper:")[0]
assert forward.count('push ')==16 and forward.count('call ')==1 and 'add         esp,40h' in forward
(PACKET/'forwarding-assembly.txt').write_text(assembly)
evidence.update(packet='3P',native_version=321,offline_checks=19,unchanged_sources=unchanged,
    damage_replacement=False,flight_reservation_enabled=False,gameplay_tested=False,
    scope='Post-selection creation boundary diagnostic only; capacity admission still pending',
    engine_forwarding='x86 cdecl, sixteen copied 32-bit words, exactly one continuation, unchanged return; final assembly inspected',
    runtime_guard='pinned ShowOff184 metadata/full relocated handler/call branches, engine entry fingerprint, CAS ownership',
    verification_limits=['No game or DLL executed','Real call/event pairing, load transitions, nesting and other threads need runtime evidence','No performance claim','No pre-damage gate closure'])
js(PACKET/'STATIC-CHECKS.json',evidence)
prior=json.loads((ROOT/'source/combat/step3k1/INSTALL-3K1-plan.json').read_text())
deps=dict(baseline['game_files'])
deps['NVOFlightKit3F.txt']=sha(GAME/'NVOFlightKit3F.txt')
plan=dict(prior,packet='3P',version=321,files=[],dependency_preconditions=[dict(path=p,sha256=h) for p,h in deps.items()])
for name in ('NVOCombatCore.dll','NVOCombatCore.pdb'):
    rel='Data/NVSE/Plugins/'+name;dest=RELEASE/rel;copy(build/name,dest)
    plan['files'].append(dict(path=rel,action='install',sha256=sha(GAME/rel),source=str(dest),source_sha256=sha(dest),log_may_change_until_game_exits=False))
js(PACKET/'INSTALL-3P-plan.json',plan)
installer=(ROOT/'tools/install_combat_3k1.ps1').read_text().replace('3K1','3P').replace('step3k1','step3p').replace('version -ne 320','version -ne 321').replace('version=320','version=321').replace('NVO-Combat-Packet-3P-Compiled','NVO-Combat-Packet-3P-Spawn-Boundary')
installer=re.sub(r"-ne '[0-9a-f]{64}'","-ne '"+sha(PACKET/'INSTALL-3P-plan.json')+"'",installer,count=1)
(ROOT/'tools/install_combat_3p.ps1').write_text(installer)
manifest=dict(packet='3P',version='0.3.21',plugin_version=321,status='Compiled; installation pending',installed_by_assistant=False,gameplay_tested=False,damage_replacement=False,flight_reservation_enabled=False,build_output=str(build.relative_to(NATIVE)),installed_files=[dict(path=r['path'],sha256=r['source_sha256']) for r in plan['files']])
(NATIVE/'BUILD-RESULT.md').write_text(f'# Native321 / Packet3P\n\nWin32 MSVC, zero warnings/errors, matching DLL/PDB.19 offline ABI/receipt checks passed. No game/DLL execution. Existing flight/damage code unchanged. Capacity reservation NOT enabled.\n\nDLL SHA256 {evidence["dll_sha256"]}\n\nPDB SHA256 {evidence["pdb_sha256"]}\n')
for n in ('README.md','START-HERE.html'):copy(PACKET/n,RELEASE/n);copy(PACKET/n,NATIVE/n)
js(RELEASE/'manifest.json',manifest);js(NATIVE/'manifest.json',manifest)
for n in ('STATIC-CHECKS.json','SOURCE-DIFF.txt','INSTALL-3P-plan.json','PROVIDER-INSPECTION.json'):copy(PACKET/n,RELEASE/'Installation'/n)
for n in ('BUILD-RESULT.md','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md'):copy(NATIVE/n,RELEASE/n)
for f in NATIVE.rglob('*'):
    rel=f.relative_to(NATIVE)
    if f.is_file() and 'out' not in rel.parts:copy(f,RELEASE/'Source/NVOCombatCore'/rel)
for n in ('build.log','toolchain.log','dll-details.txt'):copy(build/n,RELEASE/'build-evidence'/n)
copy(PACKET/'forwarding-assembly.txt',RELEASE/'build-evidence/forwarding-assembly.txt')
for n in ('checks.txt','build.log'):copy(NATIVE/'tests/out'/n,RELEASE/'build-evidence'/('fixture-'+n))
for n in ('package_combat_3p.py','package_combat_3b3a.py','install_combat_3p.ps1'):copy(ROOT/'tools'/n,RELEASE/'Source/tools'/n)
copy(ROOT/'tools/install_combat_3p.ps1',RELEASE/'Installation/install_combat_3p.ps1')
print(json.dumps(dict(release=str(RELEASE),dll_sha256=evidence['dll_sha256'],pdb_sha256=evidence['pdb_sha256'],offline_checks=19,plan_sha256=sha(PACKET/'INSTALL-3P-plan.json')),indent=2))
