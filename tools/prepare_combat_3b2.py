"""Build six isolated flight-calibration records from the user's verified base ESM.

Writes workspace files only. No engine execution or game installation.
Record layout reference: TES5Edit/Core/wbDefinitionsFNV.pas, dev-4.1.6.
"""
from pathlib import Path
import hashlib
import json
import struct
from inspect_plugin import records, fields

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'source/combat/step3b2'
BASE = Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas/Data/FalloutNV.esm')
EXPECTED = '44e654569d47fcf8ceddc576c26dd11a32f207e60b1fd23cd6089e1e5f8fa84b'


def sub(tag, data):
    assert len(data) < 65536
    return tag.encode('ascii') + struct.pack('<H', len(data)) + data


def record(tag, fid, payload):
    # 24-byte FNV record header. Form version 15 is the standard FNV version.
    return struct.pack('<4sIIIIHH', tag.encode('ascii'), len(payload), 0, fid, 0, 15, 0) + payload


def main():
    raw = BASE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED, 'Base ESM changed. Review before copying records.'
    DEST.mkdir(parents=True, exist_ok=True)
    wanted = {0xE3778, 0x4333, 0x8ED03, 0x6B53C, 0x8F20F, 0x8F20A}
    originals = {fid: (kind, flags, list(fields(data))) for kind, fid, flags, data in records(raw) if fid in wanted}
    assert len(originals) == 6
    profiles = json.loads((ROOT / 'source/combat/step3a/NVO-Flight-Pilot.json').read_text())['profiles']
    output = {'WEAP': [], 'AMMO': [], 'PROJ': []}
    audit = []
    rows = [
        (0, '9mm', 0xE3778, 0x8ED03, 0x8F20F, 0x800, 0x802, 0x804),
        (1, '308', 0x4333, 0x6B53C, 0x8F20A, 0x801, 0x803, 0x805),
    ]
    for i, label, old_weapon, old_ammo, old_proj, local_weapon, local_ammo, local_proj in rows:
        values = profiles[i]['flight_inputs']
        muzzle = values['maximum_velocity_m_per_s'] * values['barrel_length_in'] / (values['barrel_length_in'] + 2 * values['bullet_travel_before_peak_pressure_in'])
        # One master => own records have file-local index 01, never a runtime index.
        weapon, ammo, proj = (0x01000000 | n for n in (local_weapon, local_ammo, local_proj))
        for kind, old, new, name in [
            ('WEAP', old_weapon, weapon, 'NVO Flight - ' + ('9mm Pistol' if i == 0 else 'Hunting Rifle')),
            ('AMMO', old_ammo, ammo, 'NVO Flight - ' + ('9mm Round' if i == 0 else '.308 Round')),
            ('PROJ', old_proj, proj, 'NVO Flight - ' + label + ' Bullet'),
        ]:
            old_kind, flags, parts = originals[old]
            assert old_kind == kind and flags == 0
            assert not any(k in ('SCRI', 'SCRO', 'SCTX') for k, v in parts)
            new_parts, changed = [], []
            for tag, value in parts:
                result = value
                if tag == 'EDID': result = ('NVOFlightPilot' + label + kind).encode() + b'\0'
                elif tag == 'FULL': result = name.encode() + b'\0'
                elif kind == 'WEAP' and tag == 'NAM0':
                    assert len(value) == 4
                    result = struct.pack('<I', ammo)
                elif kind == 'WEAP' and tag == 'DNAM':
                    assert len(value) == 204 and struct.unpack_from('<I', value, 36)[0] == old_proj
                    data = bytearray(value)
                    struct.pack_into('<I', data, 36, proj)
                    result = bytes(data)
                    assert value[:36] == result[:36] and value[40:] == result[40:]
                elif kind == 'AMMO' and tag == 'DAT2':
                    assert len(value) == 20 and value[:8] == bytes(8)
                    result = struct.pack('<II', 1, proj) + value[8:]
                elif kind == 'PROJ' and tag == 'DATA':
                    assert len(value) == 84 and struct.unpack_from('<H', value, 2)[0] == 1
                    data = bytearray(value)
                    struct.pack_into('<H', data, 0, struct.unpack_from('<H', value)[0] & ~1)
                    struct.pack_into('<ff', data, 4, 0.0, muzzle * 70.0)
                    result = bytes(data)
                    # Everything past speed is preserved, including stock range.
                    assert result[12:] == value[12:]
                if value != result:
                    changed.append({'subrecord': tag, 'before': value.hex(), 'after': result.hex()})
                new_parts.append((tag, result))
            allowed = {'WEAP': {'EDID', 'FULL', 'NAM0', 'DNAM'}, 'AMMO': {'EDID', 'FULL', 'DAT2'}, 'PROJ': {'EDID', 'FULL', 'DATA'}}[kind]
            assert {c['subrecord'] for c in changed} == allowed
            payload = b''.join(sub(k, v) for k, v in new_parts)
            output[kind].append(record(kind, new, payload))
            audit.append({'type': kind, 'origin': f'FalloutNV.esm:{old:06X}', 'local_id': f'{new & 0xffffff:06X}',
                          'name': name, 'changed_fields': changed, 'other_subrecords_byte_identical': True})
    header = b''.join([
        # HEDR includes the six records AND their three top-level groups.
        sub('HEDR', struct.pack('<fII', 1.34, 9, 0x806)), sub('CNAM', b'NVO\0'),
        sub('SNAM', b'Packet 3B2 isolated flight calibration. No overrides or distribution.\0'),
        sub('MAST', b'FalloutNV.esm\0'), sub('DATA', struct.pack('<Q', len(raw))),
    ])
    data = record('TES4', 0, header)
    for kind in ('WEAP', 'AMMO', 'PROJ'):
        body = b''.join(output[kind])
        data += struct.pack('<4sI4sIII', b'GRUP', 24 + len(body), kind.encode(), 0, 0, 0) + body
    parsed = list(records(data))
    assert len(parsed) == 7 and {fid for kind, fid, flags, payload in parsed[1:]} == set(range(0x01000800, 0x01000806))
    assert struct.unpack_from('<I', dict(fields(parsed[0][3]))['HEDR'], 4)[0] == 9
    assert all(flags == 0 for kind, fid, flags, payload in parsed)
    assert len({dict(fields(p))['EDID'] for k, f, fl, p in parsed[1:]}) == 6
    # Validate private reference graph independently from the construction loop.
    by_id = {fid: (kind, dict(fields(payload))) for kind, fid, flags, payload in parsed[1:]}
    for i in range(2):
        w, a, p = (by_id[0x01000800 + i + offset][1] for offset in (0, 2, 4))
        assert struct.unpack('<I', w['NAM0'])[0] == 0x01000802 + i
        assert struct.unpack_from('<I', w['DNAM'], 36)[0] == 0x01000804 + i
        assert struct.unpack_from('<II', a['DAT2']) == (1, 0x01000804 + i)
        assert not (struct.unpack_from('<H', p['DATA'])[0] & 1)
        assert struct.unpack_from('<f', p['DATA'], 4)[0] == 0
        original = dict(originals[rows[i][2]][2])
        assert w['DATA'] == original['DATA'] and w['CRDT'] == original['CRDT']
    (DEST / 'NVOFlightPilot.esp').write_bytes(data)
    report = {'packet': '3B2', 'base_sha256': EXPECTED, 'esp_sha256': hashlib.sha256(data).hexdigest(),
              'format_reference': 'https://raw.githubusercontent.com/TES5Edit/TES5Edit/dev-4.1.6/Core/wbDefinitionsFNV.pas',
              'records': audit, 'record_count': 6, 'overrides': 0, 'masters': ['FalloutNV.esm'],
              'new_scripts_quests_placements_lists': 0, 'stock_weapon_damage_preserved': True,
              'flight_owner': 'private PROJ records using engine movement, native measurement only',
              'gameplay_tested': False, 'unit_scale_independently_verified': False}
    (DEST / 'RECORD-AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    config = (ROOT / 'source/combat/step3b1/NVOFlightPreview.ini').read_text()
    for i, label, ow, oa, op, w, a, p in rows:
        v = profiles[i]['flight_inputs']
        config += f'''\n[pilot-{label}]
weapon=NVOFlightPilot.esp:{w:06X}
ammo=NVOFlightPilot.esp:{a:06X}
projectile=NVOFlightPilot.esp:{p:06X}
maximum_velocity_mps={v['maximum_velocity_m_per_s']:g}
barrel_in={v['barrel_length_in']:g}
peak_travel_in={v['bullet_travel_before_peak_pressure_in']:g}
'''
    config = config.replace('; NVO combat packet 3B1. Read-only preview, no flight or damage writes.', '; NVO combat packet 3B2. Native observation of isolated PROJ flight.\n; Native flight/damage writes stay off. NVOFlightPilot.esp supplies test flight.')
    (DEST / 'NVOFlightPreview.ini').write_text(config, encoding='ascii')
    (ROOT / 'native/NVOCombatCore/config/NVOFlightPreview.ini').write_text(config, encoding='ascii')
    print(json.dumps({k: v for k, v in report.items() if k != 'records'}, indent=2))


if __name__ == '__main__':
    main()
