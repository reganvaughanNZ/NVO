from pathlib import Path
import json
from inspect_plugin import records, fields

game = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
for kind, form, flags, payload in records((game/'Data/FalloutNV.esm').read_bytes()):
    if kind not in ('ARMO', 'NPC_', 'CREA', 'WEAP', 'AMMO'):
        continue
    parts = dict(fields(payload))
    edid = parts.get('EDID', b'').rstrip(b'\0').decode('cp1252')
    full = parts.get('FULL', b'').rstrip(b'\0').decode('cp1252')
    chosen = form in (0x20420,0x20426,0xE3778,0x8F217,0xA54FF) or edid in ('ArmorCombat','ArmorCombatHelmet','WeapNV9mmPistol','WeapNV9mmSMG','Ammo9mm')
    chosen |= kind == 'NPC_' and ('ncrtrooper' in edid.lower() or 'test' in edid.lower())
    chosen |= kind == 'CREA' and 'bloatfly' in edid.lower()
    if chosen:
        print(json.dumps({'type':kind,'id':f'{form:08X}','edid':edid,'name':full,'DATA':parts.get('DATA',b'').hex(),'BMDT':parts.get('BMDT',b'').hex(),'ACBS':parts.get('ACBS',b'').hex(),'SCRI':parts.get('SCRI',b'').hex(),'TPLT':parts.get('TPLT',b'').hex()}))
