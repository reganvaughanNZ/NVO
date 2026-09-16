"""Statically inspect/package the bounded failure diagnostics. Never load the DLL."""
from pathlib import Path
import argparse
import hashlib
import inspect
import json
import re
import shutil
import package_combat_3b3a as pe_inspector

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
PACKET=ROOT/'source/combat/step3f1'
BASE=PACKET/'baseline-311'
RELEASE=ROOT/'release/NVO-Combat-Packet-3F1-Compiled'
GAME=Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')

def main():
    assert not (PACKET/'INSTALL-3F1-result.json').exists(), 'Preserve installed preimages.'
    parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
    build=(PROJECT/'out'/args.build).resolve();assert build.parent==(PROJECT/'out').resolve()
    old=(BASE/'src/FlightPhysics.cpp').read_text();new=(PROJECT/'src/FlightPhysics.cpp').read_text()
    stripped=re.sub(r'\s*// NVO_3F1_DIAGNOSTICS_BEGIN.*?// NVO_3F1_DIAGNOSTICS_END','',new,flags=re.S)
    assert re.sub(r'\s+','',old)==re.sub(r'\s+','',stripped),'Non-diagnostic physics changed'
    helper=new[new.index('void LogDisplacementFailure'):new.index('// NVO_3F1_DIAGNOSTICS_END',new.index('void LogDisplacementFailure'))]
    assert not re.search(r'\b(?:Read|Snapshot|WriteVector|VirtualProtect|memcpy|RunScriptLine)\s*\(',helper)
    assert new.count('LogDisplacementFailure(')==2
    plugin=(PROJECT/'src/Plugin.cpp').read_text()
    normalized=plugin.replace('312; // 0.3.12, packet 3F1 bounded failure diagnostics','311; // 0.3.11, packet 3D per-shot four-weapon profiles').replace('0.3.12 | phase=3F1','0.3.11 | phase=3D')
    assert normalized==(BASE/'src/Plugin.cpp').read_text()
    assert (PROJECT/'CMakeLists.txt').read_text().replace('VERSION 0.3.12','VERSION 0.3.11')==(BASE/'CMakeLists.txt').read_text()
    unchanged=[]
    for folder in ('src','include'):
        for p in sorted((PROJECT/folder).iterdir()):
            if p.is_file() and p.name not in ('Plugin.cpp','FlightPhysics.cpp'):
                assert p.read_bytes()==(BASE/folder/p.name).read_bytes(),p
                unchanged.append(str(p.relative_to(PROJECT)))
    assert len(unchanged)==16
    formats=[]
    for f in re.findall(r'nvo::log::Write\("(PHYSICS_(?:REJECT_(?:METRICS|MOTION|POSITION|CONTEXT|DETAIL_LIMIT)|DIAGNOSTIC_(?:READY|SUMMARY))[^"\n]*)"',new):
        def maximum(m):
            return {'%llu':'9'*20,'%08X':'F'*8,'%p':'F'*8,'%u':'9'*10,'%s':'X'*32,'%.9g':'-1.23456789e+308'}[m.group()]
        text=re.sub(r'%(?:llu|08X|u|p|s|\.9g)',maximum,f)
        assert '%' not in text and len(text)<766
        formats.append(dict(record=f.split()[0],conservative_max_bytes=len(text)))
    assert len(formats)==7
    scope=vars(pe_inspector).copy()
    pair_source=inspect.getsource(pe_inspector.inspect_pair)
    assert pair_source.count('0.3.4 | phase=3B3A')==1
    exec(pair_source.replace('0.3.4 | phase=3B3A','0.3.12 | phase=3F1'),scope)
    evidence=scope['inspect_pair'](build)
    dis=(build/'FlightPhysics-disassembly.txt').read_text(encoding='utf-8-sig')
    prior_dis=(ROOT/'release/NVO-Combat-Packet-3D-Compiled/build-evidence/FlightPhysics-disassembly.txt').read_text()
    bridges=re.findall(r'__declspec\(naked\) void (\w+)\(\)',new)
    for name in bridges:
        pattern=r'^\?'+re.escape(name)+r'@[^\n]*:\n(.*?)(?=^\?|\Z)'
        before=re.search(pattern,prior_dis,re.M|re.S);after=re.search(pattern,dis,re.M|re.S)
        assert before and after,name
        code=lambda m:re.findall(r'^\s+[0-9A-F]{8}: ((?:[0-9A-F]{2} )*[0-9A-F]{2})(?:\s|$)',m[1],re.M)
        assert code(before)==code(after),('Compiled bridge changed',name)
    assert len(bridges)==8 and 'LogDisplacementFailure' in dis
    pd=(build/'Plugin-disassembly.txt').read_text(encoding='utf-8-sig')
    assert 'mov         dword ptr [eax+8],138h' in pd,'Reported version312 not present'
    evidence.update(packet='3F1',plugin_version=312,non_diagnostic_physics_tokens_unchanged=True,
                    unchanged_native_sources=unchanged,compiled_bridges_unchanged=bridges,log_format_bounds=formats,
                    maximum_failure_reports_per_session=16,rows_per_failure=4,extra_engine_memory_reads=0,
                    new_native_hooks=0,damage_replacement=False,gameplay_tested=False)
    js(build/'static-evidence.json',evidence);js(PACKET/'STATIC-CHECKS.json',evidence)
    previous=json.loads((ROOT/'source/combat/step3f/INSTALL-3F-plan.json').read_text())
    installed3f=json.loads((ROOT/'source/combat/step3f/INSTALL-3F-result.json').read_text(encoding='utf-8-sig'))
    assert installed3f['status']=='installed'
    dependencies={r['path']:r['sha256'] for r in previous['dependency_preconditions']}
    dependencies.update({r['path']:r['sha256'] for r in installed3f['installed']})
    for path,expected in dependencies.items(): assert sha(GAME/path)==expected,('Installed foundation changed',path)
    copies={f'Data/NVSE/Plugins/{name}':build/name for name in ('NVOCombatCore.dll','NVOCombatCore.pdb')}
    plan=dict(previous,packet='3F1',version=312,files=[])
    plan['dependency_preconditions']=[dict(path=p,sha256=h) for p,h in dependencies.items()]
    plan['protected_assets']=list(dict.fromkeys(previous['protected_assets']+['Data/NVOFlightPilot.esp','NVOFlightKit3F.txt']))
    for relative,source in copies.items():
        target=RELEASE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        plan['files'].append(dict(path=relative,action='install',sha256=sha(GAME/relative),source=str(target),source_sha256=sha(target),log_may_change_until_game_exits=False))
    js(PACKET/'INSTALL-3F1-plan.json',plan)
    pin=sha(PACKET/'INSTALL-3F1-plan.json')
    installer=(ROOT/'tools/install_combat_3e.ps1').read_text(encoding='utf-8-sig').replace('3E','3F1').replace('step3e','step3f1').replace('3F1-Update','3F1-Compiled')
    installer=installer.replace('version -ne 311','version -ne 312').replace('version=311','version=312')
    installer=installer.replace("@('Data/NVSE/Plugins/NVOFlightPreview.ini', 'Data/NVOFlightPilot.esp', 'NVOFlightKit3F1.txt')", "@('Data/NVSE/Plugins/NVOCombatCore.dll', 'Data/NVSE/Plugins/NVOCombatCore.pdb')")
    installer=installer.replace('Count -ne 3','Count -ne 2').replace('Exactly three unique','Exactly two unique').replace('the three named','the two named')
    anchor='$nvoPlan = Get-Content -LiteralPath $nvoPlanPath -Raw | ConvertFrom-Json'
    installer=installer.replace(anchor,f"if ((Get-FileHash -LiteralPath $nvoPlanPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne '{pin}') {{ throw 'Prepared plan changed.' }}\n"+anchor)
    match=re.search(r"if \(\$dependency.path -notin @\([^\n]+",installer)
    assert match
    allow="@("+', '.join("'"+p+"'" for p in dependencies)+")"
    installer=installer[:match.start()]+"if ($dependency.path -notin "+allow+") { throw 'Unexpected dependency precondition.' }"+installer[match.end():]
    anchor='# Validate the exact allowlist and release bytes before touching the running game.'
    installer=installer.replace(anchor,"if (@(Get-Process GECK,Vortex -ErrorAction SilentlyContinue).Count) { throw 'Close GECK and Vortex before installation.' }\n\n"+anchor)
    installer=installer.replace("if (@(Running-Game).Count) { throw 'Game relaunched before installation.' }","if (@(Get-Process FalloutNV,GECK,Vortex -ErrorAction SilentlyContinue).Count) { throw 'Game, GECK or Vortex opened before installation.' }")
    assert 'Count -ne 3' not in installer and 'NVOFlightKit3F1' not in installer and 'version=311' not in installer
    (ROOT/'tools/install_combat_3f1.ps1').write_text(installer,encoding='utf-8')
    manifest=dict(packet='3F1',version='0.3.12',plugin_version=312,status='Compiled; user diagnostic check pending',
        requires_existing_packet='3F',build_output=str(build.relative_to(PROJECT)),native_rebuilt=True,
        installed_files=[dict(path=r,sha256=sha(RELEASE/r)) for r in copies],installer_plan_sha256=pin,
        damage_replacement=False,new_native_hooks=0,record_changes=0,configuration_changes=0,
        failure_reports_per_session=16,rows_per_failure=4,routine_lifetimes=8,routine_entries=64,
        source_validation='Only bounded diagnostics and version metadata differ from311.',gameplay_tested=False)
    build_report=f'''# Build312 / Packet3F1

Win32 MSVC build `{build.name}`, zero warnings/errors. Two NVSE exports; matching DLL/PDB GUID {evidence['codeview_pdb_guid']} age{evidence['pdb_age']}. Plugin Query reports312. Eight compiled naked bridges have unchanged instruction bytes. Flight code excluding marked diagnostic additions matches311, including tolerance, guards and integrator. Other16 native source/header files unchanged.

DLL SHA256 {evidence['dll_sha256']}

PDB SHA256 {evidence['pdb_sha256']}

Compilation and static source/PE/symbol/assembly inspection only. No DLL loading, game execution or gameplay test. Underlying missed-shot discrepancy and HP persistence remain unresolved. This packet makes future displacement failures diagnosable without changing the combat rules.
'''
    (PROJECT/'BUILD-RESULT.md').write_text(build_report,encoding='utf-8')
    js(PROJECT/'manifest.json',manifest);js(RELEASE/'manifest.json',manifest)
    for name in ('README.md','START-HERE.html'):
        shutil.copyfile(PACKET/name,PROJECT/name);shutil.copyfile(PACKET/name,RELEASE/name)
    for folder in ('Installation','Source/tools','Source/baseline-311','build-evidence'):(RELEASE/folder).mkdir(parents=True,exist_ok=True)
    for name in ('IMPLEMENTATION.md','STATIC-CHECKS.json','SOURCE-CHECKS.json','BASELINE.json','INSTALL-3F1-plan.json'):
        shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
    for p in BASE.rglob('*'):
        if p.is_file():
            target=RELEASE/'Source/baseline-311'/p.relative_to(BASE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    names=('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','manifest.json','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md')
    sources=[PROJECT/n for n in names]
    for folder in ('include','src','config','reference'):sources.extend(p for p in (PROJECT/folder).glob('*') if p.is_file())
    for source in sources:
        target=RELEASE/'Source/NVOCombatCore'/source.relative_to(PROJECT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    for name in ('BUILD-RESULT.md','THIRD-PARTY-NOTICES.md','CREDITS-BALLISTX.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt'):shutil.copyfile(PROJECT/name,RELEASE/name)
    for name in ('build.log','toolchain.log','dll-details.txt','static-evidence.json','FlightPhysics-disassembly.txt','FlightPhysics-symbols.txt','Plugin-disassembly.txt'):shutil.copyfile(build/name,RELEASE/'build-evidence'/name)
    for name in ('package_combat_3f1.py','package_combat_3b3a.py','install_combat_3f1.ps1','finalize_combat_3f1.py'):
        shutil.copyfile(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
    shutil.copyfile(ROOT/'tools/install_combat_3f1.ps1',RELEASE/'Installation/install_combat_3f1.ps1')
    print(json.dumps(dict(packet='3F1',version=312,build=build.name,source_guard_passed=True,compiled_bridges_unchanged=8,dll_sha256=evidence['dll_sha256'],pdb_sha256=evidence['pdb_sha256'],plan_sha256=pin),indent=2))

if __name__=='__main__':main()
