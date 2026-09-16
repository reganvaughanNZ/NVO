"""Read-only review of the completed native324 six-shot checkpoint.

Produces workspace evidence only. Never modifies or launches the game.
"""
from pathlib import Path
import hashlib,json,math,re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'source/combat/step3u'
CAP=OUT/'captures/review-20453d5c1e84/NVOCombatCore.log'
EXPECTED='20453d5c1e84f965f408d0721c283d2b851e852cdae51b43ca2f2ef376900b08'
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
RELEASE=ROOT/'release/NVO-Combat-Packet-3U-Contact-Speed'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vec(s):return tuple(map(float,s.strip('()').split(',')))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def error(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def save(p,o):p.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8')

def main():
 assert sha(CAP)==EXPECTED
 text=CAP.read_text();assert text.startswith('NVOCombatCore 0.3.24 | phase=3U |')
 assert text.rstrip().endswith('LIFECYCLE exit_game')
 rows=[]
 for n,line in enumerate(text.splitlines(),1):
  rows.append(dict(tag=line.split(' ',1)[0],line=n,**dict(re.findall(r'(\w+)=([^\s]+)',line))))
 def tagged(tag):return [r for r in rows if r['tag']==tag]
 def lifetime(tag,number):
  found=[r for r in tagged(tag) if r.get('lifetime')==str(number)]
  assert len(found)==1,(tag,number,len(found));return found[0]
 assert len(tagged('STARTUP_BANNER'))==1
 assert len(tagged('IMPACT_SPEED'))==6
 assert not any(r['tag'].startswith(('PHYSICS_REJECT','PHYSICS_DISABLED','FLIGHT_ADMISSION_FAULT')) for r in rows)
 for r in rows:
  if 'damage_replacement' in r:assert r['damage_replacement']=='0'
 for tag,fields in {
  'SUMMARY':['unmatched','overflow','read_failures','open_lifetimes'],
  'PHYSICS_SUMMARY':['rejected','overflow','open'],
  'PHYSICS_ROUTE_SUMMARY':['mismatches','accounting_unpaired'],
  'FLIGHT_ADMISSION_SUMMARY':['failed','process_fault','slots_held'],
  'SPAWN_BOUNDARY_SUMMARY':['mismatched','null_returns','stale_returns','unscoped_creates'],
  'IMPACT_SUMMARY':['optional_read_failures','unpaired_callbacks','duplicate_collisions','duplicate_callbacks','log_write_failures'],
  'HIT_TX_SUMMARY':['invalid','open','log_failures'],
  'AV_APPLY_SUMMARY':['invalid','open','log_failures'],
  'PHYSICS_POOL_RESET':['slots_held'],'LIFECYCLE_POOL_RESET':['slots_held']}.items():
  for r in tagged(tag):
   for field in fields:assert r[field]=='0',(tag,field,r[field])
 assert sum(int(r['create']) for r in tagged('SUMMARY'))==6
 assert sum(int(r['impact']) for r in tagged('SUMMARY'))==6
 assert sum(int(r['destroy']) for r in tagged('SUMMARY'))==6
 source=RELEASE/'Source/NVOCombatCore/src/FlightContactSpeed.inl'
 assert 'if (s.valid!=31 || !s.policyRead || !s.target) return out;' in source.read_text()
 shots=[]
 for i in range(1,7):
  step=lifetime('IMPACT_STEP',i);speed=lifetime('IMPACT_SPEED',i);terrain=lifetime('IMPACT_TERRAIN',i)
  g=lifetime('IMPACT_GEOMETRY',i);boundary=lifetime('IMPACT_BOUNDARY',i)
  assert step['valid_mask']=='31' and speed['flags_read']=='1' and terrain['valid']=='1'
  assert step['more_contacts']=='0' and speed['reset_observed']=='1'
  assert lifetime('IMPACT_CALLBACK',i)['status']=='correlated'
  start,expected,candidate=vec(g['start']),vec(g['expected']),vec(terrain['candidate'])
  position,delta=vec(g['position']),vec(g['accounting_delta'])
  floor=float(terrain['floor']);tol=float(g['tolerance'])
  raised=floor-candidate[2]>30
  corrected=(candidate[0],candidate[1],floor if raised else candidate[2])
  metrics=dict(raise_rule_triggered=raised,floor_minus_candidate_units=floor-candidate[2],
    preclamp_endpoint_error=error(candidate,add(start,expected)),
    final_position_rule_error=error(position,corrected),
    final_accounting_rule_error=error(delta,tuple(x-y for x,y in zip(corrected,start))),
    contact_point_error=error(vec(terrain['contact']),vec(g['contact'])),tolerance=tol)
  assert metrics['preclamp_endpoint_error']<=tol
  assert metrics['final_position_rule_error']<=tol and metrics['final_accounting_rule_error']<=tol
  assert metrics['contact_point_error']<=tol
  assert terrain['target']==step['target'] and terrain['region']==step['region'] and terrain['flags']==speed['flags']
  if i in [2,3,4]:
   assert step['weapon']=='000E3778' and step['target']=='00000000'
   assert speed['status']=='snapshot_unavailable' and speed['available']=='0'
  else:assert speed['available']=='1' and speed['status']=='observed_engine_segment'
  shots.append(dict(shot=i,session=int(step['session']),weapon=step['weapon'],ammo=step['ammo'],
    target=step['target'],contact_region=int(step['region']),speed_status=speed['status'],
    speed_available=speed['available']=='1',mean_segment_mps=float(speed['mean_segment_mps']) if speed['available']=='1' else None,
    terrain_geometry=metrics,native_explained_clamp=terrain['explained_clamp']=='1',
    impact_step_line=step['line'],speed_line=speed['line'],terrain_line=terrain['line'],boundary_line=boundary['line']))
 assert [s['shot'] for s in shots if s['terrain_geometry']['raise_rule_triggered']]==[2,3]
 first=lifetime('IMPACT_HIT',1);vats=lifetime('IMPACT_HIT',5)
 assert first['contact_region']==first['hit_region']=='1'
 assert vats['contact_region']=='3' and vats['hit_region']=='0' and vats['regions_differ']=='1'
 # Body-part mapping from the supplied primary JIP source, not the VATS aim.
 mapping=Path(r'C:\Users\regan\Desktop\NVO Mod References (Open Source)\JIP-LN-NVSE-main\nvse\GameForms.h')
 assert re.search(r'eBodyPart_Torso = 0,\s+eBodyPart_Head1,\s+eBodyPart_Head2,\s+eBodyPart_LeftArm1,',mapping.read_text())
 manifest=json.loads((RELEASE/'manifest.json').read_text())
 checks=manifest['installed_files'][:]
 plan=json.loads((OUT/'INSTALL-3U-plan.json').read_text())
 checks += [x for x in plan['dependency_preconditions'] if Path(x['path']).stem!='NVOCombatCore']
 for item in checks:assert sha(GAME/item['path'])==item['sha256'],item['path']
 assert not (GAME/'Data/RD.esm').exists()
 result=dict(packet='3U',native_version=324,status='partial_pass_fix_required',capture=str(CAP.relative_to(ROOT)),
  capture_sha256=EXPECTED,shots=shots,creates=6,impacts=6,destroys=6,reloads=1,
  applied_steps=51,clear_flight_steps_verified=48,collision_ending_applied_steps=3,
  movement_rejections=0,unpaired_accounting=0,pools_clear_after_reload_and_exit=True,startup_banners=1,
  speed_results_available=3,zero_id_world_contacts_rejected=3,
  terrain_clamps_supported_by_recorded_geometry=2,terrain_clamps_accepted_by_native_estimator=0,
  vats=dict(shot=5,user_aim='torso',contact_region=3,contact_name='left arm 1',damage_record_region=0,damage_record_name='torso',automatic_remap=False),
  body_mapping_source=dict(path=str(mapping),sha256=sha(mapping)),installed_identities_verified=checks,
  source_rejection=dict(path=str(source.relative_to(ROOT)),sha256=sha(source),condition='!s.target before movement/terrain evaluation'),
  game_files_changed=False,damage_replacement=False,ultra_gate='HOLD',repeat_gameplay_needed_for_diagnosis=False,
  next='Ask before3U1: explicitly classify valid zero-ID world contacts separately from missing reads and actor identity; replay these exact six shots first. Preserve actor/hit identity guards. Do not globally waive target checks.')
 save(OUT/'RUNTIME-RESULT.json',result)
 save(CAP.parent/'audit.json',result)
 print(json.dumps({k:v for k,v in result.items() if k not in ['shots','installed_identities_verified','body_mapping_source','source_rejection']},indent=2))
if __name__=='__main__':main()
