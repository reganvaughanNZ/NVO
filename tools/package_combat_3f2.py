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
PACKET=ROOT/'source/combat/step3f2'
BASE=PACKET/'baseline-312'
RELEASE=ROOT/'release/NVO-Combat-Packet-3F2-Compiled'
GAME=Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')

def main():
    assert not (PACKET/'INSTALL-3F2-result.json').exists(), 'Preserve installed preimages.'
    parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
    build=(PROJECT/'out'/args.build).resolve();assert build.parent==(PROJECT/'out').resolve()
    old=(BASE/'src/FlightPhysics.cpp').read_text();new=(PROJECT/'src/FlightPhysics.cpp').read_text()
    unchanged=[]
    for folder in ('src','include'):
        for p in sorted((PROJECT/folder).iterdir()):
            if p.is_file() and p.name not in ('Plugin.cpp','FlightPhysics.cpp'):
                assert p.read_bytes()==(BASE/folder/p.name).read_bytes(),p
                unchanged.append(str(p.relative_to(PROJECT)))
    assert len(unchanged)==16
    for start,end in [('double Cd(', 'void __cdecl BeforeMovement(')]:
        assert old[old.index(start):old.index(end)]==new[new.index(start):new.index(end)]
    tolerance='const double tolerance=0.002+coordinate*0.0000005+Length(t->expected)*0.00002;'
    assert old.count(tolerance)==1 and new.count(tolerance)==2
    assert 'const bool matched=vectorError<=tolerance && positionError<=tolerance;' in new
    helper=new[new.index('void __cdecl AfterTerrainQuery'):new.index('__declspec(naked) void TerrainBridge')]
    assert helper.index('if (result&0xFFu) return;')<helper.index('WriteTerrainHeight(height,proposed[2])')
    for contract in ('!t->wrote','!t->baselineVerified','input!=t->frame+0xC',
                     'floor!=-2048.0f','floor)-proposed[2]<=30.0','!Snapshot(*t,life,distance)',
                     'candidateError>tolerance','candidate)!=frame-0x30','height)!=frame-0x2B4'):
        assert contract in helper,contract
    assert helper.count('WriteTerrainHeight(')==1
    assert not re.search(r'\b(?:WriteVector|VirtualProtect|RunScriptLine|memcpy)\s*\(',helper)
    log=(build/'build.log').read_text();assert not re.search(r'(?:warning|error) C\d+',log)
    scope=vars(pe_inspector).copy()
    exec(inspect.getsource(pe_inspector.inspect_pair).replace('0.3.4 | phase=3B3A','0.3.13 | phase=3F2'),scope)
    evidence=scope['inspect_pair'](build)
    dis=(build/'FlightPhysics-disassembly.txt').read_text(encoding='utf-8-sig')
    prior=(ROOT/'release/NVO-Combat-Packet-3F1-Compiled/build-evidence/FlightPhysics-disassembly.txt').read_text()
    bridges=re.findall(r'__declspec\(naked\) void (\w+)\(\)',old)
    pattern=lambda name:r'^\?'+re.escape(name)+r'@[^\n]*:\n(.*?)(?=^\?|\Z)'
    def code(m):
        instructions=[]
        for line in m[1].splitlines():
            match=re.match(r'^\s+[0-9A-F]{8}: ((?:[0-9A-F]{2} )*[0-9A-F]{2})(?:\s|$)',line)
            if match: instructions.append(match[1])
            elif re.fullmatch(r'\s+(?:[0-9A-F]{2} ?)+',line):
                assert instructions
                instructions[-1]+=' '+line.strip()
        return instructions
    for name in bridges:
        before=re.search(pattern(name),prior,re.M|re.S);after=re.search(pattern(name),dis,re.M|re.S)
        assert before and after and code(before)==code(after),name
    assert len(bridges)==8 and new.count('__declspec(naked) void ')==9
    terrain=re.search(pattern('TerrainBridge'),dis,re.M|re.S)
    encoded=' '.join(code(terrain));assert encoded.count('FF 74 24 08')==2
    assert encoded.endswith('C2 08 00') and encoded.count('0F AE 04 24')==1 and encoded.count('0F AE 0C 24')==1
    for instruction in ('FF 73 1C','FF 73 2C','FF 73 28','FF 73 10','FF 73 08','83 7B 04'):
        # CMP uses the full imm32 encoding81, not83.
        if instruction=='83 7B 04': assert '81 7B 04 16 F4 9B 00' in encoded
        else: assert instruction in encoded
    assert '[?gOriginalTerrain' in terrain[1] and '?AfterTerrainQuery' in terrain[1]
    pd=(build/'Plugin-disassembly.txt').read_text(encoding='utf-8-sig')
    assert 'mov         dword ptr [eax+8],139h' in pd
    findings=json.loads((PACKET/'ENGINE-FINDINGS.json').read_text())
    for key in ('query_fnv64','default_fnv64','threshold_fnv64'):assert findings[key] in new
    # New call is on the same protected page as position commit; flush/rollback covers both.
    assert '{kTerrainSite,static_cast<unsigned>(kCommitSite+5-kTerrainSite)}' in new
    formats=[]
    for f in re.findall(r'nvo::log::Write\("(PHYSICS_TERRAIN_[^"\n]*)"',new):
        bound=re.sub(r'%(?:llu|08X|u|p|s|\.9g)',lambda m:{'%llu':'9'*20,'%08X':'F'*8,'%p':'F'*8,'%u':'9'*10,'%s':'X'*32,'%.9g':'-1.23456789e+308'}[m.group()],f)
        assert '%' not in bound and len(bound)<766
        formats.append(dict(record=f.split()[0],maximum_bytes=len(bound)))
    assert len(formats)==4
    evidence.update(packet='3F2',plugin_version=313,unchanged_native_sources=unchanged,
        compiled_existing_bridges_unchanged=bridges,new_bridge='TerrainBridge',new_native_hooks=1,
        terrain_bridge_bytes=encoded,log_format_bounds=formats,integrator_unchanged=True,
        displacement_tolerance_unchanged=True,damage_replacement=False,gameplay_tested=False)
    js(build/'static-evidence.json',evidence);js(PACKET/'STATIC-CHECKS.json',evidence)
    js(PACKET/'SOURCE-CHECKS.json',dict(baseline=312,unchanged_sources=unchanged,
        candidate_check_uses_existing_tolerance=True,successful_query_unchanged=True,baseline_unchanged=True,
        no_actor_position_write=True,only_stack_height_output_changed=True,code_bytes_not_redistributed=True))
    js(PACKET/'BASELINE.json',dict(version=312,files=[dict(path=str(p.relative_to(BASE)),sha256=sha(p)) for p in BASE.rglob('*') if p.is_file()]))
    previous=json.loads((ROOT/'source/combat/step3f1/INSTALL-3F1-plan.json').read_text())
    installed3f=json.loads((ROOT/'source/combat/step3f1/INSTALL-3F1-result.json').read_text(encoding='utf-8-sig'))
    assert installed3f['status']=='installed'
    dependencies={r['path']:r['sha256'] for r in previous['dependency_preconditions']}
    dependencies.update({r['path']:r['sha256'] for r in installed3f['installed']})
    for path,expected in dependencies.items(): assert sha(GAME/path)==expected,('Installed foundation changed',path)
    copies={f'Data/NVSE/Plugins/{name}':build/name for name in ('NVOCombatCore.dll','NVOCombatCore.pdb')}
    plan=dict(previous,packet='3F2',version=313,files=[])
    plan['dependency_preconditions']=[dict(path=p,sha256=h) for p,h in dependencies.items()]
    plan['protected_assets']=list(dict.fromkeys(previous['protected_assets']+['Data/NVOFlightPilot.esp','NVOFlightKit3F.txt']))
    for relative,source in copies.items():
        target=RELEASE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        plan['files'].append(dict(path=relative,action='install',sha256=sha(GAME/relative),source=str(target),source_sha256=sha(target),log_may_change_until_game_exits=False))
    js(PACKET/'INSTALL-3F2-plan.json',plan)
    pin=sha(PACKET/'INSTALL-3F2-plan.json')
    installer=(ROOT/'tools/install_combat_3e.ps1').read_text(encoding='utf-8-sig').replace('3E','3F2').replace('step3e','step3f2').replace('3F2-Update','3F2-Compiled')
    installer=installer.replace('version -ne 311','version -ne 313').replace('version=311','version=313')
    installer=installer.replace("@('Data/NVSE/Plugins/NVOFlightPreview.ini', 'Data/NVOFlightPilot.esp', 'NVOFlightKit3F2.txt')", "@('Data/NVSE/Plugins/NVOCombatCore.dll', 'Data/NVSE/Plugins/NVOCombatCore.pdb')")
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
    assert 'Count -ne 3' not in installer and 'NVOFlightKit3F2' not in installer and 'version=311' not in installer
    (ROOT/'tools/install_combat_3f2.ps1').write_text(installer,encoding='utf-8')
    manifest=dict(packet='3F2',version='0.3.13',plugin_version=313,status='Compiled; user diagnostic check pending',
        requires_existing_packet='3F1',build_output=str(build.relative_to(PROJECT)),native_rebuilt=True,
        installed_files=[dict(path=r,sha256=sha(RELEASE/r)) for r in copies],installer_plan_sha256=pin,
        damage_replacement=False,new_native_hooks=1,record_changes=0,configuration_changes=0,
        failure_reports_per_session=16,rows_per_failure=4,routine_lifetimes=8,routine_entries=64,
        source_validation='Failed terrain default correction with unchanged integrator, tolerance and eight existing assembly bridges.',gameplay_tested=False)
    build_report=f"""# Native313 / Packet3F2 build

MSVC Win32 build {build.name}, zero warnings/errors. Existing eight assembly bridges unchanged; one new terrain-query wrapper with original query called exactly once and original return/register/FP state preserved. Integrator and displacement tolerance unchanged. Sixteen other native source/header files unchanged. Static DLL/PDB identity verified; no DLL execution or assistant gameplay.

DLL SHA256 {evidence['dll_sha256']}
PDB SHA256 {evidence['pdb_sha256']}

Gameplay acceptance is pending. See Installation/IMPLEMENTATION.md and STATIC-CHECKS.json.
"""
    (PROJECT/'BUILD-RESULT.md').write_text(build_report,encoding='utf-8')
    js(PROJECT/'manifest.json',manifest);js(RELEASE/'manifest.json',manifest)
    for name in ('README.md','START-HERE.html'):
        shutil.copyfile(PACKET/name,PROJECT/name);shutil.copyfile(PACKET/name,RELEASE/name)
    for folder in ('Installation','Source/tools','Source/baseline-312','build-evidence'):(RELEASE/folder).mkdir(parents=True,exist_ok=True)
    for name in ('IMPLEMENTATION.md','STATIC-CHECKS.json','SOURCE-CHECKS.json','BASELINE.json','ENGINE-FINDINGS.json','INSTALL-3F2-plan.json'):
        shutil.copyfile(PACKET/name,RELEASE/'Installation'/name)
    for p in BASE.rglob('*'):
        if p.is_file():
            target=RELEASE/'Source/baseline-312'/p.relative_to(BASE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    names=('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','manifest.json','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md')
    sources=[PROJECT/n for n in names]
    for folder in ('include','src','config','reference'):sources.extend(p for p in (PROJECT/folder).glob('*') if p.is_file())
    for source in sources:
        target=RELEASE/'Source/NVOCombatCore'/source.relative_to(PROJECT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    for name in ('BUILD-RESULT.md','THIRD-PARTY-NOTICES.md','CREDITS-BALLISTX.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt'):shutil.copyfile(PROJECT/name,RELEASE/name)
    for name in ('build.log','toolchain.log','dll-details.txt','static-evidence.json','FlightPhysics-disassembly.txt','FlightPhysics-symbols.txt','Plugin-disassembly.txt'):shutil.copyfile(build/name,RELEASE/'build-evidence'/name)
    for name in ('package_combat_3f2.py','package_combat_3b3a.py','install_combat_3f2.ps1','finalize_combat_3f2.py'):
        shutil.copyfile(ROOT/'tools'/name,RELEASE/'Source/tools'/name)
    shutil.copyfile(ROOT/'tools/install_combat_3f2.ps1',RELEASE/'Installation/install_combat_3f2.ps1')
    print(json.dumps(dict(packet='3F2',version=313,build=build.name,source_guard_passed=True,compiled_existing_bridges_unchanged=8,new_bridges=1,dll_sha256=evidence['dll_sha256'],pdb_sha256=evidence['pdb_sha256'],plan_sha256=pin),indent=2))

if __name__=='__main__':main()
