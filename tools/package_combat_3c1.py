"""Package compiled 3C1, statically inspect identities, and prepare a reviewed install plan.
Does not load the DLL or alter game files.
"""
import argparse, hashlib, json, re, shutil, subprocess, zipfile
from pathlib import Path
import package_combat_3b3a as previous
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'native/NVOCombatCore'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
DUMP=Path(r'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\HostX64\x86\dumpbin.exe')
digest=previous.digest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
    build=(PROJECT/'out'/args.build).resolve();assert build.parent==(PROJECT/'out').resolve()
    # Reuse the previous byte-level PE/export/CodeView/PDB inspection with this release's header.
    source=Path(previous.__file__).read_text()
    begin=source.index('def inspect_pair(');end=source.index('\n\ndef main():',begin)
    inspection=source[begin:end].replace('0.3.4 | phase=3B3A','0.3.6 | phase=3C1')
    scope=vars(previous).copy();exec(inspection,scope);evidence=scope['inspect_pair'](build)
    prior=ROOT/'release/NVO-Combat-Packet-3C-Compiled/Source/NVOCombatCore'
    for n in ('CurrentHit.cpp','NativeObserver.cpp','DamageEvents.cpp','FlightPreview.cpp'):
        assert (prior/'src'/n).read_bytes()==(PROJECT/'src'/n).read_bytes(),n
    oldtiming=(prior/'src/FlightTiming.cpp').read_text().replace('#include "FlightTiming.hpp"','#include "FlightTiming.hpp"\n#include "FlightPhysics.hpp"')
    oldtiming=oldtiming.replace('    std::uint64_t h = 14695981039346656037ull;', '    if (!nvo::physics::NormalizeOwnedHooks(address, bytes, size)) return false;\n    std::uint64_t h = 14695981039346656037ull;')
    assert oldtiming==(PROJECT/'src/FlightTiming.cpp').read_text()
    outputs=[]
    for module,label in [('FlightPhysics','flight-physics'),('FlightTiming','flight-timing'),('CurrentHit','wrapper')]:
        for option,suffix in [('/disasm','disassembly'),('/symbols','symbols')]:
            name=f'{label}-{suffix}.txt';outputs.append(name)
            p=subprocess.run([str(DUMP),option,str(build/f'{module}.obj')],capture_output=True,check=True)
            (build/name).write_bytes(p.stdout)
    dis=(build/'flight-physics-disassembly.txt').read_text()
    bridge=dis[dis.index('?MatrixBridge@',dis.index('File Type:')):]
    # Find the actual function body, not an offset operand referring to the symbol.
    match=re.search(r'^\?MatrixBridge@[^\n]+:\n(.*?)(?=\n\?\w)',dis,re.M|re.S)
    assert match;bridge=match[1]
    move=re.search(r'^\?MovementBridge@[^\n]+:\n(.*?)(?=\n\?\w)',dis,re.M|re.S)
    assert move
    for token in ('pushfd','pushad','fxsave','fxrstor','popad','popfd','jmp','[ebx+2Ch]','[ebx+28h]','[ebx+18h]','[ebx+8]'):
        assert token in move[1],token
    assert move[1].count('call ')==1 and move[1].count('jmp ')==1 and not re.search(r'\bret\b',move[1])
    for token in ('pushfd','pushad','fxsave','fxrstor','popad','popfd','jmp','[ebx+2Ch]','[ebx+18h]','[ebx+10h]','[ebx+8]'):
        assert token in bridge,token
    assert bridge.count('call ')==1 and bridge.count('jmp ')==1 and not re.search(r'\bret\b',bridge)
    evidence['static_review']=[
        'New MovementBridge preserves GP/EFLAGS/x87/SSE/MXCSR, reads original ECX/EBP/timestep/vector, calls read-only helper once and tail-jumps to 0092F260 with original ret-0C cleanup.',
        'Existing MatrixBridge and physics argument write contract remain unchanged; bounded diagnostic counters explain early returns.',
        'Both owned CALL patches installed transactionally at DeferredInit; fingerprints normalize only fully contained verified owned bytes.',
        'CurrentHit, NativeObserver, DamageEvents and FlightPreview unchanged from 305; FlightTiming only adds owned-hook normalization to existing code guards.',
        'No added object/damage/position writes; movement-entry helper only observes. Mathematical gravity/drag, identity guard and original matrix call remain as in 305.',
        'Zero-update lives now emit PHYSICS_NO_UPDATE; PHYSICS_ARMED explicitly states execution_observed=0.',
        'No runtime execution, game launch or gameplay tests by assistant. Exact cause of 305 zero updates remains unproven; next user log is required.'
    ]
    (build/'static-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    (PROJECT/'BUILD-RESULT.md').write_text(f'''# Packet 3C1 build result

NVOCombatCore 0.3.6 / 306. Build `{build.name}`. Win32 MSVC 19.51.36257.0, /W4 /O2 /MT /Zi. Zero warnings/errors. Exactly NVSEPlugin_Load and NVSEPlugin_Query exports. Matching DLL/PDB GUID `{evidence['codeview_pdb_guid']}`, age {evidence['pdb_age']}.

DLL SHA256: {evidence['dll_sha256']}

PDB SHA256: {evidence['pdb_sha256']}

Compilation and static source/assembly/identity inspection only. No DLL execution, game launch, GECK work or gameplay tests. This packet diagnoses the 305 zero-update failure. The cause and working flight remain unverified until the user capture. Separate INSTALL-3C1 receipt records actual installation.
''')
    release=ROOT/'release/NVO-Combat-Packet-3C1-Compiled';dest=release/'Data/NVSE/Plugins';dest.mkdir(parents=True,exist_ok=True)
    for name in ('NVOCombatCore.dll','NVOCombatCore.pdb'):shutil.copyfile(build/name,dest/name)
    files=[]
    for name in ('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md'):
        files.append(PROJECT/name)
    for folder in ('include','src','config','reference'):files+=sorted(p for p in (PROJECT/folder).glob('*') if p.is_file())
    installed=[dict(path='Data/NVSE/Plugins/'+p.name,sha256=digest(p)) for p in sorted(dest.iterdir())]
    manifest=dict(packet='3C1',version='0.3.6',plugin_version=306,status='Compiled; user runtime acceptance pending',assistant_game_tested=False,
        native_flight_write_scope='Two exact private pilot weapon/ammo/projectile triples; checked movement argument only',damage_replacement=False,
        new_callsite='009BF411',original_target='0092F260',retained_physics_callsite='00930255',retained_timing_slot='0108FD54',new_dependencies=[],new_config=None,requires_existing_config='NVOFlightPhysics.ini',purpose='Distinguish missed movement hook from silent early filters; no claim of fixed flight',
        active_projectile_capacity=128,physics_continues_after_log_limits=True,detail_rows_maximum=7168,priority_rows_maximum=1024,
        build_output=str(build.relative_to(PROJECT)),installed_files=installed,source_files=[dict(path=p.relative_to(PROJECT).as_posix(),sha256=digest(p)) for p in files],
        installation_note='Package metadata only. See source/combat/step3c1/INSTALL-3C1-result.json for actual transaction.')
    (PROJECT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');files.append(PROJECT/'manifest.json')
    for p in files:
        target=release/'Source/NVOCombatCore'/p.relative_to(PROJECT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        if p.parent==PROJECT and p.suffix in ('.md','.html','.json','.txt'):shutil.copyfile(p,release/p.name)
    evidenceDir=release/'build-evidence';evidenceDir.mkdir(exist_ok=True)
    for name in ['build.log','toolchain.log','dll-details.txt','static-evidence.json']+outputs:shutil.copyfile(build/name,evidenceDir/name)
    (release/'Installation').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'tools/install_combat_3c1.ps1',release/'Installation/install_combat_3c1.ps1')
    oldplan=json.loads((ROOT/'source/combat/step3c/INSTALL-3C-plan.json').read_text())
    plan={**oldplan,'packet':'3C1','version':306,'created':'2026-09-15','files':[]}
    plan['protected_assets']=list(oldplan['protected_assets'])+['Data/NVSE/Plugins/NVOFlightPhysics.ini']
    for row in installed:
        p=GAME/row['path'];source=release/row['path']
        plan['files'].append(dict(path=row['path'],action='install',sha256=digest(p) if p.exists() else None,source=str(source),source_sha256=digest(source),log_may_change_until_game_exits=False))
    (ROOT/'source/combat/step3c1/INSTALL-3C1-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    zipPath=ROOT/'release/NVO-Combat-Packet-3C1-Compiled.zip'
    with zipfile.ZipFile(zipPath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(release.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(release).as_posix())
    with zipfile.ZipFile(ROOT/'release/NVO-Combat-Packet-3C1-Source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,'native/NVOCombatCore/'+p.relative_to(PROJECT).as_posix())
        for n in ('package_combat_3c1.py','package_combat_3b3a.py','install_combat_3c1.ps1'):z.write(ROOT/'tools'/n,'tools/'+n)
    print(json.dumps(dict(compiled_zip=str(zipPath),zip_sha256=digest(zipPath),zip_bytes=zipPath.stat().st_size,**evidence),indent=2))
if __name__=='__main__':main()
