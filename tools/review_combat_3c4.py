"""Review archived 309 gameplay evidence and decode its bounded code capture offline."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,re,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'source/combat/step3c4/captures/2026-09-15-3C4-7e3ad3449a2c'
raw=(FOLDER/'NVOCombatCore.log').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='7e3ad3449a2c959bda7231b06540e132f97bd8a6cb009e094b849248f5f722a5'
lines=raw.decode('utf-8').splitlines()
rows=[(l.split(' ',1)[0],dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)',l))) for l in lines if l]
def vec(t): return tuple(map(float,t.strip('()').split(',')))
def distance(a,b): return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
samples={}; codes={}
for name,r in rows:
    if name in ('PHYSICS_STEP','PHYSICS_ARGUMENT','PHYSICS_BOUNDARY','PHYSICS_ARGUMENT_RETURN','PHYSICS_ACTUAL','PHYSICS_CONTROLLER'):
        key=tuple(int(r[k]) for k in ('session','lifetime','step'))
        field=name+(':'+r['phase'] if name=='PHYSICS_CONTROLLER' else '')
        assert field not in samples.setdefault(key,{})
        samples[key][field]=r
    if name=='PHYSICS_CONTROLLER_CODE_BEGIN':
        assert r['target'] not in codes
        codes[r['target']]={'meta':r,'data':bytearray()}
    elif name=='PHYSICS_CONTROLLER_CODE':
        c=codes[r['target']]; assert len(c['data'])==int(r['offset'],16)
        c['data'].extend(bytes.fromhex(r['hex']))
    elif name=='PHYSICS_CONTROLLER_CODE_END':
        c=codes[r['target']];assert len(c['data'])==int(r['bytes'])==int(c['meta']['bytes']);c['ended']=True
comparisons=[]
for key,s in sorted(samples.items()):
    enter=s.get('PHYSICS_CONTROLLER:virtual_enter',s.get('PHYSICS_CONTROLLER:direct_enter'))
    leave=s.get('PHYSICS_CONTROLLER:return')
    assert enter and leave
    arg=vec(s['PHYSICS_ARGUMENT']['readback']);p=s['PHYSICS_STEP'];actual=s['PHYSICS_ACTUAL']
    cp,sp=math.cos(float(p['pitch'])),math.sin(float(p['pitch']))
    cy,sy=math.cos(float(p['heading'])),math.sin(float(p['heading']))
    x,y,z=arg;zero_z=(cy*x+sy*cp*y,-sy*x+cy*cp*y,-sp*y)
    comparisons.append(dict(session=key[0],lifetime=key[1],step=key[2],phase=p['phase'],
        request_matches_input=vec(enter['request'])==arg,
        request_unchanged_after_controller=enter['request']==leave['request'],
        controller_phase=enter['phase'],vtable=enter['vtable'],target=enter['target'],request=arg,
        controller_dt_matches_move=enter['dt_s']==p['movement_dt_s'],
        candidate_equals_actual=s['PHYSICS_BOUNDARY']['candidate_delta']==actual['actual_delta'],
        actual_matches=int(actual['matched']),vector_error=float(actual['vector_error']),tolerance=float(actual['tolerance']),
        local_z_omission_error=distance(zero_z,vec(actual['actual_delta']))))
code_evidence=[]
dump=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/HostX64/x86/dumpbin.exe')
for target,c in codes.items():
    assert c.get('ended');data=bytes(c['data']);fnv=14695981039346656037
    for b in data: fnv=((fnv^b)*1099511628211)&0xffffffffffffffff
    assert f'{fnv:016X}'==c['meta']['fnv64']
    binpath=FOLDER/f'controller-{target}.bin';binpath.write_bytes(data)
    obj=FOLDER/f'controller-{target}.obj'
    obj.write_bytes(struct.pack('<HHIIIHH',0x14c,1,0,0,0,0,0)+struct.pack('<8sIIIIIIHHI',b'.text',0,int(target,16),len(data),60,0,0,0,0,0x60000020)+data)
    output=subprocess.run([str(dump),'/disasm',str(obj)],capture_output=True,check=True).stdout
    assert b'File Type: COFF OBJECT' in output
    (FOLDER/f'controller-{target}.txt').write_bytes(output)
    code_evidence.append(dict(target=target,bytes=len(data),fnv64=f'{fnv:016X}',sha256=hashlib.sha256(data).hexdigest(),complete=True))
report=dict(log_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),lines=len(lines),comparisons=comparisons,code=code_evidence,
    timing_phases=dict(Counter(r.get('phase') for n,r in rows if n=='FLIGHT_STEP')),
    lifecycle=[l for l in lines if l.startswith('LIFECYCLE ')],summaries=[l for l in lines if 'SUMMARY ' in l],
    physics_shots=[r for n,r in rows if n=='PHYSICS_SHOT'],cap_reached=any(l.startswith('DETAIL_LIMIT') for l in lines),
    physics_accepted=False,controller_diagnostic_accepted=True,game_modified=False)
(FOLDER/'review-data.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('lifecycle','summaries')},indent=2))
