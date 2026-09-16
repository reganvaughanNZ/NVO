"""Read-only audit of the one-shot3F2 recheck, including the struck reference."""
from pathlib import Path
import hashlib
import json
import math
import re
from inspect_plugin import records

ROOT=Path(__file__).resolve().parents[1]
SHA='61b25ed13fb3accf597e3dcd8166fc76f43801a309fa136dbc43e843d1d69822'
FOLDER=ROOT/'source/combat/step3f2/captures'/f'2026-09-15-3F2-{SHA[:12]}'
raw=(FOLDER/'NVOCombatCore.log').read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
lines=raw.decode().splitlines();assert lines[0].startswith('NVOCombatCore 0.3.13 | phase=3F2') and lines[-1]=='LIFECYCLE exit_game'
fields=lambda s:dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)',s))
get=lambda n:[fields(s) for s in lines if s.startswith(n+' ')]
vec=lambda s:tuple(map(float,s.strip('()').split(',')))
s,=get('FLIGHT_SELECT');p,=get('FLIGHT_PREVIEW')
c,=[fields(s) for s in lines if s.startswith('EVENT ') and ' CREATE ' in s]
assert s['ammo']==p['ammo']==c['ammo']=='0006B53C'
assert s['weapon']==p['weapon']==c['weapon']=='00004333'
assert s['replacement']==p['projectile_base']=='0C000807'
assert s['source']==p['source']==c['source']=='00000014'
assert c['tracked']==c['ammo_known']=='1' and c['projectile']==p['projectile']
impact,=[fields(s) for s in lines if s.startswith('EVENT ') and ' IMPACT ' in s]
assert impact['target']=='001070C1' and impact['matched']=='1'
assert not get('HIT_CONTEXT') and not get('PHYSICS_REJECT') and not get('PHYSICS_DISABLED')
terrain,=get('PHYSICS_TERRAIN_SUMMARY');assert terrain['eligible_queries']=='5'
for key in ('failed_queries','corrected','verified','collision_excluded','log_write_failures'):assert terrain[key]=='0'
route,=get('PHYSICS_ROUTE_SUMMARY')
assert route['move_entries_all']==route['accounting_entries_all']=='6'
assert route['baselines_verified']=='1' and route['applied_verified']=='4'
steps={r['step']:r for r in get('PHYSICS_STEP')};actual=get('PHYSICS_ACTUAL')
assert len(steps)==6 and len(actual)==5
for a in actual:
    assert a['matched']=='1'
    error=math.dist(vec(steps[a['step']]['world_delta']),vec(a['actual_delta']))
    assert error<=float(a['tolerance']) and float(a['position_error'])<=float(a['tolerance'])
    matching=[r for r in get('PHYSICS_CONTROLLER') if r['step']==a['step']]
    assert len(matching)==2 and matching[0]['request']==matching[1]['request']
    assert matching[0]['target']==matching[1]['target']=='00C73170'
assert len(get('PHYSICS_LOCAL_Z'))==6
summary,=get('SUMMARY');assert summary['create']==summary['impact']==summary['destroy']=='1'
for name in ('SUMMARY','PHYSICS_ROUTE_SUMMARY','PHYSICS_DIAGNOSTIC_SUMMARY','FLIGHT_TIMING_SUMMARY','FLIGHT_PREVIEW_SUMMARY'):
    for r in get(name):
        for key in ('unmatched','reused_live_address','overflow','read_failures','open_lifetimes','mismatches','accounting_unpaired','lives_without_update','invalid','open','identity_mismatches','report_write_failures'):
            if key in r:assert r[key]=='0'
# Check whether the identified vanilla reference/base is overridden by NVO's three plugins.
game=Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
overrides=[]
for name in ('RD.esm','NVO.esm','NVOFlightPilot.esp'):
    for kind,fid,flags,payload in records((game/'Data'/name).read_bytes()):
        if fid in (0x1070C1,0x928F3):overrides.append(dict(plugin=name,type=kind,id=f'{fid:08X}'))
reference=json.loads((FOLDER/'impact-reference.json').read_text())
data=dict(capture=json.loads((FOLDER/'capture.json').read_text()),normal_flight_checks_passed=True,
    failed_terrain_query_reproduced=False,correction_checkpoint_accepted=False,
    baseline_verified=1,edited_steps_verified=4,movement_accounting_pairs=6,
    eligible_terrain_queries=5,failed_queries=0,corrections=0,impact=impact,
    impact_age_s=float(next(r for r in get('FLIGHT_TRAVEL') if r['phase']=='impact')['life_delta_s']),
    initial_pitch_degrees=float(steps['0']['pitch'])*180/math.pi,
    initial_vertical_velocity_mps=float(steps['0']['vz_before']),
    struck_reference=reference,matching_active_plugin_records=overrides,
    next_action='Ask before preparing a controlled test-position fixture. No further manual aiming retry requested.',
    game_modified=False,assistant_gameplay=False)
(FOLDER/'review-data.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:data[k] for k in ('normal_flight_checks_passed','correction_checkpoint_accepted','impact_age_s','initial_pitch_degrees','matching_active_plugin_records')},indent=2))
