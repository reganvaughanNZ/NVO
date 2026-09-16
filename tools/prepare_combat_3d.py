"""Prepare four private projectile bases and explicit stock-weapon profiles.
No stock record overrides and no writes to the game installation.
"""
from pathlib import Path
import hashlib, json, struct, subprocess
from inspect_plugin import records, fields
from prepare_combat_3b2 import sub, record

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'source/combat/step3d'
PROJECT = ROOT/'native/NVOCombatCore'
GAME = Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas/Data')
DONOR = Path(r'C:/Users/regan/Desktop/NVO Mod References (Open Source)/BallistX-70341-5-4-1712065466.rar')

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    base = (GAME/'FalloutNV.esm').read_bytes()
    assert hashlib.sha256(base).hexdigest() == '44e654569d47fcf8ceddc576c26dd11a32f207e60b1fd23cd6089e1e5f8fa84b'
    assert hashlib.sha256(DONOR.read_bytes()).hexdigest() == 'd71fe28f1262dec7a0f2086f06b243168d74a3f11d8b57cd8b7b8127c9506e3d'
    tables = {}
    for name in ('WeaponData', 'CartridgeData'):
        data = subprocess.run(['tar','-xOf',str(DONOR),f'Config/BallistX/Data/{name}.cfg'], capture_output=True, check=True).stdout
        tables[name] = data.decode('cp1252').replace('\r\r\n','\n').replace('\r\n','\n').splitlines()
    def donor_row(table, fid):
        found = [(i, line) for i, line in enumerate(tables[table],1) if line.split(';')[0].split() and line.split(';')[0].split()[0] == f'@FalloutNV.esm:{fid:06X}']
        assert len(found) == 1
        return [float(v) for v in found[0][1].split(';')[0].split()[1:]], dict(line=found[0][0], text=found[0][1])
    combinations = [('9mm-pistol',0xE3778,0x8ED03,0x8F20F,0x806),
                    ('hunting-rifle',0x4333,0x6B53C,0x8F20A,0x807),
                    ('9mm-smg',0x8F217,0x8ED03,0x8F20F,0x808),
                    ('service-rifle',0xE9C3B,0x4240,0x426D,0x809)]
    wanted = {n for row in combinations for n in row[1:4]}
    originals = {fid:(kind,flags,list(fields(data))) for kind,fid,flags,data in records(base) if fid in wanted}
    # Current NVO does not override the projectile records copied for this packet.
    assert not any(fid in {row[3] for row in combinations} for kind,fid,flags,data in records((GAME/'NVO.esm').read_bytes()))
    previous = (ROOT/'source/combat/step3b2/NVOFlightPilot.esp').read_bytes()
    assert (GAME/'NVOFlightPilot.esp').read_bytes() == previous, 'Installed pilot records changed; inspect before extending.'
    groups = {kind:[] for kind in ('WEAP','AMMO','PROJ')}
    for kind,fid,flags,data in records(previous):
        if kind != 'TES4':
            assert flags == 0
            groups[kind].append(record(kind,fid,data))
    audit, profiles = [], []
    for label,weapon,ammo,proj,local in combinations:
        assert originals[weapon][0] == 'WEAP' and originals[ammo][0] == 'AMMO'
        w, wr = donor_row('WeaponData',weapon)
        c, cr = donor_row('CartridgeData',proj)
        model,bc,mass,diameter,maximum,peak,temperature,damage = c
        barrel = w[0]; muzzle = maximum*barrel/(barrel+2*peak)
        kind,flags,parts = originals[proj]
        assert kind == 'PROJ' and flags == 0
        changed, new = [], []
        for tag,value in parts:
            out = value
            if tag == 'EDID': out = ('NVOFlight3D'+label.replace('-','')+'Projectile').encode()+b'\0'
            elif tag == 'FULL': out = ('NVO Flight - '+label+' Bullet').encode()+b'\0'
            elif tag == 'DATA':
                assert len(value)==84 and struct.unpack_from('<H',value,2)[0] == 1
                out = bytearray(value)
                assert not (struct.unpack_from('<H',out)[0] & 0x402), 'Explosive/detonating projectile is outside scope'
                struct.pack_into('<H',out,0,struct.unpack_from('<H',value)[0]&~1)
                struct.pack_into('<ff',out,4,0,muzzle*70)
                out=bytes(out)
                assert out[12:]==value[12:]
            if out!=value: changed.append(dict(tag=tag,before=value.hex(),after=out.hex()))
            new.append((tag,out))
        assert {item['tag'] for item in changed} == {'EDID','FULL','DATA'}
        groups['PROJ'].append(record('PROJ',0x01000000|local,b''.join(sub(k,v) for k,v in new)))
        profiles.append(dict(name=label,weapon=f'FalloutNV.esm:{weapon:06X}',ammo=f'FalloutNV.esm:{ammo:06X}',
            source_projectile=f'FalloutNV.esm:{proj:06X}',projectile=f'NVOFlightPilot.esp:{local:06X}',
            select_on_fire=1,flight_enabled=1,drag_model=int(model),ballistic_coefficient=bc,
            maximum_velocity_mps=maximum,barrel_in=barrel,peak_travel_in=peak))
        audit.append(dict(name=label,weapon_name=dict(originals[weapon][2])['FULL'].rstrip(b'\0').decode('cp1252'),
            weapon_source=wr,cartridge_source=cr,modified_subrecords=changed,muzzle_mps=muzzle,
            cartridge_mass_grain=mass,diameter_in=diameter,unused_donor_damage=damage))
    # Preserve all six previous records byte-for-byte, only extend the PROJ group.
    header = b''.join([sub('HEDR',struct.pack('<fII',1.34,13,0x80A)),sub('CNAM',b'NVO\0'),
        sub('SNAM',b'3D private projectile bases selected per shot. No stock overrides.\0'),
        sub('MAST',b'FalloutNV.esm\0'),sub('DATA',struct.pack('<Q',len(base)))])
    output = record('TES4',0,header)
    for kind,items in groups.items():
        body=b''.join(items)
        output+=struct.pack('<4sI4sIII',b'GRUP',24+len(body),kind.encode(),0,0,0)+body
    parsed=list(records(output)); old=list(records(previous))
    assert len(parsed)==11 and all(fid>>24==1 for kind,fid,flags,data in parsed[1:])
    byid={fid:(kind,flags,data) for kind,fid,flags,data in parsed}
    assert all(byid[fid]==(kind,flags,data) for kind,fid,flags,data in old[1:])
    (DEST/'NVOFlightPilot.esp').write_bytes(output)
    # Prior private weapons retain their own ammo/projectile forms and profiles.
    for source,localw,locala,localp in [(profiles[0],0x800,0x802,0x804),(profiles[1],0x801,0x803,0x805)]:
        p=dict(source);p.update(name='pilot-'+source['name'],weapon=f'NVOFlightPilot.esp:{localw:06X}',
            ammo=f'NVOFlightPilot.esp:{locala:06X}',projectile=f'NVOFlightPilot.esp:{localp:06X}',
            source_projectile=f'NVOFlightPilot.esp:{localp:06X}',select_on_fire=0)
        profiles.append(p)
    config='; Packet 3D. Explicit per-shot profiles. BallistX donor tuning, fixed atmosphere.\n[Preview]\nschema=2\nenabled=1\ndonor_units_per_metre=70\nmax_matches=32\n'
    for p in profiles:
        config+='\n['+p['name']+']\n'+''.join(f'{k}={v:g}\n' if isinstance(v,(int,float)) else f'{k}={v}\n' for k,v in p.items() if k!='name')
    for path in (DEST/'NVOFlightPreview.ini',PROJECT/'config/NVOFlightPreview.ini'): path.write_text(config,encoding='ascii')
    physics='; Packet 3D. Drag model and coefficient belong to each flight profile.\n[Physics]\nschema=2\nenabled=1\nunits_per_metre=70\ngravity_mps2=9.80665\nair_density_kg_m3=1.225\nspeed_of_sound_mps=340.294\n'
    for path in (DEST/'NVOFlightPhysics.ini',PROJECT/'config/NVOFlightPhysics.ini'): path.write_text(physics,encoding='ascii')
    kit=''.join(f'player.additem {w:08X} 1\r\n' for _,w,_,_,_ in combinations)
    kit+=''.join(f'player.additem {a:08X} {count}\r\n' for a,count in [(0x8ED03,300),(0x6B53C,100),(0x4240,200)])
    (DEST/'NVOFlightKit.txt').write_bytes(kit.encode('ascii'))
    report=dict(packet='3D',version=311,profiles=profiles,audit=audit,private_projectiles_added=4,stock_overrides=0,
        previous_six_records_preserved=True,esm_modified=False,esp_sha256=hashlib.sha256(output).hexdigest(),
        donor_archive_sha256=hashlib.sha256(DONOR.read_bytes()).hexdigest(),
        ammo_form_ids=['FalloutNV.esm:08ED03','FalloutNV.esm:06B53C','FalloutNV.esm:004240'])
    (DEST/'RECORD-AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(esp_sha256=report['esp_sha256'],profiles=len(profiles),stock_overrides=0,kit=kit),indent=2))

if __name__=='__main__':main()
