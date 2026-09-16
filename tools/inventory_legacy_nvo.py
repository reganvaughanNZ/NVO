"""Read-only legacy source inventory for reuse review. Never runs old scripts."""
from pathlib import Path
import hashlib, json
OLD=Path('C:/Users/regan/Documents/Codex/2026-08-16/can-you-explore-and-create-a')
OUT=Path(__file__).resolve().parents[1]/'reference/legacy-nvo-review'
OUT.mkdir(parents=True,exist_ok=True)
roots={'v09':OLD/'outputs/nvo-realism-hybrid-v0.9.0',
       'v10_staged':OLD/'outputs/NVO-Realism-v1.0.0-dev-staged',
       'v10_work':OLD/'work/nvo-realism-hybrid-v1.0.0-dev'}
inventories={}
for name,root in roots.items():
    files={p.relative_to(root).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
           for p in sorted(root.rglob('*')) if p.is_file() and p.suffix.lower() in ('.txt','.ini','.md','.ps1')}
    inventories[name]={'root':str(root),'files':files}
def udf_map(name):
    return {Path(k).name:v['sha256'] for k,v in inventories[name]['files'].items() if '/user_defined_functions/NVOCombat/' in k}
a,b,c=(udf_map(n) for n in roots)
summary={'v09_udfs':len(a),'v10_staged_udfs':len(b),'v10_work_udfs':len(c),
         'v09_unchanged_in_v10_staged':sorted(n for n in a if a[n]==b.get(n)),
         'v09_changed_in_v10_staged':sorted(n for n in a if n in b and a[n]!=b[n]),
         'v10_new_udfs':sorted(set(b)-set(a)),
         'v10_work_differences_from_staged':sorted(n for n in set(b)|set(c) if b.get(n)!=c.get(n))}
(OUT/'inventory.json').write_text(json.dumps({'summary':summary,'inventories':inventories},indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
