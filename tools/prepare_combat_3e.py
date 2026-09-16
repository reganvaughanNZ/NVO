"""Append three standard-ammunition flight profiles and private projectiles.

Workspace preparation only. Retains the accepted 3D1 records/configuration and DLL.
"""
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
PACKET = ROOT/'source/combat/step3e'
PREVIOUS = ROOT/'source/combat/step3d1'
RELEASE = ROOT/'release/NVO-Combat-Packet-3E-Update'
GAME = Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas')
DONOR = Path(r'C:/Users/regan/Desktop/NVO Mod References (Open Source)/BallistX-70341-5-4-1712065466.rar')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def main():
    assert not (PACKET/'INSTALL-3E-result.json').exists(), 'Installed preimages must remain immutable.'
    PACKET.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for folder, name in ((ROOT/'source/combat/step3d','INSTALL-3D-result.json'),
                         (PREVIOUS,'INSTALL-3D1-result.json')):
        receipt = json.loads((folder/name).read_text(encoding='utf-8-sig'))
        assert receipt['status'] == 'installed' and receipt['version'] == 311
        hashes.update({r['path']:r['sha256'] for r in receipt['installed']})
    for relative, expected in hashes.items():
        assert sha(GAME/relative) == expected, ('Foundation changed', relative)
    assert sha(PREVIOUS/'NVOFlightPilot.esp') == hashes['Data/NVOFlightPilot.esp']
    assert sha(PREVIOUS/'NVOFlightPreview.ini') == hashes['Data/NVSE/Plugins/NVOFlightPreview.ini']
    assert sha(GAME/'Data/FalloutNV.esm') == '44e654569d47fcf8ceddc576c26dd11a32f207e60b1fd23cd6089e1e5f8fa84b'
    assert sha(DONOR) == 'd71fe28f1262dec7a0f2086f06b243168d74a3f11d8b57cd8b7b8127c9506e3d'

    # Explicit engine source and donor key even where currently equal; never infer calibre from a shared projectile.
    additions = [
        dict(name='10mm-pistol', weapon=0x434F, ammo=0x4241, source=0x2CD5F, cartridge=0x2CD5F, local=0x80A),
        dict(name='357-magnum-revolver', weapon=0x8F216, ammo=0x8ED02, source=0x8F20C, cartridge=0x8F20C, local=0x80B),
        dict(name='44-magnum-revolver', weapon=0x8F215, ammo=0x2937E, source=0x3BF0C, cartridge=0x3BF0C, local=0x80C),
    ]
    original_config = (PREVIOUS/'NVOFlightPreview.ini').read_text(encoding='ascii')
    old_cfg = configparser.ConfigParser()
    old_cfg.read_string(original_config)
    stock_ids = set()
    for section in old_cfg.sections():
        for key in ('weapon','ammo','source_projectile'):
            value = old_cfg[section].get(key,'')
            if value.startswith('FalloutNV.esm:'):
                stock_ids.add(int(value.split(':')[1],16))
    for item in additions:
        stock_ids.update(item[key] for key in ('weapon','ammo','source'))
    base = (GAME/'Data/FalloutNV.esm').read_bytes()
    originals = {fid:(kind,flags,list(fields(payload))) for kind,fid,flags,payload in records(base)
                 if fid in stock_ids or kind == 'FLST'}
    assert stock_ids.issubset(originals)
    overrides = [f'{fid:08X}' for kind,fid,flags,payload in records((GAME/'Data/NVO.esm').read_bytes()) if fid in stock_ids]
    assert not overrides, ('Inspect NVO source-form overrides', overrides)
    tables = {}
    for name in ('WeaponData','CartridgeData'):
        text = subprocess.run(['tar','-xOf',str(DONOR),f'Config/BallistX/Data/{name}.cfg'],
                              capture_output=True,check=True).stdout.decode('cp1252')
        tables[name] = text.replace('\r\r\n','\n').replace('\r\n','\n').splitlines()

    def donor_row(table, fid):
        key = f'@FalloutNV.esm:{fid:06X}'
        found = [(i,line) for i,line in enumerate(tables[table],1)
                 if line.split(';')[0].split() and line.split(';')[0].split()[0] == key]
        assert len(found) == 1, (table,key)
        i,line = found[0]
        return list(map(float,line.split(';')[0].split()[1:])),dict(line=i,text=line)

    previous = (PREVIOUS/'NVOFlightPilot.esp').read_bytes()
    old_records = list(records(previous))
    assert len(old_records) == 11
    groups = {kind:[] for kind in ('WEAP','AMMO','PROJ')}
    for kind,fid,flags,payload in old_records[1:]:
        assert flags == 0 and fid >> 24 == 1
        groups[kind].append(record(kind,fid,payload))
    config = '; Packet 3E. Seven regular standard-ammo profiles and two legacy private profiles.\n' + original_config.split('\n',1)[1]
    audits = []
    for item in additions:
        name,weapon,ammo,source,cartridge,local = (item[k] for k in ('name','weapon','ammo','source','cartridge','local'))
        assert originals[weapon][0] == 'WEAP' and originals[ammo][0] == 'AMMO'
        wp,ap = dict(originals[weapon][2]),dict(originals[ammo][2])
        assert struct.unpack_from('<I',wp['DNAM'],36)[0] == source
        ammo_list = struct.unpack('<I',wp['NAM0'])[0]
        assert originals[ammo_list][0] == 'FLST'
        ammo_members = [struct.unpack('<I',v)[0] for k,v in originals[ammo_list][2] if k == 'LNAM']
        assert ammo in ammo_members
        ammo_projectile = struct.unpack_from('<I',ap['DAT2'],4)[0]
        assert ammo_projectile == 0, 'Ammunition overrides projectile; audit before adding profile.'
        w,wr = donor_row('WeaponData',weapon)
        c,cr = donor_row('CartridgeData',cartridge)
        model,bc,mass,diameter,maximum,peak,temperature,damage = c
        barrel = w[0]
        muzzle = maximum*barrel/(barrel+2*peak)
        assert model in (1,7) and 0.05 <= bc <= 2 and 10 <= muzzle <= 1600
        kind,flags,parts = originals[source]
        assert kind == 'PROJ' and flags == 0
        new_parts = []
        for tag,value in parts:
            new = value
            if tag == 'EDID': new = ('NVOFlight3E'+name.replace('-','')+'Projectile').encode()+b'\0'
            elif tag == 'FULL': new = ('NVO Flight - '+name+' Bullet').encode()+b'\0'
            elif tag == 'DATA':
                assert len(value) == 84 and struct.unpack_from('<H',value,2)[0] == 1
                old_flags = struct.unpack_from('<H',value)[0]
                assert not old_flags & 0x402
                new = bytearray(value)
                struct.pack_into('<H',new,0,old_flags & ~1)
                struct.pack_into('<ff',new,4,0,muzzle*70)
                new = bytes(new)
                assert new[2:4] == value[2:4] and new[12:] == value[12:]
            new_parts.append((tag,new))
        groups['PROJ'].append(record('PROJ',0x01000000|local,b''.join(sub(k,v) for k,v in new_parts)))
        profile = dict(weapon=f'FalloutNV.esm:{weapon:06X}',ammo=f'FalloutNV.esm:{ammo:06X}',
                       source_projectile=f'FalloutNV.esm:{source:06X}',projectile=f'NVOFlightPilot.esp:{local:06X}',
                       select_on_fire=1,flight_enabled=1,drag_model=int(model),ballistic_coefficient=bc,
                       maximum_velocity_mps=maximum,barrel_in=barrel,peak_travel_in=peak)
        config += '\n['+name+']\n'+''.join(f'{k}={v:g}\n' if isinstance(v,(int,float)) else f'{k}={v}\n' for k,v in profile.items())
        audits.append(dict(**item,weapon_name=wp['FULL'].rstrip(b'\0').decode('cp1252'),
                           ammo_name=ap['FULL'].rstrip(b'\0').decode('cp1252'),ammo_list=f'{ammo_list:08X}',
                           ammo_members=[f'{fid:08X}' for fid in ammo_members],ammo_projectile_override=ammo_projectile,
                           weapon_source=wr,cartridge_source=cr,muzzle_mps=muzzle,
                           retained_source_fields={k:v.hex() for k,v in parts},clone_fields={k:v.hex() for k,v in new_parts},
                           unused_donor_damage=damage,profile=profile))
    # Preserve header fields except HEDR count/next ID and description.
    header = []
    for tag,value in fields(old_records[0][3]):
        if tag == 'HEDR':
            assert struct.unpack_from('<II',value,4) == (13,0x80A)
            value = value[:4]+struct.pack('<II',16,0x80D)
        elif tag == 'SNAM': value = b'3E explicit standard-ammo projectile profiles. No stock overrides.\0'
        header.append(sub(tag,value))
    output = record('TES4',0,b''.join(header))
    for kind,items in groups.items():
        body = b''.join(items)
        output += struct.pack('<4sI4sIII',b'GRUP',24+len(body),kind.encode(),0,0,0)+body
    parsed = list(records(output))
    assert len(parsed) == 14 and len({fid for kind,fid,flags,payload in parsed}) == 14
    by_id = {fid:(kind,flags,payload) for kind,fid,flags,payload in parsed}
    assert all(by_id[fid] == (kind,flags,payload) for kind,fid,flags,payload in old_records[1:])
    for kind,fid,flags,payload in old_records[1:]:
        old_bytes = record(kind,fid,payload)
        assert previous.count(old_bytes) == output.count(old_bytes) == 1, 'Complete old record bytes changed.'
    assert set(by_id)-{row[1] for row in old_records} == {0x0100080A,0x0100080B,0x0100080C}
    assert all(flags == 0 for kind,fid,flags,payload in parsed)
    cfg = configparser.ConfigParser();cfg.read_string(config)
    assert all(dict(cfg[name]) == dict(old_cfg[name]) for name in old_cfg.sections())
    assert len(cfg.sections())-1 == 9 and len(config.encode('ascii')) < 16384
    graph_checks = []
    for name in cfg.sections():
        if name == 'Preview': continue
        p = cfg[name]
        if p['select_on_fire'] != '1': continue
        weapon,ammo,source = (int(p[key].split(':')[1],16) for key in ('weapon','ammo','source_projectile'))
        assert struct.unpack_from('<I',dict(originals[weapon][2])['DNAM'],36)[0] == source
        private = 0x01000000|int(p['projectile'].split(':')[1],16)
        src = dict(originals[source][2]);clone = dict(fields(by_id[private][2]))
        assert clone.keys() == src.keys()
        assert all(clone[tag] == value for tag,value in src.items() if tag not in ('EDID','FULL','DATA'))
        a,b = src['DATA'],clone['DATA'];old_flags,new_flags = struct.unpack_from('<H',a)[0],struct.unpack_from('<H',b)[0]
        gravity,speed = struct.unpack_from('<ff',b,4)
        expected = float(p['maximum_velocity_mps'])*float(p['barrel_in'])/(float(p['barrel_in'])+2*float(p['peak_travel_in']))*70
        assert len(a) == len(b) == 84 and b[2:4] == a[2:4] == b'\x01\x00' and b[12:] == a[12:]
        assert not new_flags & 0x403 and new_flags == old_flags & ~1 and gravity == 0 and abs(speed/expected-1) < 3e-6
        graph_checks.append(dict(profile=name,source=f'{source:08X}',private=f'{private:08X}',weapon_projectile_verified=True,clone_verified=True))
    assert len(graph_checks) == 7
    canonical = ROOT/'native/NVOCombatCore/config/NVOFlightPreview.ini'
    assert canonical.read_text(encoding='ascii') in (original_config,config)
    (PACKET/'NVOFlightPilot.esp').write_bytes(output)
    (PACKET/'NVOFlightPreview.ini').write_text(config,encoding='ascii')
    canonical.write_text(config,encoding='ascii')
    kit = ''.join(f'player.additem {row["weapon"]:08X} 1\r\n' for row in additions)
    kit += ''.join(f'player.additem {row["ammo"]:08X} 100\r\n' for row in additions)
    (PACKET/'NVOFlightKit3E.txt').write_bytes(kit.encode('ascii'))
    write_json(PACKET/'RECORD-AUDIT.json',dict(packet='3E',native_plugin_version=311,native_rebuilt=False,
               base_esm_sha256=sha(GAME/'Data/FalloutNV.esm'),donor_sha256=sha(DONOR),additions=audits,
               all_seven_regular_profiles_checked=graph_checks,previous_ten_private_records_preserved=True,
               previous_six_profiles_preserved=True,total_profiles=9,source_overrides_in_NVO=overrides,
               stock_overrides=0,damage_replacement=False,gameplay_tested=False))
    copies = {'Data/NVOFlightPilot.esp':PACKET/'NVOFlightPilot.esp',
              'Data/NVSE/Plugins/NVOFlightPreview.ini':PACKET/'NVOFlightPreview.ini',
              'NVOFlightKit3E.txt':PACKET/'NVOFlightKit3E.txt'}
    for relative,source in copies.items():
        target = RELEASE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    plan = json.loads((PREVIOUS/'INSTALL-3D1-plan.json').read_text())
    plan.update(packet='3E',files=[])
    for relative in copies:
        target = GAME/relative
        assert relative in hashes or not target.exists(), ('Unexpected existing kit', relative)
        plan['files'].append(dict(path=relative,action='install',sha256=sha(target) if target.exists() else None,
                                 source=str(RELEASE/relative),source_sha256=sha(RELEASE/relative),log_may_change_until_game_exits=False))
    write_json(PACKET/'INSTALL-3E-plan.json',plan)
    write_json(RELEASE/'manifest.json',dict(packet='3E',kind='record and configuration update',native_plugin_version=311,
               native_version='0.3.11',native_rebuilt=False,requires_packet='3D1',status='Prepared; user gameplay check pending',
               installed_files=[dict(path=r,sha256=sha(RELEASE/r)) for r in copies],required_foundation=plan['dependency_preconditions'],
               new_regular_profiles=3,total_profiles=9,damage_replacement=False,assistant_gameplay_tested=False))
    print(json.dumps(dict(packet='3E',install_files=3,profiles=9,mapping_checks=7,
                         new_muzzle_mps={a['name']:a['muzzle_mps'] for a in audits},
                         installed_files=[dict(path=r,sha256=sha(RELEASE/r)) for r in copies]),indent=2))


if __name__ == '__main__':
    main()
