"""Prepare the .308 standard/AP/HP identity checkpoint; no game writes or execution."""
from pathlib import Path
import configparser
import hashlib
import json
import shutil
import struct
import subprocess

from inspect_plugin import records, fields
from prepare_combat_3b2 import sub, record

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'source/combat/step3f'
PREVIOUS = ROOT/'source/combat/step3e'
RELEASE = ROOT/'release/NVO-Combat-Packet-3F-Update'
GAME = Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
DONOR = Path(r'C:/Users/regan/Desktop/NVO Mod References (Open Source)/BallistX-70341-5-4-1712065466.rar')
JIP_FORMS = Path(r'C:/Users/regan/Desktop/NVO Mod References (Open Source)/JIP-LN-NVSE-main/nvse/GameForms.h')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')

def main():
    assert not (PACKET/'INSTALL-3F-result.json').exists(), 'Preserve installed transaction records.'
    assert (PREVIOUS/'CHECKPOINT-ACCEPTED.md').is_file(), 'Requires accepted 3E.'
    PACKET.mkdir(parents=True, exist_ok=True)
    previous_receipt = json.loads((PREVIOUS/'INSTALL-3E-result.json').read_text(encoding='utf-8-sig'))
    assert previous_receipt['status'] == 'installed' and previous_receipt['version'] == 311
    for row in previous_receipt['installed']:
        assert sha(GAME/row['path']) == row['sha256'], ('Installed 3E changed', row['path'])
    plan = json.loads((PREVIOUS/'INSTALL-3E-plan.json').read_text())
    for row in plan['dependency_preconditions']:
        assert sha(GAME/row['path']) == row['sha256'], ('Foundation changed', row['path'])
    assert sha(GAME/'Data/FalloutNV.esm') == '44e654569d47fcf8ceddc576c26dd11a32f207e60b1fd23cd6089e1e5f8fa84b'
    assert sha(DONOR) == 'd71fe28f1262dec7a0f2086f06b243168d74a3f11d8b57cd8b7b8127c9506e3d'
    assert sha(PREVIOUS/'NVOFlightPilot.esp') == sha(GAME/'Data/NVOFlightPilot.esp')
    assert sha(PREVIOUS/'NVOFlightPreview.ini') == sha(GAME/'Data/NVSE/Plugins/NVOFlightPreview.ini')

    weapon, source, standard, ap, hp, ammo_list = 0x4333, 0x8F20A, 0x6B53C, 0x13E442, 0x13E443, 0x1537E9
    expected_effects = {
        standard: {},
        ap: {0x160C6A: (2, 2, 15.0), 0x1582E7: (0, 1, 0.949999988079071)},
        hp: {0x157B56: (2, 1, 3.0), 0x157B54: (0, 1, 1.75)},
    }
    wanted = {weapon, source, standard, ap, hp, ammo_list} | set(expected_effects[ap]) | set(expected_effects[hp])
    stock = {fid:(kind, flags, list(fields(payload)))
             for kind,fid,flags,payload in records((GAME/'Data/FalloutNV.esm').read_bytes()) if fid in wanted}
    assert set(stock) == wanted
    wp = dict(stock[weapon][2])
    assert stock[weapon][0] == 'WEAP' and stock[ammo_list][0] == 'FLST'
    assert struct.unpack_from('<I', wp['DNAM'], 36)[0] == source
    assert struct.unpack('<I', wp['NAM0'])[0] == ammo_list
    members = [struct.unpack('<I', v)[0] for t,v in stock[ammo_list][2] if t == 'LNAM']
    assert {standard, ap, hp}.issubset(members)
    ammo_audit = []
    for ammo in (standard, ap, hp):
        kind, flags, parts = stock[ammo]
        d = dict(parts)
        assert kind == 'AMMO' and flags == 0
        assert struct.unpack_from('<f', d['DATA'])[0] == 1.0
        assert d['DATA'][4] == 0  # No ignore-resistance or non-playable ammo flags.
        assert struct.unpack_from('<II', d['DAT2']) == (0, 0)  # Default shot count, no projectile override.
        effects = [struct.unpack('<I', v)[0] for t,v in parts if t == 'RCIL']
        assert set(effects) == set(expected_effects[ammo]) and len(effects) == len(set(effects))
        decoded = []
        for effect in effects:
            ek, ef, ep = stock[effect]
            ed = dict(ep)
            assert ek == 'AMEF' and ef == 0 and len(ed['DATA']) == 12
            values = struct.unpack('<IIf', ed['DATA'])
            assert values == expected_effects[ammo][effect]
            decoded.append(dict(form=f'{effect:08X}',editor_id=ed['EDID'].rstrip(b'\0').decode(),
                                effect_type=values[0],operation=values[1],value=values[2]))
        ammo_audit.append(dict(form=f'{ammo:08X}',name=d['FULL'].rstrip(b'\0').decode(),speed_multiplier=1,
                               projectile_override=0,projectiles_per_shot_field=0,effects=decoded,
                               raw_fields={k:v.hex() for k,v in parts}))
    # Check all retained non-base plugins, not merely the currently edited NVO master.
    plugin_audit = []
    for path in sorted((GAME/'Data').iterdir()):
        if path.suffix.lower() not in ('.esm','.esp') or path.name.lower() == 'falloutnv.esm': continue
        rr = list(records(path.read_bytes()))
        masters = [v.rstrip(b'\0').decode() for t,v in fields(rr[0][3]) if t == 'MAST']
        assert masters and masters[0].lower() == 'falloutnv.esm', ('Audit master indices', path.name)
        conflicts = [f'{fid:08X}' for k,fid,fl,b in rr[1:] if fid in wanted]
        assert not conflicts, ('Inspect override before supporting these rounds', path.name, conflicts)
        plugin_audit.append(dict(plugin=path.name,sha256=sha(path),relevant_overrides=conflicts))

    cfg_text = (PREVIOUS/'NVOFlightPreview.ini').read_text(encoding='ascii')
    old_cfg = configparser.ConfigParser(); old_cfg.read_string(cfg_text)
    base_profile = dict(old_cfg['hunting-rifle'])
    assert base_profile['ammo'] == 'FalloutNV.esm:06B53C' and base_profile['projectile'] == 'NVOFlightPilot.esp:000807'
    donor_rows = {}
    for table, key in (('WeaponData', '@FalloutNV.esm:004333'), ('CartridgeData', '@FalloutNV.esm:08F20A')):
        data = subprocess.run(['tar','-xOf',str(DONOR),f'Config/BallistX/Data/{table}.cfg'],capture_output=True,check=True).stdout.decode('cp1252')
        rows = [(i, line) for i,line in enumerate(data.replace('\r\r\n','\n').replace('\r\n','\n').splitlines(),1)
                if line.split(';')[0].split() and line.split(';')[0].split()[0] == key]
        assert len(rows) == 1
        i, line = rows[0]
        donor_rows[table] = dict(line=i,text=line,values=list(map(float,line.split(';')[0].split()[1:])))
    assert donor_rows['WeaponData']['values'][0] == float(base_profile['barrel_in']) == 22
    donor_c = donor_rows['CartridgeData']['values']
    assert donor_c[:2] == [7,0.209] and donor_c[4:6] == [1012,2.1]
    muzzle = 1012 * 22 / (22 + 2 * 2.1)
    previous = (PREVIOUS/'NVOFlightPilot.esp').read_bytes()
    old_records = list(records(previous))
    assert len(old_records) == 14
    groups = {k:[] for k in ('WEAP','AMMO','PROJ')}
    for kind,fid,flags,payload in old_records[1:]:
        assert flags == 0 and fid >> 24 == 1
        groups[kind].append(record(kind,fid,payload))
    additions = [('hunting-rifle-ap', ap, 0x80D), ('hunting-rifle-hp', hp, 0x80E)]
    clone_audit = []
    config = '; Packet 3F. Exact .308 AP/HP identity profiles; shared baseline flight tuning.\n' + cfg_text.split('\n',1)[1]
    config += '\n; AP/HP retain the accepted standard .308 velocity/drag for this identity checkpoint.\n; No inference of variant-specific real-world ballistics or NVO damage/penetration.\n'
    for name, ammo, local in additions:
        assert stock[source][0] == 'PROJ' and stock[source][1] == 0
        new_parts = []
        for tag, value in stock[source][2]:
            new = value
            if tag == 'EDID': new = ('NVOFlight3F'+name.replace('-','')+'Projectile').encode()+b'\0'
            elif tag == 'FULL': new = ('NVO Flight - .308 '+name[-2:].upper()+' Bullet').encode()+b'\0'
            elif tag == 'DATA':
                assert len(value) == 84 and struct.unpack_from('<H',value,2)[0] == 1
                flags = struct.unpack_from('<H',value)[0]; assert not flags & 0x402
                new = bytearray(value)
                struct.pack_into('<H',new,0,flags & ~1)
                struct.pack_into('<ff',new,4,0,muzzle*70)
                new = bytes(new)
                assert new[2:4] == value[2:4] and new[12:] == value[12:]
            new_parts.append((tag,new))
        groups['PROJ'].append(record('PROJ',0x01000000|local,b''.join(sub(k,v) for k,v in new_parts)))
        profile = dict(base_profile, ammo=f'FalloutNV.esm:{ammo:06X}',projectile=f'NVOFlightPilot.esp:{local:06X}')
        config += '\n['+name+']\n'+''.join(f'{k}={v}\n' for k,v in profile.items())
        clone_audit.append(dict(profile=name,ammo=f'{ammo:08X}',private=f'0100{local:04X}',
                                fields={t:v.hex() for t,v in new_parts},configuration=profile))
    header = []
    for tag, value in fields(old_records[0][3]):
        if tag == 'HEDR':
            assert struct.unpack_from('<II',value,4) == (16,0x80D)
            value = value[:4]+struct.pack('<II',18,0x80F)
        elif tag == 'SNAM': value = b'3F exact .308 AP/HP selection. Shared baseline flight tuning. No stock overrides.\0'
        header.append(sub(tag,value))
    output = record('TES4',0,b''.join(header))
    for kind, rows in groups.items():
        body = b''.join(rows)
        output += struct.pack('<4sI4sIII',b'GRUP',24+len(body),kind.encode(),0,0,0)+body
    parsed = list(records(output)); by_id = {fid:(k,fl,p) for k,fid,fl,p in parsed}
    assert len(parsed) == len(by_id) == 16
    for k,fid,fl,p in old_records[1:]:
        assert by_id[fid] == (k,fl,p)
        assert previous.count(record(k,fid,p)) == output.count(record(k,fid,p)) == 1
    assert set(by_id)-{fid for k,fid,fl,p in old_records} == {0x0100080D,0x0100080E}
    cfg = configparser.ConfigParser(); cfg.read_string(config)
    assert list(cfg.sections())[:len(old_cfg.sections())] == old_cfg.sections()
    assert all(dict(cfg[s]) == dict(old_cfg[s]) for s in old_cfg.sections())
    assert len(cfg.sections())-1 == 11 and len(config.encode('ascii')) < 16384
    seen = set()
    for name in cfg.sections():
        if name == 'Preview': continue
        p = cfg[name]
        if p['select_on_fire'] == '1':
            match = tuple(p[k].lower() for k in ('weapon','ammo','source_projectile'))
            assert match not in seen; seen.add(match)
        if name.startswith('hunting-rifle'):
            d = dict(fields(by_id[0x01000000|int(p['projectile'].split(':')[1],16)][2]))
            src = dict(stock[source][2])
            assert d.keys() == src.keys()
            assert all(d[k] == v for k,v in src.items() if k not in ('EDID','FULL','DATA'))
            a,b = src['DATA'],d['DATA']
            assert b[2:4] == a[2:4] and b[12:] == a[12:]
            assert struct.unpack_from('<H',b)[0] == struct.unpack_from('<H',a)[0] & ~1
            gravity,speed = struct.unpack_from('<ff',b,4)
            assert gravity == 0 and abs(speed/(muzzle*70)-1) < 3e-6
    canonical = ROOT/'native/NVOCombatCore/config/NVOFlightPreview.ini'
    assert canonical.read_text(encoding='ascii') in (cfg_text,config)
    (PACKET/'NVOFlightPilot.esp').write_bytes(output)
    (PACKET/'NVOFlightPreview.ini').write_text(config,encoding='ascii')
    canonical.write_text(config,encoding='ascii')
    kit = 'player.additem 00004333 1\r\n'+''.join(f'player.additem {a:08X} 40\r\n' for a in (standard,ap,hp))
    (PACKET/'NVOFlightKit3F.txt').write_bytes(kit.encode('ascii'))
    unchanged = []
    for directory in ('src','include'):
        for path in sorted((ROOT/'native/NVOCombatCore'/directory).iterdir()):
            if path.is_file():
                prior = ROOT/'release/NVO-Combat-Packet-3D-Compiled/Source/NVOCombatCore'/directory/path.name
                assert sha(path) == sha(prior), ('Native source changed', path)
                unchanged.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    assert len(unchanged) == 18
    write_json(PACKET/'RECORD-AUDIT.json',dict(packet='3F',native_plugin_version=311,
        base_esm_sha256=sha(GAME/'Data/FalloutNV.esm'),donor_sha256=sha(DONOR),donor_rows=donor_rows,
        donor_policy='All three .308 profiles deliberately share the accepted standard flight inputs for an identity checkpoint. No AP/HP ballistic equivalence claim. Donor variant conversions are not imported.',
        weapon=f'{weapon:08X}',source_projectile=f'{source:08X}',ammo_list=f'{ammo_list:08X}',ammo_members=[f'{i:08X}' for i in members],
        ammo_audit=ammo_audit,clone_audit=clone_audit,other_plugin_audit=plugin_audit,
        jit_effect_enum_source=dict(path=str(JIP_FORMS),sha256=sha(JIP_FORMS),lines='2907-2988'),
        native_selector_source=dict(path='native/NVOCombatCore/src/FlightPreview.cpp',sha256=sha(ROOT/'native/NVOCombatCore/src/FlightPreview.cpp'),
                                   detail='Existing exact weapon + equipped ammo + original projectile selector; creation independently checks weapon + ammo + private base.'),
        muzzle_mps=muzzle,old_private_records_preserved=13,old_profiles_preserved=9,profile_count=11,
        stock_overrides=0,damage_replacement=False,gameplay_tested=False))
    write_json(PACKET/'STATIC-CHECKS.json',dict(native_source_files_unchanged=unchanged,native_build_executed=False,
        gameplay_tested=False,profile_capacity=16,profile_count=11,config_bytes=len(config.encode('ascii')),
        unique_selection_keys=True,three_hunting_rifle_clones_checked=True,ammo_effects_unchanged=True,
        previous_thirteen_complete_records_preserved=True,previous_nine_profiles_preserved=True))
    copies = {'Data/NVOFlightPilot.esp':PACKET/'NVOFlightPilot.esp',
              'Data/NVSE/Plugins/NVOFlightPreview.ini':PACKET/'NVOFlightPreview.ini',
              'NVOFlightKit3F.txt':PACKET/'NVOFlightKit3F.txt'}
    plan.update(packet='3F',files=[])
    plan['protected_assets'] = list(dict.fromkeys(plan['protected_assets']+['NVOFlightKit3E.txt','Data/RD.esm']))
    for relative, src in copies.items():
        dest = RELEASE/relative; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)
        assert relative != 'NVOFlightKit3F.txt' or not (GAME/relative).exists(), 'Unexpected kit preimage.'
        plan['files'].append(dict(path=relative,action='install',sha256=sha(GAME/relative) if (GAME/relative).exists() else None,
                                 source=str(dest),source_sha256=sha(dest),log_may_change_until_game_exits=False))
    write_json(PACKET/'INSTALL-3F-plan.json',plan)
    write_json(RELEASE/'manifest.json',dict(packet='3F',kind='record and configuration update',native_plugin_version=311,
        native_version='0.3.11',native_rebuilt=False,requires_packet='3E',status='Prepared; user gameplay check pending',
        installed_files=[dict(path=r,sha256=sha(RELEASE/r)) for r in copies],required_foundation=plan['dependency_preconditions'],
        new_ammo_profiles=2,total_profiles=11,damage_replacement=False,assistant_gameplay_tested=False))
    print(json.dumps(dict(packet='3F',profiles=11,new_private_records=2,muzzle_mps=muzzle,
                         ammo_ids=[f'{a:08X}' for a in (standard,ap,hp)],native_unchanged=len(unchanged)),indent=2))

if __name__ == '__main__':
    main()
