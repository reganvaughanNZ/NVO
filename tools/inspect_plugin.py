"""Read-only TES4/FNV record and embedded script inventory. Never writes plugins."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import struct
import zlib


def records(data, start=0, end=None):
    end = len(data) if end is None else end
    pos = start
    while pos < end:
        if pos + 24 > end:
            raise ValueError(f'Truncated record header at {pos}')
        kind = data[pos:pos + 4].decode('ascii')
        size = struct.unpack_from('<I', data, pos + 4)[0]
        if kind == 'GRUP':
            if size < 24 or pos + size > end:
                raise ValueError(f'Invalid group at {pos}')
            yield from records(data, pos + 24, pos + size)
            pos += size
            continue
        flags, form = struct.unpack_from('<II', data, pos + 8)
        stop = pos + 24 + size
        if stop > end:
            raise ValueError(f'Truncated record at {pos}')
        payload = data[pos + 24:stop]
        if flags & 0x40000:
            expected = struct.unpack_from('<I', payload)[0]
            payload = zlib.decompress(payload[4:])
            if len(payload) != expected:
                raise ValueError('Compressed size mismatch')
        yield kind, form, flags, payload
        pos = stop


def fields(payload):
    pos = 0
    extended = None
    while pos < len(payload):
        if pos + 6 > len(payload):
            raise ValueError('Truncated subrecord')
        tag = payload[pos:pos + 4].decode('ascii')
        size = struct.unpack_from('<H', payload, pos + 4)[0]
        pos += 6
        if tag == 'XXXX':
            extended = struct.unpack_from('<I', payload, pos)[0]
            pos += size
            continue
        size = extended if extended is not None else size
        extended = None
        if pos + size > len(payload):
            raise ValueError('Subrecord exceeds record')
        yield tag, payload[pos:pos + size]
        pos += size


def inspect(path):
    data = path.read_bytes()
    result = {'source': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
              'masters': [], 'records': [], 'scripts': []}
    counts = collections.Counter()
    for kind, form, flags, payload in records(data):
        counts[kind] += 1
        parts = list(fields(payload))
        strings = {tag: value.rstrip(b'\x00').decode('cp1252', errors='replace')
                   for tag, value in parts if tag in ('EDID', 'FULL', 'CNAM', 'SNAM') and kind == 'TES4'
                   or tag in ('EDID', 'FULL')}
        row = {'type': kind, 'form': f'{form:08X}', 'flags': f'{flags:08X}', **strings}
        if kind == 'TES4':
            result['masters'] = [v.rstrip(b'\x00').decode('cp1252') for t, v in parts if t == 'MAST']
        if kind == 'NPC_':
            row['actor_data'] = {t: list(v) for t, v in parts if t in ('DATA', 'DNAM', 'ACBS')}
            row['inventory'] = [{'form': f'{struct.unpack_from("<I", v)[0]:08X}',
                                 'count': struct.unpack_from('<i', v, 4)[0]}
                                for t, v in parts if t == 'CNTO']
        result['records'].append(row)
        for tag, value in parts:
            if tag == 'SCTX':
                result['scripts'].append({**row, 'source': value.rstrip(b'\x00').decode('cp1252', errors='replace')})
    result['counts'] = dict(counts)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('plugin', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = inspect(args.plugin)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'masters': result['masters'],
                      'counts': result['counts'], 'embedded_scripts': len(result['scripts'])}, indent=2))
