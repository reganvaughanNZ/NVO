"""Disassemble hash-verified runtime code offline. Never execute captured bytes."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DUMPBIN = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/HostX64/x86/dumpbin.exe')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    folder = args.capture.resolve()
    assert folder.is_relative_to(ROOT / 'source/combat')
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8-sig'))
    result = []
    for row in manifest['files']:
        path = (folder / row['filename']).resolve()
        assert path.parent == folder
        code = path.read_bytes()
        assert len(code) == row['bytes'] and hashlib.sha256(code).hexdigest() == row['sha256']
        address = int(row['address'], 16)
        item = dict(name=row['name'], address=row['address'], sha256=row['sha256'])
        if len(code) == 8:
            item['double'] = struct.unpack('<d', code)[0]
            item['raw_hex'] = code.hex()
        elif 0x401000 <= address < 0x1016000:
            obj = folder / (row['name'] + '.obj')
            obj.write_bytes(struct.pack('<HHIIIHH', 0x14C, 1, 0, 0, 0, 0, 0)
                + struct.pack('<8sIIIIIIHHI', b'.text', 0, address, len(code), 60, 0, 0, 0, 0, 0x60000020) + code)
            text = subprocess.run([str(DUMPBIN), '/disasm', str(obj)], capture_output=True, check=True).stdout
            (folder / (row['name'] + '.txt')).write_bytes(text)
            item['disassembled'] = True
        result.append(item)
    (folder / 'inspection.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
