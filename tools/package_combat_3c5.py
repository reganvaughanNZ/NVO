"""Package compiled 3C5, statically inspect identities, and prepare a reviewed install plan.
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
    assert not (ROOT/'source/combat/step3c5/INSTALL-3C5-result.json').exists(), 'Already installed; do not regenerate preimages'
    parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);args=parser.parse_args()
    build=(PROJECT/'out'/args.build).resolve();assert build.parent==(PROJECT/'out').resolve()
    # Reuse the previous byte-level PE/export/CodeView/PDB inspection with this release's header.
    source=Path(previous.__file__).read_text()
    begin=source.index('def inspect_pair(');end=source.index('\n\ndef main():',begin)
    inspection=source[begin:end].replace('0.3.4 | phase=3B3A','0.3.10 | phase=3C5')
    scope=vars(previous).copy();exec(inspection,scope);evidence=scope['inspect_pair'](build)
    prior=ROOT/'release/NVO-Combat-Packet-3C4-Compiled/Source/NVOCombatCore'
    for n in ('CurrentHit.cpp','NativeObserver.cpp','DamageEvents.cpp','FlightPreview.cpp','FlightTiming.cpp','NativeLog.cpp'):
        assert (prior/'src'/n).read_bytes()==(PROJECT/'src'/n).read_bytes(),n
    outputs=[]
    for module,label in [('FlightPhysics','flight-physics'),('FlightTiming','flight-timing'),('CurrentHit','wrapper')]:
        for option,suffix in [('/disasm','disassembly'),('/symbols','symbols')]:
            name=f'{label}-{suffix}.txt';outputs.append(name)
            p=subprocess.run([str(DUMP),option,str(build/f'{module}.obj')],capture_output=True,check=True)
            (build/name).write_bytes(p.stdout)
    dis=(build/'flight-physics-disassembly.txt').read_text()
    bridge=dis[dis.index('?AccountingBridge@',dis.index('File Type:')):]
    # Find the actual function body, not an offset operand referring to the symbol.
    match=re.search(r'^\?AccountingBridge@[^\n]+:\n(.*?)(?=\n\?\w)',dis,re.M|re.S)
    assert match;bridge=match[1]
    move=re.search(r'^\?MovementBridge@[^\n]+:\n(.*?)(?=\n\?\w)',dis,re.M|re.S)
    assert move
    for token in ('pushfd','pushad','fxsave','fxrstor','popad','popfd','jmp','[ebx+2Ch]','[ebx+28h]','[ebx+18h]','[ebx+8]'):
        assert token in move[1],token
    assert move[1].count('call ')==1 and move[1].count('jmp ')==1 and not re.search(r'\bret\b',move[1])
    for token in ('pushfd','pushad','fxsave','fxrstor','popad','popfd','jmp','[ebx+28h]','[ebx+34h]','[ebx+18h]','[ebx+8]'):
        assert token in bridge,token
    assert bridge.count('call ')==1 and bridge.count('jmp ')==1 and not re.search(r'\bret\b',bridge)
    for name in ('CommitBridge','NodeBridge'):
        m=re.search(r'^\?'+name+r'@[^\n]+:\n(.*?)(?=\n\?)',dis,re.M|re.S)
        assert m,name
        for token in ('pushfd','pushad','fxsave','fxrstor','popad','popfd','[ebx+10h]','[ebx+8]'):
            assert token in m[1],(name,token)
        assert m[1].count('call ')==1 and m[1].count('jmp ')==1 and not re.search(r'\bret\b',m[1])
    for name in ('ControllerDispatchBridge','ControllerDirectBridge','ControllerReturnBridge'):
        m=re.search(r'^\?'+name+r'@[^\n]+:\n(.*?)(?=\n\?)',dis,re.M|re.S)
        assert m,name
        body=m[1]
        for token in ('pushfd','pushad','fxsave','fxrstor','popad','popfd','cld','fninit','ldmxcsr','[ebx+18h]','[ebx+10h]','[ebx+8]','add         esp,18h'):
            assert token in body,(name,token)
        assert body.count('call ')==1 and body.count('jmp ')==1 and not re.search(r'\bret\b',body)
        if name=='ControllerDispatchBridge':
            assert 'mov         eax,dword ptr [edx+0C8h]' in body
            assert '[ebx+1Ch]' in body and '[ebx+28h]' in body and 'jmp         eax' in body
            assert body.index('[edx+0C8h]')<body.index('pushfd')
        elif name=='ControllerDirectBridge': assert '[ebx+28h]' in body and '0C70B60h' in body
    m=re.search(r'^\?LocalZBridge@[^\n]+:\n(.*?)(?=\n\?)',dis,re.M|re.S)
    assert m,'LocalZBridge'
    body=m[1]
    for token in ('pushfd','pushad','fxsave','cld','fninit','ldmxcsr','[ebx+28h]','[ebx+8]','[ebx+4]','[ebx+10h]',
                  'add         esp,10h','test        eax,eax','je','fldz','fstp        dword ptr [esp+5Ch]'):
        assert token in body,('LocalZBridge',token)
    assert body.count('call ')==1 and body.count('ret')==2 and body.count('fxrstor')==2
    assert body.count('popad')==2 and body.count('popfd')==2 and body.count('fldz')==1
    assert body.index('call ')<body.index('test        eax,eax')<body.index('fxrstor')
    assert '[esp+58h]' not in body
    native=(PROJECT/'src/FlightPhysics.cpp').read_text()
    assert 'Fingerprint(kControllerTarget,2048,0x0193951146A4412Cull)' in native
    assert 'baseline_reset_boundary_not_observed' in native
    assert 'gCapturedTargets' not in native and 'CaptureControllerCode' not in native
    assert 'stack!=(frame&~std::uintptr_t(15))-0xB0' in native
    assert '{kLocalZSite,6,{0xD9,0xEE,0xD9,0x5C,0x24,0x58}' in native
    assert 'opened<pageCount' in native and 'opened!=pageCount' in native
    # Preserve the physical integrator and numerical acceptance thresholds.
    old=(prior/'src/FlightPhysics.cpp').read_text()
    for begin,end in [('double Cd(','// Engine source direction:'),
                      ('    const double vectorError=','    t->pending=false;')]:
        a=native[native.index(begin):];a=a[:a.index(end)]
        b=old[old.index(begin):];b=b[:b.index(end)]
        assert a==b,begin
    evidence['static_review']=[
        'New six-byte reset span verified against the archived controller prefix; full prefix fingerprint added with exact owned-patch normalization.',
        'Eight hook spans occupy four distinct pages with transactional protection/cache/rollback; fallback does not disable the engine reset globally.',
        'LocalZBridge saves GP/EFLAGS/x87/SSE/MXCSR, passes original EBX/ESI/EBP and pre-patch ESP, restores state along both return paths.',
        'Fallback FLDZ/FSTP [ESP+5C] compensates exactly for the new CALL return address; both RET paths resume through one NOP at C7351C.',
        'Only exact private pending identity/thread/controller/frame/request/byte-vector/rotation/timestep validation permits preserving local Z.',
        'An unchanged baseline must observe the guarded reset branch and match actual movement before further input edits.',
        'No new object/position/damage write or engine call from the correction helper; collision and downstream engine movement retained.',
        'Existing RK4 integration, displacement tolerance and six hit/observer/timing/preview/log modules source-identical to 309.',
        'Completed raw target-byte diagnostic capture removed; new branch/per-life counters distinguish execution from flight acceptance.',
        'No DLL execution or gameplay. Runtime correction acceptance awaits the user.'
    ]
    (build/'static-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    (PROJECT/'BUILD-RESULT.md').write_text(f'''# Packet 3C5 build result

NVOCombatCore 0.3.10 / 310. Build `{build.name}`. Win32 MSVC 19.51.36257.0, /W4 /O2 /MT /Zi. Zero warnings/errors. Exactly NVSEPlugin_Load and NVSEPlugin_Query exports. Matching DLL/PDB GUID `{evidence['codeview_pdb_guid']}`, age {evidence['pdb_age']}.

DLL SHA256: {evidence['dll_sha256']}

PDB SHA256: {evidence['pdb_sha256']}

Compilation and static source/assembly/identity inspection only. No DLL execution, game launch, GECK work or gameplay tests. This packet conditionally preserves the pilot controller local Z at C73517 while replaying the original reset for all other calls. Runtime gravity/drag acceptance is pending. Separate INSTALL-3C5 receipt records actual installation.
''')
    release=ROOT/'release/NVO-Combat-Packet-3C5-Compiled';dest=release/'Data/NVSE/Plugins';dest.mkdir(parents=True,exist_ok=True)
    for name in ('NVOCombatCore.dll','NVOCombatCore.pdb'):shutil.copyfile(build/name,dest/name)
    files=[]
    for name in ('BUILD.cmd','CMakeLists.txt','README.md','START-HERE.html','BUILD-RESULT.md','SDK-BOUNDARY.md','sdk-reference.json','THIRD-PARTY-NOTICES.md','LICENSE-GPL-3.0.txt','LICENSE-ITR-MIT.txt','CREDITS-BALLISTX.md'):
        files.append(PROJECT/name)
    for folder in ('include','src','config','reference'):files+=sorted(p for p in (PROJECT/folder).glob('*') if p.is_file())
    installed=[dict(path='Data/NVSE/Plugins/'+p.name,sha256=digest(p)) for p in sorted(dest.iterdir())]
    manifest=dict(packet='3C5',version='0.3.10',plugin_version=310,status='Compiled; user runtime acceptance pending',assistant_game_tested=False,
        native_flight_write_scope='Two exact private triples; checked movement input and guarded preservation of controller local Z',damage_replacement=False,
        movement_callsite='009BF411',original_target='0092F260',accounting_callsite='009BF461',accounting_original='009C4E60',generic_matrix_hook=False,unchanged_initial_segments=1,retained_timing_slot='0108FD54',new_dependencies=[],new_config=None,requires_existing_config='NVOFlightPhysics.ini',purpose='Preserve the pilot local Z at the verified controller reset boundary and verify actual flight',boundary_observer_calls=['00930475','0092F5DC'],controller_observer_spans=['0092FFEA:8','0092FFD4:5','0092FFFB:5'],boundary_writes=False,controller_request_writes=False,controller_code_capture_max_targets=0,controller_code_capture_bytes_per_target=0,local_z_reset_site='00C73517',local_z_reset_span=6,controller_prefix_guard_bytes=2048,baseline_reset_observation_required=True,
        active_projectile_capacity=128,physics_continues_after_log_limits=True,detail_rows_maximum=7168,priority_rows_maximum=1024,
        build_output=str(build.relative_to(PROJECT)),installed_files=installed,source_files=[dict(path=p.relative_to(PROJECT).as_posix(),sha256=digest(p)) for p in files],
        installation_note='Package metadata only. See source/combat/step3c5/INSTALL-3C5-result.json for actual transaction.')
    (PROJECT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');files.append(PROJECT/'manifest.json')
    for p in files:
        target=release/'Source/NVOCombatCore'/p.relative_to(PROJECT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        if p.parent==PROJECT and p.suffix in ('.md','.html','.json','.txt'):shutil.copyfile(p,release/p.name)
    evidenceDir=release/'build-evidence';evidenceDir.mkdir(exist_ok=True)
    for name in ['build.log','toolchain.log','dll-details.txt','static-evidence.json']+outputs:shutil.copyfile(build/name,evidenceDir/name)
    (release/'Installation').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'tools/install_combat_3c5.ps1',release/'Installation/install_combat_3c5.ps1')
    shutil.copyfile(ROOT/'source/combat/step3c5/IMPLEMENTATION.md',release/'Installation/IMPLEMENTATION.md')
    oldplan=json.loads((ROOT/'source/combat/step3c4/INSTALL-3C4-plan.json').read_text())
    plan={**oldplan,'packet':'3C5','version':310,'created':'2026-09-15','files':[]}
    plan['protected_assets']=list(dict.fromkeys(oldplan['protected_assets']))
    for row in installed:
        p=GAME/row['path'];source=release/row['path']
        plan['files'].append(dict(path=row['path'],action='install',sha256=digest(p) if p.exists() else None,source=str(source),source_sha256=digest(source),log_may_change_until_game_exits=False))
    (ROOT/'source/combat/step3c5/INSTALL-3C5-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    zipPath=ROOT/'release/NVO-Combat-Packet-3C5-Compiled.zip'
    with zipfile.ZipFile(zipPath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(release.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(release).as_posix())
    with zipfile.ZipFile(ROOT/'release/NVO-Combat-Packet-3C5-Source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,'native/NVOCombatCore/'+p.relative_to(PROJECT).as_posix())
        for n in ('package_combat_3c5.py','package_combat_3b3a.py','install_combat_3c5.ps1','prepare_combat_3c5.py'):z.write(ROOT/'tools'/n,'tools/'+n)
    print(json.dumps(dict(compiled_zip=str(zipPath),zip_sha256=digest(zipPath),zip_bytes=zipPath.stat().st_size,**evidence),indent=2))
if __name__=='__main__':main()
