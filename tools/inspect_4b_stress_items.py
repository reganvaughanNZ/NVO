import json
from pathlib import Path
from inspect_plugin import records, fields

root = Path(__file__).resolve().parents[1]
game = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
chosen = []
for kind, form, flags, payload in records((game / 'Data/FalloutNV.esm').read_bytes()):
    if kind != 'MISC' or flags & (0x20 | 0x400):
        continue
    parts = dict(fields(payload))
    if 'SCRI' in parts or not parts.get('FULL') or not parts.get('MODL'):
        continue
    edid = parts.get('EDID', b'').rstrip(b'\0').decode('cp1252')
    full = parts['FULL'].rstrip(b'\0').decode('cp1252')
    if edid.lower().startswith(('v', 'test', 'unused', 'debug', 'dummy')):
        continue
    chosen.append(dict(form=f'{form:08X}', edid=edid, name=full, flags=flags))
out = root / 'source/combat/step4b/stress'
out.mkdir(exist_ok=True)
(out / 'CANDIDATE-ITEMS.json').write_text(json.dumps(chosen, indent=2), encoding='utf-8')
print(json.dumps(dict(count=len(chosen), items=[f'{r["form"]} {r["edid"]}' for r in chosen])))
