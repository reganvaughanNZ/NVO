"""Wrap a verified runtime code snapshot as a COFF object for offline dumpbin.

COFF has no PE image header or entry point; this tool never executes game code.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'source/combat/step3b2/timing-investigation'
DUMPBIN = Path(r'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/HostX64/x86/dumpbin.exe')


def main():
    args = argparse.ArgumentParser()
    args.add_argument('capture', help='runtime-* directory name under timing-investigation')
    name = args.parse_args().capture
    folder = (DEST / name).resolve()
    assert folder.parent == DEST.resolve() and name.startswith('runtime-')
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8-sig'))
    code = (folder / 'projectile-code-009B7000.bin').read_bytes()
    assert manifest['code_base'] == '009B7000' and len(code) == manifest['code_bytes'] == 0xE000
    assert hashlib.sha256(code).hexdigest() == manifest['code_sha256']
    table = (folder / 'vtables-0108FA44.bin').read_bytes()
    assert len(table) == 0x9CC and hashlib.sha256(table).hexdigest() == manifest['vtable_sha256']
    obj = folder / 'projectile-code.obj'
    obj.write_bytes(struct.pack('<HHIIIHH', 0x14C, 1, 0, 0, 0, 0, 0)
                    + struct.pack('<8sIIIIIIHHI', b'.text', 0, 0x9B7000, len(code), 60, 0, 0, 0, 0, 0x60000020)
                    + code)
    output = subprocess.run([str(DUMPBIN), '/disasm', str(obj)], capture_output=True, check=True).stdout
    assert b'File Type: COFF OBJECT' in output
    (folder / 'projectile-disassembly.txt').write_bytes(output)
    dispatch = {}
    for label, base in [('MissileProjectile', 0x108FA44), ('Projectile', 0x10900DC)]:
        dispatch[label] = {f'{offset:03X}': f'{struct.unpack_from("<I", table, base - 0x108FA44 + offset)[0]:08X}'
                           for offset in (0x304, 0x308, 0x30C, 0x310, 0x314)}
    (folder / 'dispatch.json').write_text(json.dumps(dispatch, indent=2) + '\n')
    print(json.dumps({'capture': str(folder), 'dispatch': dispatch, 'code_execution': False}, indent=2))


if __name__ == '__main__':
    main()
