"""Archive/review the user's 310 flight log; no game/native execution or writes."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import hashlib, json, math, re
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas\NVOCombatCore.log')
PACKET=ROOT/'source/combat/step3c5'
before=SOURCE.stat();raw=SOURCE.read_bytes();after=SOURCE.stat()
assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns), 'Log changed during read'
sha=hashlib.sha256(raw).hexdigest()
lines=raw.decode('utf-8').splitlines()
assert lines[0].startswith('NVOCombatCore 0.3.10 | phase=3C5')
assert lines[-1]=='LIFECYCLE exit_game', 'Review a completed capture'
folder=PACKET/'captures'/f'2026-09-15-3C5-{sha[:12]}'
folder.mkdir(parents=True,exist_ok=True)
archive=folder/'NVOCombatCore.log'
if archive.exists():assert archive.read_bytes()==raw
else:archive.write_bytes(raw)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==sha
rows=[(l.split(' ',1)[0],dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)',l))) for l in lines if l]
def vec(s):return tuple(map(float,s.strip('()').split(',')))
def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
samples={}
for name,row in rows:
    if name in ('PHYSICS_STEP','PHYSICS_ARGUMENT','PHYSICS_LOCAL_Z','PHYSICS_CONTROLLER','PHYSICS_ACTUAL','PHYSICS_BOUNDARY','PHYSICS_ARGUMENT_RETURN'):
        key=tuple(int(row[k]) for k in ('session','lifetime','step'))
        label=name+(':'+row['phase'] if name=='PHYSICS_CONTROLLER' else '')
        assert label not in samples.setdefault(key,{})
        samples[key][label]=row
comparisons=[]
for key,sample in sorted(samples.items()):
    step=sample['PHYSICS_STEP'];arg=sample['PHYSICS_ARGUMENT'];local=sample['PHYSICS_LOCAL_Z']
    enter=sample['PHYSICS_CONTROLLER:virtual_enter'];leave=sample['PHYSICS_CONTROLLER:return']
    assert enter['vtable']=='01090594' and enter['target']=='00C73170'
    assert local['reset_branch_observed']=='1'
    assert (local['preserve'],local['original_reset'])==(('1','0') if step['phase']=='apply' else ('0','1'))
    assert vec(arg['readback'])==vec(enter['request'])==vec(leave['request'])==vec(local['working'])
    assert enter['dt_s']==step['movement_dt_s']==local['dt_s']
    actual=sample.get('PHYSICS_ACTUAL')
    comparison=dict(session=key[0],lifetime=key[1],step=key[2],phase=step['phase'],reset_preserved=int(local['preserve']),
                    request_preserved=True,free_flight_verified=actual is not None)
    if actual:
        error=distance(vec(step['world_delta']),vec(actual['actual_delta']))
        assert actual['matched']=='1' and error<=float(actual['tolerance'])
        assert float(actual['position_error'])<=float(actual['tolerance'])
        cp,sp=math.cos(float(step['pitch'])),math.sin(float(step['pitch']))
        cy,sy=math.cos(float(step['heading'])),math.sin(float(step['heading']))
        x,y,z=vec(arg['readback']);zero_z=(cy*x+sy*cp*y,-sy*x+cy*cp*y,-sp*y)
        comparison.update(vector_error=float(actual['vector_error']),recomputed_rounded_error=error,
            tolerance=float(actual['tolerance']),position_error=float(actual['position_error']),
            omission_error=distance(zero_z,vec(actual['actual_delta'])),dt=float(step['dt_s']))
    comparisons.append(comparison)
shot_summaries=[r for n,r in rows if n=='PHYSICS_SHOT' and r['reason']=='destroy']
assert len(shot_summaries)==2
for shot in shot_summaries:
    life=int(shot['lifetime']);same=[c for c in comparisons if c['lifetime']==life]
    missing=[c for c in same if not c['free_flight_verified']]
    assert len(missing)==1 and missing[0]['step']==int(shot['steps'])
    timing=[r for n,r in rows if n=='FLIGHT_STEP' and int(r['lifetime'])==life]
    assert timing[-1]['phase']=='collision' and sum(r['phase']=='collision' for r in timing)==1
    assert int(shot['verified_steps'])==sum(c['phase']=='apply' and c['free_flight_verified'] for c in same)
    assert shot['pending']==shot['controller_pending']=='0'
    assert shot['controller_entries']==shot['controller_returns']==shot['reset_entries']==shot['movement_entries']==shot['accounting_entries']
route=[r for n,r in rows if n=='PHYSICS_ROUTE_SUMMARY']
assert len(route)==1
assert route[0]['baselines_verified']=='2' and route[0]['applied_verified']=='10' and route[0]['mismatches']=='0'
assert route[0]['reset_entries']=='14' and route[0]['reset_preserved']=='12'
assert not any(n in ('PHYSICS_REJECT','PHYSICS_DISABLED','DETAIL_LIMIT','PRIORITY_LIMIT') for n,r in rows)
report=dict(source=str(SOURCE),log_sha256=sha,bytes=len(raw),lines=len(lines),
    source_last_write_local=datetime.fromtimestamp(after.st_mtime).isoformat(),archive=str(archive.relative_to(ROOT)),
    comparisons=comparisons,timing_phases=dict(Counter(r['phase'] for n,r in rows if n=='FLIGHT_STEP')),
    lifecycle=[l for l in lines if l.startswith('LIFECYCLE ')],summaries=[l for l in lines if 'SUMMARY ' in l],
    shots=shot_summaries,limited_two_weapon_flight_checkpoint_accepted=True,
    collision_steps_excluded_from_free_flight_verification=2,damage_accepted=False,
    new_reload_vats_stress_coverage=False,game_modified=False)
(folder/'review-data.json').write_text(json.dumps(report,indent=2)+'\n')
free=[c for c in comparisons if c['phase']=='apply' and c['free_flight_verified']]
print(json.dumps(dict(archive=str(archive),sha256=sha,bytes=len(raw),lines=len(lines),
    source_last_write_local=report['source_last_write_local'],free_flight_applied=len(free),
    max_vector_error=max(c['vector_error'] for c in free),max_error_fraction=max(c['vector_error']/c['tolerance'] for c in free),
    shots=shot_summaries,timing_phases=report['timing_phases'],summaries=report['summaries']),indent=2))
