"""Prepare the 3D1 record/config correction. Workspace writes only; no game execution.

Engine projectile identity and BallistX cartridge-row identity are intentionally separate.
The old 3D packet and its transaction remain immutable.
"""
from pathlib import Path
import configparser
import hashlib
import json
import shutil
import struct
import subprocess

from inspect_plugin import records, fields
from prepare_combat_3b2 import sub

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3d1'
PREVIOUS = ROOT / 'source/combat/step3d'
RELEASE = ROOT / 'release/NVO-Combat-Packet-3D1-Update'
GAME = Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
DONOR = Path(r'C:/Users/regan/Desktop/NVO Mod References (Open Source)/BallistX-70341-5-4-1712065466.rar')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def main():
    assert not (PACKET / 'INSTALL-3D1-result.json').exists(), 'Do not regenerate installed preimages.'
    PACKET.mkdir(parents=True, exist_ok=True)
    previous_result = json.loads((PREVIOUS / 'INSTALL-3D-result.json').read_text(encoding='utf-8-sig'))
    previous_hashes = {row['path']: row['sha256'] for row in previous_result['installed']}
    # Verify the installed foundation, rather than silently overwriting intervening changes.
    for relative, expected in previous_hashes.items():
        assert sha(GAME / relative) == expected, ('Installed foundation changed', relative)
    assert sha(GAME / 'Data/FalloutNV.esm') == '44e654569d47fcf8ceddc576c26dd11a32f207e60b1fd23cd6089e1e5f8fa84b'
    assert sha(DONOR) == 'd71fe28f1262dec7a0f2086f06b243168d74a3f11d8b57cd8b7b8127c9506e3d'
    assert sha(PREVIOUS / 'NVOFlightPilot.esp') == previous_hashes['Data/NVOFlightPilot.esp']
    assert sha(PREVIOUS / 'NVOFlightPreview.ini') == previous_hashes['Data/NVSE/Plugins/NVOFlightPreview.ini']
    canonical = ROOT / 'native/NVOCombatCore/config/NVOFlightPreview.ini'
    original_config = (PREVIOUS / 'NVOFlightPreview.ini').read_text(encoding='ascii')

    # name, weapon, actual engine source, donor cartridge key; do not infer one from another.
    mappings = [
        ('9mm-pistol', 0xE3778, 0x8F20F, 0x8F20F),
        ('hunting-rifle', 0x4333, 0x8F20A, 0x8F20A),
        ('9mm-smg', 0x8F217, 0x17A2C6, 0x8F20F),
        ('service-rifle', 0xE9C3B, 0x426D, 0x426D),
    ]
    old_cfg = configparser.ConfigParser()
    old_cfg.read_string(original_config)
    before = '[9mm-smg]\nweapon=FalloutNV.esm:08F217\nammo=FalloutNV.esm:08ED03\nsource_projectile=FalloutNV.esm:08F20F'
    after = before.replace('source_projectile=FalloutNV.esm:08F20F', 'source_projectile=FalloutNV.esm:17A2C6')
    assert original_config.count(before) == 1
    config = original_config.replace(before, after).replace('; Packet 3D.', '; Packet 3D1. SMG original projectile corrected.')
    assert canonical.read_text(encoding='ascii') in (original_config, config), 'Canonical config changed; inspect first.'
    cfg = configparser.ConfigParser()
    cfg.read_string(config)
    assert cfg.sections() == old_cfg.sections()
    changes = [(section, key) for section in cfg for key in cfg[section]
               if cfg[section][key] != old_cfg[section][key]]
    assert changes == [('9mm-smg', 'source_projectile')]

    wanted = {form for row in mappings for form in row[1:3]}
    base = (GAME / 'Data/FalloutNV.esm').read_bytes()
    originals = {fid: (kind, flags, list(fields(data)))
                 for kind, fid, flags, data in records(base) if fid in wanted}
    assert len(originals) == len(wanted)
    tables = {}
    for table in ('WeaponData', 'CartridgeData'):
        text = subprocess.run(['tar', '-xOf', str(DONOR), f'Config/BallistX/Data/{table}.cfg'],
                              capture_output=True, check=True).stdout.decode('cp1252')
        tables[table] = text.replace('\r\r\n', '\n').replace('\r\n', '\n').splitlines()

    def donor_row(table, fid):
        key = f'@FalloutNV.esm:{fid:06X}'
        matches = [(i, line) for i, line in enumerate(tables[table], 1)
                   if line.split(';')[0].split() and line.split(';')[0].split()[0] == key]
        assert len(matches) == 1, (table, key)
        number, line = matches[0]
        return list(map(float, line.split(';')[0].split()[1:])), dict(line=number, text=line)

    audits = []
    for name, weapon, source, cartridge in mappings:
        assert originals[weapon][0] == 'WEAP' and originals[source][0] == 'PROJ'
        actual = struct.unpack_from('<I', dict(originals[weapon][2])['DNAM'], 36)[0]
        assert actual == source, (name, 'WEAP projectile mismatch', actual, source)
        assert cfg[name]['weapon'] == f'FalloutNV.esm:{weapon:06X}'
        assert cfg[name]['source_projectile'] == f'FalloutNV.esm:{actual:06X}'
        weapon_values, wr = donor_row('WeaponData', weapon)
        cartridge_values, cr = donor_row('CartridgeData', cartridge)
        model, bc, mass, diameter, maximum, peak, temperature, damage = cartridge_values
        expected = dict(drag_model=model, ballistic_coefficient=bc,
                        maximum_velocity_mps=maximum, peak_travel_in=peak, barrel_in=weapon_values[0])
        assert all(float(cfg[name][key]) == value for key, value in expected.items())
        audits.append(dict(profile=name, weapon=f'{weapon:08X}', actual_source_projectile=f'{source:08X}',
                           donor_cartridge_key=f'{cartridge:08X}', weapon_source=wr, cartridge_source=cr,
                           weapon_projectile_mapping_verified=True, tuning_unchanged=True))
    # In this installation NVO has no overrides of the source weapons/projectiles.
    overrides = [f'{fid:08X}' for kind, fid, flags, data in records((GAME / 'Data/NVO.esm').read_bytes())
                 if fid in wanted]
    assert not overrides, ('Inspect NVO overrides before claiming base-game relationships', overrides)

    previous = (PREVIOUS / 'NVOFlightPilot.esp').read_bytes()
    old_records = list(records(previous))
    smg_id = 0x01000808  # File-local index: one master, not a runtime load-order index.
    old_smg = next(dict(fields(data)) for kind, fid, flags, data in old_records if fid == smg_id)
    kind, flags, parts = originals[0x17A2C6]
    assert kind == 'PROJ' and flags == 0
    profile = cfg['9mm-smg']
    muzzle = float(profile['maximum_velocity_mps']) * float(profile['barrel_in']) / (
        float(profile['barrel_in']) + 2 * float(profile['peak_travel_in']))
    new_parts = []
    for tag, value in parts:
        new = value
        if tag in ('EDID', 'FULL'):
            new = old_smg[tag]  # Stable private Editor ID and presentation name.
        elif tag == 'DATA':
            assert len(value) == 84 and struct.unpack_from('<H', value, 2)[0] == 1
            source_flags = struct.unpack_from('<H', value)[0]
            assert not source_flags & 0x402
            new = bytearray(value)
            struct.pack_into('<H', new, 0, source_flags & ~1)
            struct.pack_into('<ff', new, 4, 0, muzzle * 70)
            new = bytes(new)
            assert new[12:] == value[12:] and new[2:4] == value[2:4]
        new_parts.append((tag, new))
    payload = b''.join(sub(tag, value) for tag, value in new_parts)
    replacements = []

    def rewrite(start, end):
        output = bytearray()
        pos = start
        while pos < end:
            header = bytearray(previous[pos:pos + 24])
            size = struct.unpack_from('<I', header, 4)[0]
            if header[:4] == b'GRUP':
                body = rewrite(pos + 24, pos + size)
                struct.pack_into('<I', header, 4, 24 + len(body))
                pos += size
            else:
                fid = struct.unpack_from('<I', header, 12)[0]
                body = previous[pos + 24:pos + 24 + size]
                if fid == smg_id:
                    assert header[:4] == b'PROJ'
                    body = payload
                    struct.pack_into('<I', header, 4, len(body))
                    replacements.append(fid)
                pos += 24 + size
            output.extend(header)
            output.extend(body)
        assert pos == end
        return bytes(output)

    output = rewrite(0, len(previous))
    assert replacements == [smg_id]
    new_records = list(records(output))
    assert len(new_records) == len(old_records) == 11
    changed_records = [f'{old[1]:08X}' for old, new in zip(old_records, new_records) if old != new]
    assert changed_records == ['01000808']  # TES4 header and all other records preserved.
    by_id = {fid: dict(fields(data)) for kind, fid, flags, data in new_records}
    for name, weapon, source, cartridge in mappings:
        clone_id = 0x01000000 | int(cfg[name]['projectile'].split(':')[1], 16)
        source_parts = dict(originals[source][2])
        clone = by_id[clone_id]
        assert source_parts.keys() == clone.keys()
        for tag, value in source_parts.items():
            if tag not in ('EDID', 'FULL', 'DATA'):
                assert clone[tag] == value, (name, tag)
        original_data, data = source_parts['DATA'], clone['DATA']
        old_flags, new_flags, projectile_type = struct.unpack_from('<H', original_data)[0], *struct.unpack_from('<HH', data)
        gravity, speed = struct.unpack_from('<ff', data, 4)
        p = cfg[name]
        velocity = float(p['maximum_velocity_mps']) * float(p['barrel_in']) / (float(p['barrel_in']) + 2 * float(p['peak_travel_in']))
        assert new_flags == old_flags & ~1 and not new_flags & 0x403
        assert projectile_type == 1 and gravity == 0
        assert abs(speed / (velocity * 70) - 1) < 3e-6
        assert data[2:4] == original_data[2:4] and data[12:] == original_data[12:]
    (PACKET / 'NVOFlightPilot.esp').write_bytes(output)
    (PACKET / 'NVOFlightPreview.ini').write_text(config, encoding='ascii')
    canonical.write_text(config, encoding='ascii')
    audit = dict(packet='3D1',native_plugin_version=311,native_binary_rebuilt=False,
                 base_esm_sha256=sha(GAME/'Data/FalloutNV.esm'),donor_sha256=sha(DONOR),
                 mappings=audits,source_overrides_in_NVO=overrides,records_changed=changed_records,
                 existing_other_records_preserved=10,stock_overrides=0,
                 config_value_changes=changes,esm_modified=False,
                 before_esp_sha256=hashlib.sha256(previous).hexdigest(),after_esp_sha256=hashlib.sha256(output).hexdigest(),
                 smg_source_fields={tag:value.hex() for tag,value in parts},
                 smg_clone_fields={tag:value.hex() for tag,value in new_parts},
                 smg_muzzle_mps=muzzle,gameplay_tested=False)
    write_json(PACKET/'RECORD-AUDIT.json',audit)

    copies={'Data/NVOFlightPilot.esp':PACKET/'NVOFlightPilot.esp',
            'Data/NVSE/Plugins/NVOFlightPreview.ini':PACKET/'NVOFlightPreview.ini'}
    for relative,source in copies.items():
        target=RELEASE/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    previous_plan=json.loads((PREVIOUS/'INSTALL-3D-plan.json').read_text())
    plan={**previous_plan,'packet':'3D1','version':311,'files':[],
          'protected_assets':previous_plan['protected_assets']+['NVOFlightKit.txt'],
          'dependency_preconditions':previous_plan['dependency_preconditions']+[
              dict(path=relative,sha256=previous_hashes[relative]) for relative in
              ('Data/NVSE/Plugins/NVOCombatCore.dll','Data/NVSE/Plugins/NVOCombatCore.pdb',
               'Data/NVSE/Plugins/NVOFlightPhysics.ini')]}
    for relative in copies:
        plan['files'].append(dict(path=relative,action='install',sha256=previous_hashes[relative],
                                 source=str(RELEASE/relative),source_sha256=sha(RELEASE/relative),
                                 log_may_change_until_game_exits=False))
    write_json(PACKET/'INSTALL-3D1-plan.json',plan)
    write_json(RELEASE/'manifest.json',dict(packet='3D1',kind='record and configuration update',
               native_plugin_version=311,native_version='0.3.11',native_binary_rebuilt=False,
               requires_packet='3D',status='Prepared; user gameplay check pending',
               installed_files=[dict(path=r,sha256=sha(RELEASE/r)) for r in copies],
               required_foundation=plan['dependency_preconditions'],damage_replacement=False,
               prior_pistol_checkpoint_accepted=True,assistant_gameplay_tested=False))
    print(json.dumps(dict(packet='3D1',install_files=2,records_changed=changed_records,
                         mapping_checks=len(audits),esp_sha256=sha(PACKET/'NVOFlightPilot.esp'),
                         preview_sha256=sha(PACKET/'NVOFlightPreview.ini'),native_plugin_version=311),indent=2))


if __name__ == '__main__':
    main()
