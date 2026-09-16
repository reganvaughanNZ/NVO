"""Derive the next bounded package and the established two-file installer."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'tools/package_combat_3c4.py').read_text()
s=s.replace('3C4','3C5').replace('3c4','3c5').replace('0.3.9','0.3.10').replace('309','310')
s=s.replace("prior=ROOT/'release/NVO-Combat-Packet-3C3-Compiled", "prior=ROOT/'release/NVO-Combat-Packet-3C4-Compiled")
s=s.replace("ROOT/'source/combat/step3c3/INSTALL-3C3-plan.json'", "ROOT/'source/combat/step3c4/INSTALL-3C4-plan.json'")
start=s.index("    evidence['static_review']=[")
end=s.index("    (build/'static-evidence.json')",start)
block=r'''    m=re.search(r'^\?LocalZBridge@[^\n]+:\n(.*?)(?=\n\?)',dis,re.M|re.S)
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
'''
s=s[:start]+block+s[end:]
s=s.replace('This packet records controller request entry/return and the concrete dispatched implementation to locate the unresolved vertical mismatch. It is not an accepted physics correction.',
            'This packet conditionally preserves the pilot controller local Z at C73517 while replaying the original reset for all other calls. Runtime gravity/drag acceptance is pending.')
s=s.replace("native_flight_write_scope='Two exact private pilot weapon/ammo/projectile triples; checked movement argument only'", "native_flight_write_scope='Two exact private triples; checked movement input and guarded preservation of controller local Z'")
s=s.replace("purpose='Identify actual controller dispatch and compare request entry/return before correcting gravity'", "purpose='Preserve the pilot local Z at the verified controller reset boundary and verify actual flight'")
s=s.replace('controller_code_capture_max_targets=2,controller_code_capture_bytes_per_target=2048,',
            "controller_code_capture_max_targets=0,controller_code_capture_bytes_per_target=0,local_z_reset_site='00C73517',local_z_reset_span=6,controller_prefix_guard_bytes=2048,baseline_reset_observation_required=True,")
# Strengthen the existing installer without expanding its allowlist.
installer=(ROOT/'tools/install_combat_3c4.ps1').read_text(encoding='utf-8-sig')
installer=installer.replace('3C4','3C5').replace('3c4','3c5').replace('version=309','version=310')
installer=installer.replace("$nvoPlan = Get-Content -LiteralPath $nvoPlanPath -Raw | ConvertFrom-Json", """if (Test-Path -LiteralPath (Join-Path $nvoWorkspace 'source\\combat\\step3c5\\INSTALL-3C5-result.json')) { throw 'Installation already recorded; do not overwrite the transaction.' }
$nvoPlan = Get-Content -LiteralPath $nvoPlanPath -Raw | ConvertFrom-Json
if ($nvoPlan.packet -ne '3C5' -or $nvoPlan.version -ne 310 -or @($nvoPlan.empty_directories).Count) { throw 'Unexpected packet or cleanup scope.' }""")
installer=installer.replace('            # Remove the deployed file, never overwrite a possible Vortex hardlink.',
    '            $nvoTouched += $row.path\n            # Remove the deployed file, never overwrite a possible Vortex hardlink.')
installer=installer.replace('        $nvoTouched += $row.path\n        if ($row.action',
    '        if (-not $before.existed) { $nvoTouched += $row.path }\n        if ($row.action')
(ROOT/'tools/package_combat_3c5.py').write_text(s,encoding='utf-8')
(ROOT/'tools/install_combat_3c5.ps1').write_text(installer,encoding='utf-8')
print('Prepared the 3C5 packager, assembly checks and two-file installer.')
