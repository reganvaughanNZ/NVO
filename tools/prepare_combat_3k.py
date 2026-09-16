"""Read-only provider inspection for packet 3K; does not edit/build/install native code."""
from pathlib import Path
import hashlib
import json
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3k'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
PROVIDER = GAME / 'Data/NVSE/Plugins/itr-nvse.dll'
SOURCE = Path(r'C:\Users\regan\Desktop\NVO Mod References (Open Source)\itr-nvse-master\itr-nvse\handlers\OnPreDamageHandler.cpp')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect():
    expected = '31f5abad415750141906efbe810a32eb35ac714335e65e806215655c72c7fc0c'
    if sha(PROVIDER) != expected:
        raise ValueError('ITR provider changed; review the new provider before proceeding.')
    data = PROVIDER.read_bytes()
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    opt = pe + 24
    assert data[pe:pe+4] == b'PE\0\0'
    assert struct.unpack_from('<H', data, pe+4)[0] == 0x14c
    assert struct.unpack_from('<H', data, opt)[0] == 0x10b
    count = struct.unpack_from('<H', data, pe+6)[0]
    opt_size = struct.unpack_from('<H', data, pe+20)[0]
    image_base = struct.unpack_from('<I', data, opt+28)[0]
    sections = []
    for index in range(count):
        entry = opt + opt_size + index*40
        _, rva, raw_size, raw = struct.unpack_from('<IIII', data, entry+8)
        sections.append((rva, raw_size, raw))

    def offset(rva, size=1):
        for start, raw_size, raw in sections:
            if start <= rva and rva+size <= start+raw_size:
                result = raw+rva-start
                assert result+size <= len(data)
                return result
        raise ValueError(f'RVA not completely backed by file: {rva:X}+{size:X}')

    reloc_rva, reloc_size = struct.unpack_from('<II', data, opt+96+5*8)
    cursor = offset(reloc_rva, reloc_size)
    end = cursor + reloc_size
    relocations = []
    while cursor < end:
        page, size = struct.unpack_from('<II', data, cursor)
        assert size >= 8 and size % 2 == 0 and cursor+size <= end
        for value in struct.unpack_from('<'+'H'*((size-8)//2), data, cursor+8):
            kind = value >> 12
            assert kind in (0, 3)
            if kind == 3:
                relocations.append(page+(value & 0xfff))
        cursor += size

    disassembly_path = ROOT / 'source/combat/step3h/inspection/itr-disassembly.txt'
    disassembly = disassembly_path.read_text(encoding='utf-8-sig')
    block = re.search(r'^OnPreDamageHandler::Hook_DamageActorValue:\n(.*?)(?=^\S|\Z)',
                      disassembly, re.M | re.S)
    assert block
    instructions = re.findall(r'^  ([0-9A-F]{8}): ((?:[0-9A-F]{2} )*[0-9A-F]{2})\s',
                              block[1], re.M)
    start = int(instructions[0][0], 16)-image_base
    stop = int(instructions[-1][0], 16)-image_base+len(instructions[-1][1].split())
    assert (start, stop) == (0x34c1b, 0x34dc0)
    body = data[offset(start, stop-start):offset(start, stop-start)+stop-start]
    for address, encoded in instructions:
        at = int(address, 16)-image_base-start
        chunk = bytes.fromhex(encoded)
        assert body[at:at+len(chunk)] == chunk
    relative_relocations = sorted(r-start for r in relocations if start <= r < stop)
    assert len(set(relative_relocations)) == len(relative_relocations)
    assert all(r+4 <= len(body) for r in relative_relocations)
    fingerprint = 14695981039346656037
    for value in body:
        fingerprint = ((fingerprint ^ value)*1099511628211) & ((1 << 64)-1)

    findings = {
        'status': 'offline provider evidence only; engine runtime capture pending',
        'provider_path': str(PROVIDER), 'provider_sha256': expected,
        'source_path': str(SOURCE), 'source_sha256': sha(SOURCE),
        'disassembly_sha256': sha(disassembly_path),
        'preferred_base': image_base,
        'timestamp': struct.unpack_from('<I', data, pe+8)[0],
        'image_size': struct.unpack_from('<I', data, opt+56)[0],
        'thunk_rva': start, 'thunk_size': len(body),
        'thunk_sha256_preferred_base': hashlib.sha256(body).hexdigest(),
        'thunk_fnv64_preferred_base': f'{fingerprint:016X}',
        'highlow_relocation_offsets': relative_relocations,
        'relocation_rule': 'Subtract loaded-minus-preferred base at these dwords before hashing.',
        'damage_slot_offset': 0x3ac,
        'classes': [
            {'name': 'Character', 'table': 0x1086a6c, 'saved_original_rva': 0x7c754,
             'expected_engine_original': 0x881130},
            {'name': 'Creature', 'table': 0x10870ac, 'saved_original_rva': 0x7c748,
             'expected_engine_original': 0x8d49f0},
            {'name': 'PlayerCharacter', 'table': 0x108aa3c, 'saved_original_rva': 0x7c738,
             'expected_engine_original': 0x93b7a0},
        ],
        'engine_runtime_validated': False,
        'native_code_modified': False,
        'damage_replacement_enabled': False,
        'limitations': [
            'Expected engine originals come from on-disk tables, not captured loaded pointer values.',
            'ITR may scale health after the method-entry observation.',
            'A before/after observation measures the net change across the provider call, including nested work.',
            'This fingerprint alone does not validate engine getter behavior or terminal damage application.',
        ],
    }
    (PACKET / 'inspection/ITR-DamageActorValue.txt').write_text(block.group(0), encoding='utf-8')
    (PACKET / 'PROVIDER-FINDINGS.json').write_text(json.dumps(findings, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'thunk_bytes': len(body), 'relocations': len(relative_relocations),
                      'output': str(PACKET / 'PROVIDER-FINDINGS.json'),
                      'runtime_capture_pending': True}))


if __name__ == '__main__':
    inspect()
