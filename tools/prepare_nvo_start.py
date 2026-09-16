"""Prepare an independent donor fork and auditable sources; never edits the donor."""
from pathlib import Path
import json
import shutil
import struct
import zlib
from inspect_plugin import records, fields

ROOT = Path(__file__).resolve().parents[1]
DONOR = Path(r'C:\Users\regan\AppData\Roaming\Vortex\falloutnv\mods\Alternate Start With Delayed Main Quest-82319-1-60-1745944285')
OUT = ROOT / 'build' / 'NVO-Alternative-Start' / 'Data'


def fork_records(data, start=0, end=None):
    end = len(data) if end is None else end
    out = bytearray()
    pos = start
    while pos < end:
        header = bytearray(data[pos:pos + 24])
        size = struct.unpack_from('<I', header, 4)[0]
        if header[:4] == b'GRUP':
            payload = fork_records(data, pos + 24, pos + size)
            struct.pack_into('<I', header, 4, len(payload) + 24)
            pos += size
        else:
            payload = data[pos + 24:pos + 24 + size]
            compressed = struct.unpack_from('<I', header, 8)[0] & 0x40000
            if compressed:
                payload = zlib.decompress(payload[4:])
            # Equal-length string substitutions preserve compiled operand lengths.
            # Internal EditorIDs and FormIDs stay unchanged; the fork must run alone.
            for old, new in ((b'AltStart.esm', b'NVOStart.esm'),
                             (b'ALTStartConfig.ini', b'NVOStartConfig.ini')):
                assert len(old) == len(new)
                payload = payload.replace(old, new)
            if compressed:
                payload = struct.pack('<I', len(payload)) + zlib.compress(payload)
            struct.pack_into('<I', header, 4, len(payload))
            pos += 24 + size
        out += header + payload
    return bytes(out)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    fork = fork_records((DONOR / 'AltStart.esm').read_bytes())
    # Validate every record and subrecord before producing the fork.
    for kind, form, flags, payload in records(fork):
        list(fields(payload))
    target = OUT / 'NVOStart.esm'
    if target.exists():
        raise SystemExit('Refusing to overwrite an existing working fork.')
    target.write_bytes(fork)
    shutil.copy2(DONOR / 'ALTStart.bsa', OUT / 'NVOStart.bsa')
    (OUT / 'NVOStart.override').touch()
    (OUT / 'config').mkdir(exist_ok=True)
    shutil.copy2(DONOR / 'config' / 'ALTStartConfig.ini', OUT / 'config' / 'NVOStartConfig.ini')
    # Keep the optional later Courier cinematic available in the local build.
    shutil.copytree(DONOR / 'Video', OUT / 'Video', dirs_exist_ok=True)
    inventory = json.loads((ROOT / 'reference' / 'altstart-inventory.json').read_text())
    src = ROOT / 'reference' / 'donor-scripts'
    src.mkdir(exist_ok=True)
    for script in inventory['scripts']:
        if script['type'] == 'SCPT':
            (src / (script['EDID'] + '.txt')).write_text(script['source'], encoding='cp1252')
    by_form = {r['form']: r for r in inventory['records']}
    lists = {}
    for kind, form, flags, payload in records(fork):
        parts = list(fields(payload))
        edid = next((v.rstrip(b'\x00').decode('cp1252') for t, v in parts if t == 'EDID'), '')
        if edid in ('ALTBackList', 'ALTBackUDFList'):
            lists[edid] = [f'{struct.unpack("<I", v)[0]:08X}' for t, v in parts if t == 'LNAM']
    mapping = []
    assert len(lists['ALTBackList']) == len(lists['ALTBackUDFList'])
    for i, (msg, udf) in enumerate(zip(lists['ALTBackList'], lists['ALTBackUDFList'])):
        mapping.append({'id': i, 'message': by_form[msg], 'function': by_form[udf]})
    (ROOT / 'reference' / 'background-map.json').write_text(json.dumps(mapping, indent=2))
    for row in mapping:
        print(row['id'], row['message'].get('FULL'), row['function']['EDID'])
    print('Independent fork:', target)
