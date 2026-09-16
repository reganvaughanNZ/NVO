"""Prepare a passive, traceable BallistX pilot dataset. Never writes game files."""
from pathlib import Path
import hashlib
import html
import importlib.util
import json
import math
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path(r'C:/Users/regan/Desktop/NVO Mod References (Open Source)/BallistX-70341-5-4-1712065466.rar')
GAME = Path(r'C:/Users/regan/Desktop/Steam Install Folder/steamapps/common/Fallout New Vegas/Data')
DEST = ROOT / 'source/combat/step3a'
EXPECTED_DONOR = 'd71fe28f1262dec7a0f2086f06b243168d74a3f11d8b57cd8b7b8127c9506e3d'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert digest(ARCHIVE.read_bytes()) == EXPECTED_DONOR, 'Donor archive changed: review before adapting.'
    DEST.mkdir(parents=True, exist_ok=True)
    provenance = {'archive': ARCHIVE.name, 'sha256': EXPECTED_DONOR, 'members': {}}

    def member(name):
        raw = subprocess.run(['tar', '-xOf', str(ARCHIVE), name], capture_output=True, check=True).stdout
        provenance['members'][name] = {'sha256': digest(raw), 'size_bytes': len(raw)}
        # Donor text contains CRCRLF and Windows-1252 characters.
        return raw.decode('cp1252').replace('\r\r\n', '\n').replace('\r\n', '\n')

    cartridges_name = 'Config/BallistX/Data/CartridgeData.cfg'
    weapons_name = 'Config/BallistX/Data/WeaponData.cfg'
    tables = {name: member(name) for name in (cartridges_name, weapons_name)}
    member('Config/BallistX/Help.txt')

    def selected_row(name, key, columns):
        found = [(i, line) for i, line in enumerate(tables[name].splitlines(), 1)
                 if line.split(';', 1)[0].split() and line.split(';', 1)[0].split()[0] == '@' + key]
        assert len(found) == 1, (name, key, 'missing or duplicate')
        i, line = found[0]
        fields = line.split(';', 1)[0].split()
        assert len(fields) == columns
        values = list(map(float, fields[1:]))
        assert all(math.isfinite(v) and v >= 0 for v in values)
        source = {'member': name, 'line': i, 'original_row': line}
        return values, source

    # Explicit pilot selections, not an inference from a weapon name or ammo price.
    pilots = [
        ('9mm-pistol-standard', 'FalloutNV.esm:0E3778', 'FalloutNV.esm:08ED03', 'FalloutNV.esm:08F20F'),
        ('hunting-rifle-standard-308', 'FalloutNV.esm:004333', 'FalloutNV.esm:06B53C', 'FalloutNV.esm:08F20A'),
    ]
    spec = importlib.util.spec_from_file_location('nvo_inspect_plugin', ROOT / 'tools/inspect_plugin.py')
    inspect = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inspect)
    wanted = {int(k.split(':')[1], 16) for row in pilots for k in row[1:]}
    game_data = (GAME / 'FalloutNV.esm').read_bytes()
    records = {}
    for kind, fid, flags, payload in inspect.records(game_data):
        if fid in wanted:
            fields = dict(inspect.fields(payload))
            records[fid] = {'type': kind, **{k: fields[k].rstrip(b'\0').decode('cp1252')
                                           for k in ('EDID', 'FULL') if k in fields}}
    provenance['base_record_file'] = {'name': 'FalloutNV.esm', 'sha256': digest(game_data),
                                     'scope': 'Record identity/type only. Not a winning-override or runtime projectile selection audit.'}

    profiles = []
    for pilot, weapon, ammo, projectile in pilots:
        for key, expected in ((weapon, 'WEAP'), (ammo, 'AMMO'), (projectile, 'PROJ')):
            assert records[int(key.split(':')[1], 16)]['type'] == expected, (key, expected)
        cv, cs = selected_row(cartridges_name, projectile, 9)
        wv, ws = selected_row(weapons_name, weapon, 4)
        drag, bc, grain, diameter, max_velocity, peak, temp, ignored_damage = cv
        barrel, ignored_zero, ignored_precision = wv
        assert drag in (1, 7) and min(bc, grain, diameter, max_velocity, barrel) > 0
        muzzle = max_velocity * barrel / (barrel + 2 * peak)
        profiles.append({
            'id': pilot,
            'match': {'weapon': weapon, 'ammunition': ammo, 'projectile_base': projectile,
                      'policy': 'All three must match the live shot. Otherwise preserve engine behaviour.'},
            'record_identities': {kind: records[int(key.split(':')[1], 16)]
                                  for kind, key in (('weapon', weapon), ('ammunition', ammo), ('projectile', projectile))},
            'flight_inputs': {'drag_curve': 'G' + str(int(drag)), 'ballistic_coefficient_lb_per_in2': bc,
                             'mass_grain': grain, 'diameter_in': diameter, 'maximum_velocity_m_per_s': max_velocity,
                             'bullet_travel_before_peak_pressure_in': peak, 'barrel_length_in': barrel,
                             'reference_temperature_k': 288.15},
            'preview_only': {'muzzle_velocity_m_per_s_at_reference_temperature': round(muzzle, 6),
                             'mass_kg': grain * 0.00006479891, 'diameter_m': diameter * 0.0254,
                             'barrel_length_m': barrel * 0.0254},
            'donor_source': {'cartridge': cs, 'weapon': ws},
            'unused_donor_values': {'base_damage': ignored_damage, 'zero_moa': ignored_zero,
                                    'precision_moa': ignored_precision, 'temperature_velocity_coefficient_m_per_s_per_k': temp}
        })

    curves = {}
    for drag in ('G1', 'G7'):
        name = f'Config/BallistX/Functions/{drag}_DragFunction.cfg'
        values = []
        for line in member(name).splitlines():
            tokens = line.split(';', 1)[0].split()
            if not tokens:
                continue
            assert len(tokens) == 2
            mach, coefficient = map(float, tokens)
            assert math.isfinite(mach) and math.isfinite(coefficient) and mach >= 0 and coefficient > 0
            assert not values or mach > values[-1][0]
            values.append([mach, coefficient])
        assert values[0][0] == 0 and values[-1][0] >= 3
        curves[drag] = {'source_member': name, 'columns': ['mach', 'drag_coefficient'], 'samples': values}

    data = {'schema_version': 1, 'packet': '3A', 'status': 'passive_source_data_not_runtime_configuration',
            'installed_native_version': 203, 'runtime_reader_implemented': False,
            'projectile_changes_enabled': False, 'damage_changes_enabled': False,
            'muzzle_preview_formula': 'maximum_velocity * barrel_length / (barrel_length + 2 * peak_pressure_travel)',
            'form_keys': 'Originating plugin filename plus six-digit local ID. Never a hard-coded load-order prefix.',
            'profiles': profiles, 'drag_curves': curves,
            'exclusions': ['No new ammo records or distributions', 'No shared WEAP/PROJ edits',
                           'No donor damage, zeroing or spread writes', 'No laser/plasma/explosive/melee flight conversion',
                           'No weather integration, projectile lifetime cutoff, engine-unit conversion or active integrator yet']}
    (DEST / 'NVO-Flight-Pilot.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    (DEST / 'PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    result = {'scope': 'Static data preparation only; no native build or game/GECK testing.',
              'checks': ['Exact donor archive hash', 'Unique selected rows and expected column counts',
                         'Positive finite physics inputs', 'Ascending finite drag tables',
                         'Base ESM WEAP/AMMO/PROJ identities', 'No runtime data reader claimed'],
              'profiles': [{ 'id': p['id'], **p['preview_only']} for p in profiles],
              'pending': ['Winning overrides and live projectile-base matching', 'Engine units and direction/velocity semantics',
                          'Native profile reader and read-only shot preview', 'Bounded flight integrator and hook ownership',
                          'User validation before any flight changes']}
    (DEST / 'PREPARATION-RESULT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    raw_json = (DEST / 'NVO-Flight-Pilot.json').read_text(encoding='utf-8')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>NVO combat packet 3A</title>
<style>body{max-width:860px;margin:48px auto;padding:0 24px;background:#151b1d;color:#eef4ed;font:18px/1.55 system-ui}a{color:#b8e0a7}button{padding:12px 20px;font:inherit;cursor:pointer}textarea{width:100%;height:320px;background:#0b1113;color:#d2e6cf;margin-top:20px}small{display:block}</style>
<h1>Packet 3A: BallistX pilot data</h1><p>Purpose: prepare two traceable weapon/cartridge profiles before implementing flight.</p>
<p>This is source data. Keep NVOCombatCore version 203 installed. There is nothing to copy into GECK or the game, and no additional playtest for this packet.</p>
<p>The pilot covers the 9mm Pistol with standard 9mm and Hunting Rifle with standard .308. Matching also requires the actual projectile base. Unknown combinations keep engine behaviour.</p>
<p><a href="README.md">Full instructions and next checkpoint</a> · <a href="NVO-Flight-Pilot.json">JSON data</a></p>
<button id="copy">Copy complete pilot JSON</button><small id="status" role="status">For source editing only. The installed DLL does not read this file.</small>
<textarea id="data" readonly aria-label="Complete pilot JSON">''' + html.escape(raw_json) + '''</textarea>
<script>document.querySelector('#copy').onclick=async()=>{const t=document.querySelector('#data');try{await navigator.clipboard.writeText(t.value);document.querySelector('#status').textContent='Copied complete pilot JSON.'}catch(e){t.select();document.querySelector('#status').textContent=document.execCommand('copy')?'Copied complete pilot JSON.':'Select the text and press Ctrl+C.'}};</script></html>'''
    (DEST / 'START-HERE.html').write_text(page, encoding='utf-8')
    # Only named packet artifacts enter the deliverable; no game/donor binaries.
    names = ['README.md', 'CREDITS.md', 'NVO-Flight-Pilot.json', 'PROVENANCE.json', 'PREPARATION-RESULT.json', 'START-HERE.html']
    assert all((DEST / n).is_file() for n in names)
    target = ROOT / 'release/NVO-Combat-Packet-3A-Data.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.write(DEST / name, 'NVO-Combat-Packet-3A-Data/' + name)
        z.write(Path(__file__), 'NVO-Combat-Packet-3A-Data/source/prepare_combat_3a.py')
        z.write(ROOT / 'tools/inspect_plugin.py', 'NVO-Combat-Packet-3A-Data/source/inspect_plugin.py')
    print(json.dumps({'packet': str(target), 'bytes': target.stat().st_size, 'sha256': digest(target.read_bytes()), **result}, indent=2))


if __name__ == '__main__':
    main()
