"""Stage the already-audited 4B pair and two opt-in console test helpers."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'source/combat/step4b'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4B-Guarded-Armour-Snapshot'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

helpers = {
    'NVOArmourKit4B.txt': 'player.additem 000E3778 1\nplayer.additem 0008ED03 100\nplayer.equipitem 000E3778\n',
    'NVOArmourTarget4B.txt': 'unequipallitems\nadditem 00020420 1\nadditem 00020426 1\nequipitem 00020420\nequipitem 00020426\nSetEquippedCurrentHealth 400 2\nSetEquippedCurrentHealth 50 1\nsetav health 2000\nrestoreav health 2000\n',
}
for name, content in helpers.items():
    if (GAME / name).exists():
        raise SystemExit(f'Refuse to replace existing test helper: {name}')
    (RELEASE / name).write_text(content, encoding='ascii')
    (STEP / name).write_text(content, encoding='ascii')

plan = json.loads((ROOT / 'source/combat/step3u1/INSTALL-3U1-plan.json').read_text(encoding='utf-8-sig'))
plan.update(packet='4B', version=326, created='2026-09-16')
expected = {
    'Data/NVSE/Plugins/NVOCombatCore.dll': ('963a6f51f8f3539c66f2503d2615eb6aff2849e7d1eb4911e7467059a5c76fce', '3d5ff40c5c8ba418c0764cba55bd8595cfa1444396f4e814552210524094e13a'),
    'Data/NVSE/Plugins/NVOCombatCore.pdb': ('d39a19ccd39c5d06e36285dbe83168fb8d0982763ae801755424142abdcf96e4', '9411d09fefe2e59fa50a891081592b81fbc9cc50602bee8951a04e706ac8d2a0'),
}
plan['files'] = []
for name in list(expected) + list(helpers):
    src = RELEASE / name
    old = sha(GAME / name) if (GAME / name).exists() else None
    new = sha(src)
    if name in expected and (old, new) != expected[name]:
        raise SystemExit(f'Pinned binary mismatch: {name}')
    plan['files'].append(dict(path=name, action='install', sha256=old, source=str(src), source_sha256=new, log_may_change_until_game_exits=False))
for dep in plan['dependency_preconditions']:
    if dep['path'] in expected:
        dep['sha256'] = expected[dep['path']][0]
    if sha(GAME / dep['path']) != dep['sha256']:
        raise SystemExit(f'Inspected dependency changed: {dep["path"]}')
plan_path = STEP / 'INSTALL-4B-plan.json'
plan_path.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')

script = (ROOT / 'tools/install_combat_3u1.ps1').read_text(encoding='utf-8-sig')
script = script.replace('step3u1', 'step4b').replace('3U1', '4B').replace('325', '326')
script = script.replace('NVO-Combat-Packet-4B-World-Contacts', RELEASE.name)
script = script.replace('644d06f54b6121adc06b69fb9d0f1b8f4b7b6cc9b2b2b827ca34718c22779426', sha(plan_path))
script = script.replace("'Data/NVSE/Plugins/NVOCombatCore.pdb')", "'Data/NVSE/Plugins/NVOCombatCore.pdb', 'NVOArmourKit4B.txt', 'NVOArmourTarget4B.txt')", 1)
script = script.replace('Count -ne 2', 'Count -ne 4').replace('Exactly two unique NVO install files required.', 'Exactly four unique NVO install files required.')
script = script.replace('Only the two named NVO install actions are allowed.', 'Only the four named NVO install actions are allowed.')
(ROOT / 'tools/install_combat_4b.ps1').write_text(script, encoding='utf-8-sig')
print('Prepared 4B install plan: audited DLL/PDB plus two manually invoked console helpers. All 10 dependency hashes match. No game files changed.')
