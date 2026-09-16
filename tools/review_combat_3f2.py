"""Audit the user's first3F2 capture. No gameplay or game-file changes."""
from pathlib import Path
import hashlib
import json
import math
import re

ROOT=Path(__file__).resolve().parents[1]
SHA='31ccf22118c2711f61712572fbd354a1e3a3de6fd8bbd7795d28eaa64ddb8c5d'
FOLDER=ROOT/'source/combat/step3f2/captures'/f'2026-09-15-3F2-{SHA[:12]}'
raw=(FOLDER/'NVOCombatCore.log').read_bytes()
assert hashlib.sha256(raw).hexdigest()==SHA
lines=raw.decode().splitlines()
assert lines[0].startswith('NVOCombatCore 0.3.13 | phase=3F2')
assert lines[-1]=='LIFECYCLE exit_game'
fields=lambda s:dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)',s))
rows=[(s.split()[0],fields(s)) for s in lines if s]
get=lambda name:[r for n,r in rows if n==name]
vec=lambda s:tuple(map(float,s.strip('()').split(',')))
dist=lambda a,b:math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
events=[(s.split()[3],fields(s)) for s in lines if s.startswith('EVENT ')]
creates=[r for n,r in events if n=='CREATE']
impacts=[r for n,r in events if n=='IMPACT']
destroys=[r for n,r in events if n=='DESTROY']
selection=get('FLIGHT_SELECT'); preview=get('FLIGHT_PREVIEW')
assert len(selection)==len(preview)==len(creates)==len(impacts)==len(destroys)==3
for i,(s,p,c,d) in enumerate(zip(selection,preview,creates,destroys),1):
    ammo,base,profile=('0013E443','0C00080E','hunting-rifle-hp') if i==2 else ('0006B53C','0C000807','hunting-rifle')
    assert s['session']==p['session']==c['session']==d['session']==str(i)
    assert p['lifetime']==c['lifetime']==d['lifetime']==str(i)
    assert s['ammo']==p['ammo']==c['ammo']==ammo
    assert s['profile']==p['profile']==profile and p['phase']=='create'
    assert s['replacement']==p['projectile_base']==base
    assert s['weapon']==p['weapon']==c['weapon']=='00004333'
    assert s['original']=='0008F20A' and s['source']==p['source']==c['source']=='00000014'
    assert c['tracked']==c['ammo_known']==d['matched']=='1'
assert [r['target'] for r in impacts]==['001070C1','FF001978','001070C1']
hits=get('HIT_CONTEXT');assert len(hits)==1
h=hits[0]
assert h['session']==h['lifetime']=='2' and h['linked']==h['ammo_known']=='1'
assert h['ammo']==h['creation_ammo']=='0013E443' and h['carrier']==preview[1]['projectile']
assert h['target']=='FF001978' and h['region']=='1'
assert len([s for s in lines if s.startswith('LIFECYCLE post_load_game success=1')])==3
assert not get('PHYSICS_REJECT') and not get('PHYSICS_DISABLED')
assert not get('PHYSICS_TERRAIN_REJECT_DEFAULT') and not get('PHYSICS_TERRAIN_REJECT_DEFAULT_VERIFIED')
terrain=get('PHYSICS_TERRAIN_SUMMARY')
assert [r['eligible_queries'] for r in terrain]==['4','3','6']
for r in terrain:
    for key in ('failed_queries','corrected','verified','collision_excluded','log_write_failures'):assert r[key]=='0'
routes=get('PHYSICS_ROUTE_SUMMARY')
assert [r['applied_verified'] for r in routes]==['3','2','5']
assert [r['baselines_verified'] for r in routes]==['1','1','1']
assert [r['move_entries_all'] for r in routes]==[r['accounting_entries_all'] for r in routes]==['5','4','7']
samples={}
for n,r in rows:
    if n in ('PHYSICS_STEP','PHYSICS_ARGUMENT','PHYSICS_LOCAL_Z','PHYSICS_CONTROLLER','PHYSICS_ACTUAL'):
        key=tuple(r[k] for k in ('session','lifetime','step'))
        label=n+(':'+r['phase'] if n=='PHYSICS_CONTROLLER' else '')
        assert label not in samples.setdefault(key,{})
        samples[key][label]=r
comparisons=[]
for key,sample in samples.items():
    step=sample['PHYSICS_STEP'];reset=sample['PHYSICS_LOCAL_Z']
    enter=sample['PHYSICS_CONTROLLER:virtual_enter'];leave=sample['PHYSICS_CONTROLLER:return']
    assert enter['target']=='00C73170' and enter['vtable']=='01090594'
    assert reset['reset_branch_observed']=='1'
    assert reset['preserve']==('1' if step['phase']=='apply' else '0')
    assert vec(sample['PHYSICS_ARGUMENT']['readback'])==vec(enter['request'])==vec(leave['request'])==vec(reset['working'])
    item=dict(session=key[0],lifetime=key[1],step=key[2],phase=step['phase'])
    actual=sample.get('PHYSICS_ACTUAL')
    if actual:
        assert actual['matched']=='1'
        error=dist(vec(step['world_delta']),vec(actual['actual_delta']))
        assert error<=float(actual['tolerance']) and float(actual['position_error'])<=float(actual['tolerance'])
        item.update(verified=True,vector_error=float(actual['vector_error']),position_error=float(actual['position_error']),tolerance=float(actual['tolerance']))
    else:
        assert (key[1],key[2]) in [('1','4'),('2','3'),('3','6')]
        item.update(verified=False,collision_excluded=True)
    comparisons.append(item)
assert len(comparisons)==16
assert sum(r['verified'] and r['phase']=='apply' for r in comparisons)==10
summary=[(n,r) for n,r in rows if n=='SUMMARY' or n.endswith('_SUMMARY')]
zeros=set('unmatched reused_live_address overflow read_failures open_lifetimes invalid_contexts open accounting_unpaired invalid retired_during_update overlap_lifetimes thread_changes nesting_limit identity_mismatches open_samples damage_replacement timing_writes damage_writes observer_writes skipped move_untracked accounting_untracked report_write_failures reports_omitted_by_limit mismatches lives_without_update'.split())
for n,r in summary:
    for key in zeros.intersection(r):assert r[key]=='0',(n,key)
data=dict(capture=json.loads((FOLDER/'capture.json').read_text()),
    correction_checkpoint_accepted=False,failed_terrain_query_reproduced=False,
    ordinary_movement_checks_passed=True,ammo_identity_at_fire_accepted=True,
    actual_ammo_sequence=['standard','HP','standard'],user_reported_last_ammo='HP',
    last_ammo_discrepancy='Both selector and creation identify standard .308 after a second reload; save-selection cause not directly observed.',
    loads=3,reloads=2,shots=3,impacts=impacts,hits=hits,
    impact_travel=[r for r in get('FLIGHT_TRAVEL') if r['phase']=='impact'],
    terrain_queries=13,terrain_failures=0,terrain_corrections=0,
    detailed_edited_matches=10,detailed_baselines=3,controller_pairs=16,collision_exclusions=3,
    comparisons=comparisons,summaries=summary,
    game_modified=False,assistant_gameplay=False,
    next_check='Same installed build; one level standard .308 shot across unobstructed open space, outside VATS, wait15s then exit. Need failed-query/correction/accounting correlation; no new DLL.')
(FOLDER/'review-data.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:data[k] for k in ('correction_checkpoint_accepted','actual_ammo_sequence','loads','reloads','terrain_queries','terrain_failures','detailed_edited_matches','controller_pairs')},indent=2))
