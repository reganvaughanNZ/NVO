"""Read three supplied donor archives without installing or running their contents."""
from pathlib import Path, PurePosixPath
import collections, hashlib, json, subprocess
from inspect_plugin import records, fields
ROOT=Path(__file__).resolve().parents[1]
DONORS=Path(r'C:\Users\regan\Desktop\NVO Mod References (Open Source)')
OUT=ROOT/'reference/ballistics-donors-20260915'
OUT.mkdir(parents=True,exist_ok=True)
names={
    'pbb':("Physics' Based Ballistics-82561-1-1-2-1743173812 (1).7z", "Physics' Based Ballistics-82561-1-1-2-1743173812.7z"),
    'cbd':('Caliber Based Damage-82543-3-0-1-1758669413 (2).7z','Caliber Based Damage-82543-3-0-1-1758669413 (1).7z'),
    'tracers':('Bullet Tracers New vegas-64198-1-5-1732215906.7z',None),
    'espless':('Improved Bullet Tracers - ESPless 98891 1.2.1 2026-08-15T15-19Z cGx5fkON.7z',None),
}
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={}
for key,(name,prior) in names.items():
    archive=DONORS/name
    listing=subprocess.run(['tar','-tf',str(archive)],capture_output=True,check=True).stdout.decode('utf-8').splitlines()
    row=dict(archive=str(archive),sha256=digest(archive),members=listing,
        identical_to_previous=bool(prior and digest(archive)==digest(DONORS/prior)),files=[],plugins=[])
    for member in listing:
        relative=PurePosixPath(member)
        assert not relative.is_absolute() and '..' not in relative.parts and ':' not in member
        if relative.suffix.lower() not in ('.txt','.ini','.xml','.esp','.gek'):continue
        data=subprocess.run(['tar','-xOf',str(archive),member],capture_output=True,check=True).stdout
        dest=OUT/key/Path(*relative.parts)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
        row['files'].append(dict(member=member,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        if relative.suffix.lower()=='.esp':
            plugin=dict(member=member,masters=[],records=[],counts={})
            counter=collections.Counter()
            for kind,form,flags,payload in records(data):
                counter[kind]+=1
                parts=list(fields(payload))
                entry=dict(type=kind,form=f'{form:08X}',flags=f'{flags:08X}')
                for tag,value in parts:
                    if tag in ('EDID','FULL','MODL') or kind=='TES4' and tag in ('CNAM','SNAM'):
                        entry[tag]=value.rstrip(b'\x00').decode('cp1252',errors='replace')
                    if tag=='MAST':plugin['masters'].append(value.rstrip(b'\x00').decode('cp1252'))
                    if tag in ('DATA','DNAM','NAM0','NAM1','NAM2'):entry[tag]=value.hex()
                plugin['records'].append(entry)
            plugin['counts']=dict(counter)
            row['plugins'].append(plugin)
    result[key]=row
(OUT/'inventory.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:dict(sha256=v['sha256'],identical_to_previous=v['identical_to_previous'],plugins=[dict(member=p['member'],masters=p['masters'],counts=p['counts']) for p in v['plugins']]) for k,v in result.items()},indent=2))
