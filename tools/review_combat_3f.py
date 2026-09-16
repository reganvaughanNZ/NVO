"""Review immutable user-run 3F evidence. No native, game or installation changes."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'source/combat/step3f'
SHA = 'f57f04e1f1b9ce8bae6fdbf22bf25f498e413e78319ff0d93c53a286de384010'
FOLDER = PACKET/f'captures/2026-09-15-3F-{SHA[:12]}'
raw = (FOLDER/'NVOCombatCore.log').read_bytes()
assert hashlib.sha256(raw).hexdigest() == SHA
lines = raw.decode('utf-8').splitlines()
assert lines[0].startswith('NVOCombatCore 0.3.11 | phase=3D') and lines[-1] == 'LIFECYCLE exit_game'
rows = [(s.split()[0], dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)', s))) for s in lines if s]
def get(name): return [r for n,r in rows if n == name]
def vec(s): return tuple(map(float,s.strip('()').split(',')))
def distance(a,b): return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
expected = {'hunting-rifle':('0006B53C','0C000807'),
            'hunting-rifle-ap':('0013E442','0C00080D'),
            'hunting-rifle-hp':('0013E443','0C00080E')}
selected, created = get('FLIGHT_SELECT'),get('FLIGHT_PREVIEW')
assert len(selected) == len(created) == 17
events = [(line.split()[3],dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)',line)))
          for line in lines if line.startswith('EVENT ')]
creates = [r for event,r in events if event == 'CREATE']
impacts = [r for event,r in events if event == 'IMPACT']
destroys = [r for event,r in events if event == 'DESTROY']
assert len(creates) == len(destroys) == 17 and len(impacts) == 13
for index,(s,c,e) in enumerate(zip(selected,created,creates),1):
    ammo,projectile = expected[s['profile']]
    assert s['session'] == c['session'] == e['session'] == '1'
    assert s['selection'] == c['lifetime'] == e['lifetime'] == str(index)
    assert s['profile'] == c['profile'] and s['ammo'] == c['ammo'] == e['ammo'] == ammo
    assert s['replacement'] == c['projectile_base'] == projectile
    assert s['weapon'] == c['weapon'] == e['weapon'] == '00004333'
    assert s['original'] == '0008F20A' and s['source'] == c['source'] == e['source'] == '00000014'
    assert c['phase'] == 'create' and e['tracked'] == e['ammo_known'] == '1'
    assert c['projectile'] == e['projectile']
assert Counter(s['profile'] for s in selected) == {'hunting-rifle':8,'hunting-rifle-ap':3,'hunting-rifle-hp':6}

samples = {}
for name,row in rows:
    if name in ('PHYSICS_STEP','PHYSICS_ARGUMENT','PHYSICS_LOCAL_Z','PHYSICS_CONTROLLER','PHYSICS_ACTUAL','PHYSICS_BOUNDARY'):
        key=tuple(int(row[k]) for k in ('session','lifetime','step'))
        label=name+(':'+row['phase'] if name == 'PHYSICS_CONTROLLER' else '')
        assert label not in samples.setdefault(key,{})
        samples[key][label]=row
comparisons=[]
for key,sample in sorted(samples.items()):
    step,arg,reset = (sample[n] for n in ('PHYSICS_STEP','PHYSICS_ARGUMENT','PHYSICS_LOCAL_Z'))
    enter,leave = sample['PHYSICS_CONTROLLER:virtual_enter'],sample['PHYSICS_CONTROLLER:return']
    assert enter['vtable'] == '01090594' and enter['target'] == '00C73170'
    assert reset['reset_branch_observed'] == '1'
    assert (reset['preserve'],reset['original_reset']) == (('1','0') if step['phase']=='apply' else ('0','1'))
    assert vec(arg['readback']) == vec(enter['request']) == vec(leave['request']) == vec(reset['working'])
    assert enter['dt_s'] == step['movement_dt_s'] == reset['dt_s']
    result=dict(session=key[0],lifetime=key[1],step=key[2],phase=step['phase'])
    actual=sample.get('PHYSICS_ACTUAL')
    result['detailed_free_flight_verified']=actual is not None
    if actual:
        error=distance(vec(step['world_delta']),vec(actual['actual_delta']))
        assert actual['matched']=='1' and error<=float(actual['tolerance'])
        assert float(actual['position_error'])<=float(actual['tolerance'])
        result.update(vector_error=float(actual['vector_error']),position_error=float(actual['position_error']),
                      tolerance=float(actual['tolerance']),recomputed_rounded_error=error)
    else:
        assert key[1] in (2,3,4,5,6,7) and key[2] == 1
        result['collision_boundary']=sample['PHYSICS_BOUNDARY']
    comparisons.append(result)
assert len(comparisons)==140
verified=[c for c in comparisons if c['detailed_free_flight_verified']]
edited=[c for c in verified if c['phase']=='apply']
assert len(verified)==134 and len(edited)==126
assert Counter(c['lifetime'] for c in edited)=={1:63,8:63}
rejects=get('PHYSICS_REJECT')
assert [(r['lifetime'],r['reason']) for r in rejects] == [(str(i),'applied_displacement_mismatch') for i in (8,10,13)]
routes=get('PHYSICS_ROUTE_SUMMARY')
assert [r['session'] for r in routes]==['1','2','3']
assert [r['applied_verified'] for r in routes]==['1296','0','0']
assert [r['mismatches'] for r in routes]==['3','0','0']
assert routes[0]['reset_entries']=='1329' and routes[0]['reset_preserved']=='1312'
assert routes[0]['baselines_verified']=='17'
assert routes[0]['move_entries_all']==routes[0]['accounting_entries_all']=='1767'
summaries=[(n,r) for n,r in rows if n=='SUMMARY' or n.endswith('_SUMMARY')]
zero_fields=set('unmatched reused_live_address overflow read_failures open_lifetimes invalid_contexts open accounting_unpaired lives_without_update invalid retired_during_update overlap_lifetimes thread_changes nesting_limit identity_mismatches open_samples damage_replacement timing_writes damage_writes observer_writes skipped move_untracked accounting_untracked'.split())
for name,row in summaries:
    for key in zero_fields.intersection(row): assert row[key]=='0',(name,key,row[key])
for row in get('SUMMARY'):
    if row['session']!='1': assert row['create']==row['impact']==row['destroy']=='0'
assert [r['profiles'] for r in get('FLIGHT_PREVIEW_READY')]==['11','11','11']
assert len([s for s in lines if s.startswith('LIFECYCLE post_load_game success=1')])==3
hits=get('HIT_CONTEXT')
assert len(hits)==3
for row in hits:
    assert row['linked']==row['ammo_known']=='1' and row['ammo']==row['creation_ammo']
    c=created[int(row['lifetime'])-1]
    assert row['ammo']==c['ammo'] and row['carrier']==c['projectile'] and row['weapon']==c['weapon']
    assert row['target']=='FF001978' and row['target_type']=='3B'
assert [(r['lifetime'],r['ammo']) for r in hits]==[('7','0013E443'),('9','0013E442'),('14','0006B53C')]
failed_flights=[]
for r in rejects:
    c=created[int(r['lifetime'])-1]
    travel=next(t for t in get('FLIGHT_TRAVEL') if t['lifetime']==r['lifetime'] and t['phase']=='destroy')
    failed_flights.append(dict(lifetime=int(r['lifetime']),profile=c['profile'],reason=r['reason'],
                              destroy_life_s=float(travel['life_delta_s']),engine_travel_units=float(travel['travel_delta_units']),
                              failure_measurements_logged=False))
data=dict(capture=json.loads((FOLDER/'capture.json').read_text()),packet_3F_accepted=False,
    ammo_identity_at_fire_accepted=True,post_reload_shot_verified=False,ammo_persistence_accepted=False,
    per_profile=dict(Counter(s['profile'] for s in selected)),selection_sequence=[s['profile'] for s in selected],
    all_17_selection_creation_pairs_corroborated=True,hits=hits,health_inputs=get('HEALTH_INPUT'),
    rejected_flights=failed_flights,summary_reported_edited_matches=1296,summary_applied_steps=1312,
    summary_baselines=17,summary_mismatches=3,detailed_edited_matches=126,detailed_baselines=8,
    detailed_controller_pairs=140,detailed_collision_exclusions=6,
    maximum_detailed_vector_error=max(c['vector_error'] for c in edited),
    maximum_detailed_error_fraction=max(c['vector_error']/c['tolerance'] for c in edited),
    maximum_detailed_position_error=max(c['position_error'] for c in verified),
    diagnostic_limits=dict(lifetimes=8,accounting_entries_per_lifetime=64,failures_outside_detailed_trace=True),
    comparisons=comparisons,summaries=summaries,lifecycle=[s for s in lines if s.startswith('LIFECYCLE ')],
    selected_ammo_at_save_or_load_logged=False,user_report='HP did not remain equipped between loads.',
    damage_authority_accepted=False,game_modified=False,gameplay_tested_by_assistant=False)
(FOLDER/'review-data.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in data.items() if k in ('packet_3F_accepted','ammo_identity_at_fire_accepted','per_profile','rejected_flights','summary_reported_edited_matches','detailed_edited_matches','maximum_detailed_vector_error','maximum_detailed_error_fraction','maximum_detailed_position_error')},indent=2))
