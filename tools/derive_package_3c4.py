"""One-time, explicit derivation of the established package/install tooling."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'tools/package_combat_3c3.py'
s=p.read_text().replace('3C3','3C4').replace('3c3','3c4').replace('0.3.8','0.3.9').replace('308','309')
s=s.replace("prior=ROOT/'release/NVO-Combat-Packet-3C2-Compiled", "prior=ROOT/'release/NVO-Combat-Packet-3C3-Compiled")
s=s.replace("ROOT/'source/combat/step3c2/INSTALL-3C2-plan.json'", "ROOT/'source/combat/step3c3/INSTALL-3C3-plan.json'")
a=s.index("    evidence['static_review']=[")
b=s.index("    (build/'static-evidence.json')",a)
s=s[:a]+'''    for name in ('ControllerDispatchBridge','ControllerDirectBridge','ControllerReturnBridge'):
        m=re.search(r'^\\?'+name+r'@[^\\n]+:\\n(.*?)(?=\\n\\?)',dis,re.M|re.S)
        assert m,name
        body=m[1]
        for token in ('pushfd','pushad','fxsave','fxrstor','popad','popfd','cld','fninit','ldmxcsr','[ebx+18h]','[ebx+10h]','[ebx+8]','add         esp,18h'):
            assert token in body,(name,token)
        assert body.count('call ')==1 and body.count('jmp ')==1 and not re.search(r'\\bret\\b',body)
        if name=='ControllerDispatchBridge':
            assert 'mov         eax,dword ptr [edx+0C8h]' in body
            assert '[ebx+1Ch]' in body and '[ebx+28h]' in body and 'jmp         eax' in body
            assert body.index('[edx+0C8h]')<body.index('pushfd')
        elif name=='ControllerDirectBridge': assert '[ebx+28h]' in body and '0C70B60h' in body
    evidence['static_review']=[
        'Seven original spans checked against the archived loaded engine code; complete movement-body fingerprint retained.',
        'New virtual bridge recreates MOV EAX,[EDX+C8], saves full GP/EFLAGS/x87/SSE state, passes saved ECX/frame/args/request/target/phase, restores state and tail-jumps EAX.',
        'Eight-byte virtual span is CALL + three NOPs; original callee argument cleanup returns through NOPs to 0092FFF2.',
        'New direct and return observers use preserved original receivers, arguments, return addresses and one original tail jump; no engine calls from helpers.',
        'Read-only request entry/return paired by pending private identity, frame, controller, argument frame and thread.',
        'Optional target bytes limited to two targets/2048 bytes, committed executable game image only, no jump/call following.',
        'Variable-length owned spans normalize only complete exact patches; transaction and rollback cover the same three pages.',
        'Six hit/observer/timing/preview/log modules remain source-identical to 308. Existing 12-byte movement write/integrator/tolerance remain.',
        'No gravity fix claimed; compilation/static source/assembly/PE/PDB inspection only. No DLL execution or gameplay.'
    ]
'''+s[b:]
s=s.replace('This packet records the written/returned movement input and two read-only generic movement boundaries to locate the unresolved 307 vertical mismatch.', 'This packet records controller request entry/return and the concrete dispatched implementation to locate the unresolved vertical mismatch.')
s=s.replace("purpose='Locate the 307 vertical displacement mismatch through write readback and two read-only movement exit observations',boundary_observer_calls=['00930475','0092F5DC'],boundary_writes=False,", "purpose='Identify actual controller dispatch and compare request entry/return before correcting gravity',boundary_observer_calls=['00930475','0092F5DC'],controller_observer_spans=['0092FFEA:8','0092FFD4:5','0092FFFB:5'],boundary_writes=False,controller_request_writes=False,controller_code_capture_max_targets=2,controller_code_capture_bytes_per_target=2048,")
s=s.replace("    for name in ('COPY-QUIET-STARTUP.html','NVOCombatBootstrapScript-quiet.txt'):\n        shutil.copyfile(ROOT/'source/combat/step3c4'/name,release/name)\n", "    shutil.copyfile(ROOT/'source/combat/step3c4/IMPLEMENTATION.md',release/'Installation/IMPLEMENTATION.md')\n")
# Do not silently regenerate an already-created transaction plan after installation.
s=s.replace("    parser=argparse.ArgumentParser();", "    assert not (ROOT/'source/combat/step3c4/INSTALL-3C4-result.json').exists(), 'Already installed; do not regenerate preimages'\n    parser=argparse.ArgumentParser();")
(ROOT/'tools/package_combat_3c4.py').write_text(s,encoding='utf-8')
installer=(ROOT/'tools/install_combat_3c3.ps1').read_text(encoding='utf-8-sig').replace('3C3','3C4').replace('3c3','3c4').replace('308','309')
(ROOT/'tools/install_combat_3c4.ps1').write_text(installer,encoding='utf-8')
print('Derived 3C4 packager and allowlisted two-file installer.')
