"""Narrow, read-only comparison of GECK serialization differences in Packet 3N.

Never rewrite records. Preserve associations inside inventory and perk entries.
Layouts: xEdit dev-4.1.6 Core/wbDefinitionsFNV.pas (see review notes), and
xNVSE TESLeveledList::LoadBaseData for LVLO padding.
"""
from collections import Counter
import struct


def texture_entries(raw):
    count, = struct.unpack_from('<I', raw)
    at = 4
    entries = []
    for _ in range(count):
        size, = struct.unpack_from('<I', raw, at)
        end = at + 4 + size + 8
        assert end <= len(raw)
        entries.append(raw[at:end])
        at = end
    assert at == len(raw)
    return tuple(sorted(entries))


def layout_key(record):
    kind = record['kind']
    parts = record['parts']
    ordered, items, effects, spells, factions = [], [], [], [], []
    i = 0
    while i < len(parts):
        tag, value = parts[i]
        i += 1
        if kind in ('CONT', 'NPC_', 'CREA') and tag == 'CNTO':
            entry = [(tag, value)]
            if i < len(parts) and parts[i][0] == 'COED':
                entry.append(parts[i]); i += 1
            items.append(tuple(entry))
            continue
        if kind in ('NPC_', 'CREA') and tag in ('SPLO', 'SNAM'):
            (spells if tag == 'SPLO' else factions).append((tag, value))
            continue
        if kind == 'PERK' and tag == 'PRKE':
            entry = [(tag, value)]
            while i < len(parts) and parts[i][0] != 'PRKF':
                assert parts[i][0] != 'PRKE'
                entry.append(parts[i]); i += 1
            assert i < len(parts)
            entry.append(parts[i]); i += 1
            effects.append(tuple(entry))
            continue
        if kind == 'ARMO' and tag in ('MODS', 'MO3S'):
            value = texture_entries(value)
        elif kind == 'CELL' and tag == 'XCLR':
            assert len(value) % 4 == 0
            value = tuple(sorted(value[n:n+4] for n in range(0, len(value), 4)))
        elif kind == 'LVLI' and tag == 'LVLO':
            assert len(value) == 12
            value = value[:2] + b'\0\0' + value[4:10] + b'\0\0'
        elif kind == 'CREA' and tag == 'AIDT':
            assert len(value) == 20
            value = value[:5] + b'\0\0\0' + value[8:]
        elif (kind == 'QUST' and tag == 'QSTA') or (kind == 'REFR' and tag == 'XESP'):
            assert len(value) == 8
            value = value[:5] + b'\0\0\0'
        ordered.append((tag, value))
    return (record['flags'], ordered, Counter(items), Counter(effects),
            Counter(spells), Counter(factions))


def equivalent(a, b):
    if not a or not b or (a['kind'], a['fid']) != (b['kind'], b['fid']):
        return False
    try:
        return layout_key(a) == layout_key(b)
    except (AssertionError, struct.error):
        return False
