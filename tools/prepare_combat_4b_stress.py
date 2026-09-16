"""Prepare optional user-run stress fixtures; no game or native-code writes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'source/combat/step4b/stress'
RELEASE = ROOT / 'release/NVO-Combat-Packet-4B-Stress-Check'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path, obj): path.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
RELEASE.mkdir(exist_ok=True)
approved = '''Crutch TeddyBear01 MotorcycleGasTank PilotLight MotorcycleHandbrake
LeafBlower FirehoseNozzle Conductor NukaColaBottle TinCan01 Turpentine AbraxoCleaner
Lunchbox CherryBomb SensorModule WonderGlue DeathclawHand LeatherBelt MedicalBrace
PaintGun RadscorpionPoisonGland ToyCar SurgicalTubing SteamGaugeAssembly PressureCooker
SurgicalBonesaw01 SurgicalScissors01 SurgicalScalpel01 SurgicalTweasers01 SurgicalForceps01
SurgicalSyringe01 Clipboard01 Clipboard04 Clipboard03 Clipboard02 BigPot Plate04 CoffeeKettle
LawnmowerBlade NukaTruck Baseball01 Basketball BaseballGlove PoolBall pool2ball pool5ball
pool8ball pool10ball pool13ball poolcueball poolTriangle SpareParts FissionBattery Ashtray
SkullBrahmin Camera PrewarMoney CigaretteCarton CigarettePack CoffeeMug01 BoardCutting
BoxDetergent BowlDog Fork01 GnomeGarden DrinkingGlass01 Iron PanCookingMetal Paperweight
PlateDinnerCeramic Plunger PotCookingMetal Rake ShotGlass01 Spatula01 Spoon01 MedicalBraceNew
HotPlate Cigarette01 DinnerPlate01 DrinkingGlass02 GardenGnome01 GardenGnomeDestroyed01
GlassPitcher01 Hammer01 Harmonica01 Knife01 Knife02 Milkbottle01 Pencil01 Plate01 Plate02
Plate03 SpoonBig01 Spork01 TinCan02 WhetStone01 ScotchBottle01Empty01 WhiskeyBottle01Empty01
Wrench01 Opthalmoscope Flour WoodChipper PreWarBook ToasterPostwar ToasterPrewar Chessboard
SodaBottleEmpty01 BurnedBook02 BurnedBook03 BurnedBook04 BurnedBook05 BurnedBook06 BurnedBook07
BurnedBook08 BurnedBook01 BookGeneric01 JournalGeneric DinoToy DeathclawEggNV MantisLeg
BookGeneric03b BookGeneric04b BookGeneric05b BookGeneric06b BookGeneric07b BookGeneric08b
BookGeneric02b SSBottleEmpty JetEmpty DrainedSmallEnergyCell'''.split()
by_edid = {row['edid']: row for row in json.loads((STEP / 'CANDIDATE-ITEMS.json').read_text())}
assert len(approved) >= 128 and len(set(approved)) == len(approved)
selected = [by_edid[name] for name in approved[:128]]
assert len({row['form'] for row in selected}) == 128
helpers = {
    'NVOStressKit4B.txt': 'player.additem 0008F217 1\nplayer.additem 0008ED03 300\nplayer.equipitem 0008F217\n',
    'NVOStressTarget4B.txt':
        'unequipallitems\nadditem 00020420 1\nadditem 00020426 1\nequipitem 00020420\nequipitem 00020426\n'
        'SetEquippedCurrentHealth 400 2\nSetEquippedCurrentHealth 50 1\nsetav health 100000\nrestoreav health 100000\n'
        + ''.join(f'additem {row["form"]} 1\n' for row in selected),
}
receipt = json.loads((ROOT / 'source/combat/step4b/INSTALL-4B-result.json').read_text(encoding='utf-8-sig'))
old_plan = json.loads((ROOT / 'source/combat/step4b/INSTALL-4B-plan.json').read_text())
protected = {row['path']: row['sha256'] for row in old_plan['dependency_preconditions']}
protected.update({row['path']: row['sha256'] for row in receipt['installed']})
assert all(sha(GAME / name) == digest for name, digest in protected.items())
rows = []
for name, content in helpers.items():
    assert not (GAME / name).exists(), f'New test helper already exists: {name}'
    for base in (STEP, RELEASE):
        (base / name).write_text(content, encoding='ascii')
    rows.append(dict(path=name, source=str(RELEASE / name), sha256=sha(RELEASE / name)))
plan = dict(packet='4B-stress', native_version=326, game_root=str(GAME), files=rows,
            protected=protected, no_native_changes=True, damage_replacement=False)
dump(STEP / 'INSTALL-plan.json', plan)
dump(STEP / 'ITEM-PROVENANCE.json', dict(count=128, source=str(GAME / 'Data/FalloutNV.esm'),
    source_sha256=sha(GAME / 'Data/FalloutNV.esm'), selection='Explicit list of distinct ordinary MISC forms; no script, deleted or quest-item flag in base record.',
    script_flag_basis='Local xNVSE GameForms.h:321-322: Deleted0x20, QuestItem0x400. Raw MISC subrecords filtered for absent SCRI.', items=selected))
print(json.dumps(dict(helpers=rows, distinct_misc_forms=128, inspected_protected_files=len(protected))))
