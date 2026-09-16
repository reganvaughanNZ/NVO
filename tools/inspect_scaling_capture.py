"""Read-only 3L evidence: disassemble captured bytes and inventory active GMSTs."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess
from inspect_plugin import records, fields

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3l'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
DUMPBIN = Path(r'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x86\dumpbin.exe')
parser = argparse.ArgumentParser()
parser.add_argument('capture')
args = parser.parse_args()
folder = (PACKET / args.capture).resolve()
assert folder.parent == PACKET.resolve() and folder.name.startswith('runtime-')
manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8-sig'))
for row in manifest['files']:
    path = folder / row['filename']
    assert path.parent == folder
    data = path.read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    if 'tables' in row['name']:
        continue
    obj = path.with_suffix('.obj')
    obj.write_bytes(struct.pack('<HHIIIHH', 0x14c, 1, 0, 0, 0, 0, 0)
                   + struct.pack('<8sIIIIIIHHI', b'.text', 0, int(row['address'], 16),
                                 len(data), 60, 0, 0, 0, 0, 0x60000020) + data)
    output = subprocess.run([str(DUMPBIN), '/disasm', str(obj)], capture_output=True, check=True).stdout
    assert b'File Type: COFF OBJECT' in output
    path.with_suffix('.txt').write_bytes(output)

loadorder = [s.strip() for s in (PACKET / 'inventory/loadorder.txt').read_text(encoding='utf-8-sig').splitlines()
             if s.strip() and not s.startswith('#')]
active = {s.strip().lstrip('*') for s in (PACKET / 'inventory/plugins.txt').read_text(encoding='utf-8-sig').splitlines()
          if s.strip() and not s.startswith('#')}
assert set(loadorder) == active
wanted = {s['name'] for s in manifest['settings'] if s['name'] != 'iDifficulty'}
chains = {name: [] for name in sorted(wanted)}
plugins = []
for name in loadorder:
    assert Path(name).name == name
    path = GAME / 'Data' / name
    data = path.read_bytes()
    plugins.append({'name': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    for kind, form, flags, payload in records(data):
        if kind != 'GMST':
            continue
        parts = dict(fields(payload))
        edid = parts['EDID'].rstrip(b'\0').decode('ascii')
        if edid not in wanted:
            continue
        assert not flags & 0x20, f'Deleted setting: {edid}'
        value, = struct.unpack('<f' if edid.startswith('f') else '<i', parts['DATA'])
        chains[edid].append({'plugin': name, 'form': f'{form:08X}', 'value': value})
result = {'scope': 'disk records in active load order, not script mutations', 'plugins': plugins,
          'chains': chains, 'runtime_comparison': []}
for s in manifest['settings']:
    if s['name'] in chains:
        chain = chains[s['name']]
        result['runtime_comparison'].append({'name': s['name'], 'live': s['value'],
            'winner': chain[-1] if chain else None,
            'matches': abs(s['value'] - chain[-1]['value']) < 1e-6 if chain else None})
(PACKET / 'inventory/GMST-OVERRIDES.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'capture': str(folder), 'active_plugins': len(plugins),
                  'comparisons': result['runtime_comparison']}, indent=2))
