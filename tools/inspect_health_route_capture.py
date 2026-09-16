"""Disassemble read-only health route snapshots, never execute their bytes."""
from pathlib import Path
import argparse, hashlib, json, struct, subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3k'
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
    address = int(row['address'], 16)
    if 'tables' in row['name']:
        continue
    obj = path.with_suffix('.obj')
    obj.write_bytes(struct.pack('<HHIIIHH', 0x14c, 1, 0, 0, 0, 0, 0)
                    + struct.pack('<8sIIIIIIHHI', b'.text', 0, address, len(data), 60, 0, 0, 0, 0, 0x60000020)
                    + data)
    output = subprocess.run([str(DUMPBIN), '/disasm', str(obj)], capture_output=True, check=True).stdout
    assert b'File Type: COFF OBJECT' in output
    path.with_suffix('.txt').write_bytes(output)
print(str(folder))
