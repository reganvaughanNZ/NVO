"""Analyze the archived user test; no game writes, builds or gameplay."""
from pathlib import Path
from collections import Counter
import hashlib, json, math, re

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT/'source/combat/step3c3/captures/2026-09-15-3C3-bcdb5bd990ab'
path = FOLDER/'NVOCombatCore.log'
raw = path.read_bytes()
lines = raw.decode('utf-8').splitlines()
rows = [(line.split(' ',1)[0],dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)',line)))
        for line in lines if line]

def vector(text):
    return tuple(map(float,text.strip('()').split(',')))

def distance(a,b):
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))

steps = {}
for name,row in rows:
    if name in ('PHYSICS_STEP','PHYSICS_ARGUMENT','PHYSICS_BOUNDARY','PHYSICS_ARGUMENT_RETURN','PHYSICS_ACTUAL'):
        key = (int(row['session']),int(row['lifetime']),int(row['step']))
        assert name not in steps.setdefault(key,{}), (name,key)
        steps[key][name] = row

comparisons = []
for key,step in sorted(steps.items()):
    assert len(step) == 5, key
    intent = step['PHYSICS_STEP']
    argument = step['PHYSICS_ARGUMENT']
    boundary = step['PHYSICS_BOUNDARY']
    returned = step['PHYSICS_ARGUMENT_RETURN']
    actual = step['PHYSICS_ACTUAL']
    submitted = vector(argument['readback'])
    candidate = vector(boundary['candidate_delta'])
    measured = vector(actual['actual_delta'])
    pitch,heading = float(intent['pitch']),float(intent['heading'])
    cp,sp,cy,sy = math.cos(pitch),math.sin(pitch),math.cos(heading),math.sin(heading)
    x,y,z = submitted
    full = (cy*x+sy*(cp*y+sp*z),-sy*x+cy*(cp*y+sp*z),-sp*y+cp*z)
    without_z = (cy*x+sy*cp*y,-sy*x+cy*cp*y,-sp*y)
    comparisons.append(dict(session=key[0],lifetime=key[1],step=key[2],phase=intent['phase'],
        input_readback=submitted,write_verified=int(argument['write_verified']),
        input_matches_boundary=submitted==vector(boundary['argument']),
        input_matches_return=submitted==vector(returned['argument']),
        boundary_path=boundary['path'],controller_present=int(boundary['controller_present']),
        candidate_delta=candidate,current_delta_before_commit=vector(boundary['current_delta']),
        actual_delta=measured,candidate_actual_difference=distance(candidate,measured),
        full_rotation_prediction=full,local_z_omission_prediction=without_z,
        omission_prediction_error=distance(without_z,measured),
        actual_verified=int(actual['matched']),full_intended_error=float(actual['vector_error']),
        tolerance=float(actual['tolerance']),
        interpretation='Local-Z omission fits movement destination; exact internal controller operation is not yet identified.'))

report = dict(log_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),lines=len(lines),
    archived_last_write=path.stat().st_mtime,
    event_counts=dict(Counter(row.get('phase') for name,row in rows if name=='FLIGHT_STEP')),
    comparisons=comparisons,
    lifecycle=[line for line in lines if line.startswith('LIFECYCLE ')],
    summaries=[line for line in lines if 'SUMMARY ' in line],
    physics_shots=[row for name,row in rows if name=='PHYSICS_SHOT'],
    cap_reached=any(line.startswith('DETAIL_LIMIT') for line in lines),
    physics_accepted=False,boundary_diagnostic_accepted=True,game_modified=False)
(FOLDER/'review-data.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('lifecycle','summaries')},indent=2))
