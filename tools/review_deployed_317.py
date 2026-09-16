"""Read-only installed-file and embedded-source inventory for the 317 audit."""
from pathlib import Path
import hashlib,json,datetime,re
import inspect_plugin
ROOT=Path(__file__).resolve().parents[1]
GAME=Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
OUT=ROOT/'source/combat/review'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
old=json.loads((ROOT/'backups/combat-install-3G2-20260915-223757-9e77e29a/before.json').read_text())
protected=[dict(path=f['path'],expected=f['sha256'],actual=sha(Path(f['path']))) for f in old['protected']]
for f in protected:f['matches']=f['actual']==f['expected']
receipt=json.loads((ROOT/'source/combat/step3g2/INSTALL-3G2-result.json').read_text())
installed=[dict(path=f['path'],expected=f['sha256'],actual=sha(GAME/f['path']),release_sha256=sha(ROOT/'release/NVO-Combat-Packet-3G2-Compiled'/f['path'])) for f in receipt['installed']]
for f in installed:f['matches']=f['actual']==f['expected']==f['release_sha256']
loose=[]
for p in (GAME/'Data/NVSE').rglob('*'):
    if p.is_file() and p.suffix.lower() not in ('.log','.dll','.pdb'):
        loose.append(dict(path=str(p.relative_to(GAME)),bytes=p.stat().st_size,sha256=sha(p)))
activation={n:(Path(r'C:\Users\regan\AppData\Local\FalloutNV')/n).read_text(encoding='utf-8-sig') for n in ('plugins.txt','loadorder.txt')}
active=[]
for n in activation['plugins.txt'].splitlines():
    n=n.strip().lstrip('*')
    if n and not n.startswith('#'):active.append(n)
plugins=[];selected=[]
pattern=re.compile(r'Ballist|CBD|PBB|SimpleBleed|NVOCombat|PhysicsBased|SetWeaponDamage|SetProjectile|DamageAV|ModAV|SetAV',re.I)
for n in active:
    if n.startswith(('FalloutNV','DeadMoney','HonestHearts','OldWorldBlues','LonesomeRoad','CaravanPack','ClassicPack','MercenaryPack','TribalPack','GunRunnersArsenal','YUP')):continue
    p=GAME/'Data'/n
    if not p.is_file():continue
    inv=inspect_plugin.inspect(p)
    row=dict(name=n,sha256=inv['sha256'],masters=inv['masters'],counts=inv['counts'],script_count=len(inv['scripts']),quests=[x for x in inv['records'] if x['type']=='QUST'])
    plugins.append(row)
    for s in inv['scripts']:
        if pattern.search(s['source']) or pattern.search(s.get('EDID','')):selected.append(dict(plugin=n,**s))
report=dict(captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),installed=installed,protected=protected,protected_matched=sum(x['matches'] for x in protected),activation=activation,loose_files=loose,plugins=plugins,scope='Read-only deployed hash/loose file/embedded source inventory. Source text does not prove compiled execution; archive/load-hook execution not established. No game process inspection or launch.')
(OUT/'DEPLOYED-317.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'DEPLOYED-317-SCRIPTS.json').write_text(json.dumps(selected,indent=2)+'\n')
print(json.dumps(dict(installed=installed,protected_matched=report['protected_matched'],protected_count=len(protected),active=active,loose_files=loose,plugins=[{k:v for k,v in x.items() if k!='quests'} for x in plugins],script_matches=[dict(plugin=s['plugin'],form=s['form'],edid=s.get('EDID')) for s in selected]),indent=2))
