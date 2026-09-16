"""Archive review and numerical comparison only; never edits or executes game files."""
from pathlib import Path
import hashlib, json, math, re
from inspect_plugin import records, fields

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
CAPTURE = ROOT/'source/combat/step3c2/captures/2026-09-15-3C2-5235b89c05fa'
data = (CAPTURE/'NVOCombatCore.log').read_bytes()
lines = data.decode('utf-8').splitlines()

def vals(line):
    return dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)', line))

def vec(text):
    return tuple(float(x) for x in text.strip('()').split(','))

def norm(v):
    return math.sqrt(sum(x*x for x in v))

pending, comparisons = {}, []
for line in lines:
    v = vals(line)
    if line.startswith('PHYSICS_STEP '):
        pending[v['session'],v['lifetime']] = v
    elif line.startswith('PHYSICS_ACTUAL ') and v['phase'] == 'apply':
        s = pending[v['session'],v['lifetime']]
        x,y,z = vec(s['world_delta'])
        pitch,heading = float(s['pitch']),float(s['heading'])
        cp,sp,cy,sy = math.cos(pitch),math.sin(pitch),math.cos(heading),math.sin(heading)
        lx,ly,lz = cy*x-sy*y,cp*(sy*x+cy*y)-sp*z,sp*(sy*x+cy*y)+cp*z
        # Hypothesis: the movement route discards local Z before rotation.
        discarded = (cy*lx+sy*cp*ly,-sy*lx+cy*cp*ly,-sp*ly)
        measured = vec(v['actual_delta'])
        residual = norm(tuple(a-b for a,b in zip(measured,discarded)))
        comparisons.append(dict(session=int(v['session']),lifetime=int(v['lifetime']),
            timestep_s=float(s['dt_s']),intended_world=(x,y,z),actual_world=measured,
            local_input_reconstructed=(lx,ly,lz),local_z_discard_prediction=discarded,
            local_z_discard_residual=residual,full_vector_error=float(v['vector_error']),
            tolerance=float(v['tolerance']),hypothesis_only=True))

plugin = GAME/'Data/NVO.esm'
plugin_data = plugin.read_bytes()
bootstrap = None
script_info = dict(found=False,source=str(plugin),plugin_sha256=hashlib.sha256(plugin_data).hexdigest())
for kind,form,flags,payload in records(plugin_data):
    if kind != 'SCPT': continue
    parts = dict(fields(payload))
    if parts.get('EDID',b'').rstrip(b'\0').lower() == b'nvocombatbootstrapscript':
        bootstrap = parts['SCTX'].rstrip(b'\0')
        (CAPTURE/'NVOCombatBootstrapScript-installed.txt').write_bytes(bootstrap)
        script_info = dict(form=f'{form:08X}',script_sha256=hashlib.sha256(bootstrap).hexdigest(),
            plugin_sha256=hashlib.sha256(plugin_data).hexdigest(),source=str(plugin))
        break
result = dict(log_sha256=hashlib.sha256(data).hexdigest(),log_bytes=len(data),log_lines=len(lines),
    log_source=str(GAME/'NVOCombatCore.log'),
    archive=str(CAPTURE),comparisons=comparisons,bootstrap=script_info,
    lifecycle=[x for x in lines if x.startswith('LIFECYCLE ')],
    summaries=[x for x in lines if 'SUMMARY ' in x],
    game_mutations=False,gameplay_tests=False)
(CAPTURE/'review-data.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('summaries','lifecycle')},indent=2))
if bootstrap: print(bootstrap.decode('cp1252'))
