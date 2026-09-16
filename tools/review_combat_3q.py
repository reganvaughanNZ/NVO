"""Read and preserve the user's 13-shot native322 checkpoint; never run the game."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, re

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3q'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')

def sha(data):
    return hashlib.sha256(data).hexdigest()

raw = (GAME / 'NVOCombatCore.log').read_bytes()
nvse = (GAME / 'nvse.log').read_bytes()
capture = PACKET / 'captures' / ('review-' + sha(raw)[:12])
capture.mkdir(parents=True, exist_ok=True)
for name, data in [('NVOCombatCore.log', raw), ('nvse.log', nvse)]:
    target = capture / name
    if target.exists():
        assert target.read_bytes() == data, 'Do not overwrite an existing capture'
    else:
        target.write_bytes(data)

lines = raw.decode('utf-8', errors='replace').splitlines()
rows = defaultdict(list)
for number, line in enumerate(lines, 1):
    if not line:
        continue
    kind = line.split()[0]
    data = dict(re.findall(r'\b([a-zA-Z_][a-zA-Z_0-9]*)=([^\s]+)', line))
    data['_line'] = number
    if kind == 'EVENT':
        match = re.search(r'^EVENT session=\d+ seq=\d+ (\w+)', line)
        if match:
            kind += '_' + match[1]
    rows[kind].append(data)

checks = {}
checks['native322'] = bool(lines and lines[0].startswith('NVOCombatCore 0.3.22 | phase=3Q'))
expected_weapons = ['00004333'] * 3 + ['000E3778'] * 3 + ['00004333'] + ['0008F217'] * 5 + ['000E3778']
created = rows['EVENT_CREATE']
selected = rows['FLIGHT_SELECT']
committed = rows['FLIGHT_ADMISSION_COMMIT']
boundary = rows['SPAWN_BOUNDARY']
checks['exact_thirteen_weapon_sequence'] = [r.get('weapon') for r in created] == expected_weapons
checks['all_selected_reserved'] = len(selected) == 13 and all(r.get('reservation_before_selection') == '1' for r in selected)
checks['all_returns_paired'] = len(boundary) == 13 and all(r.get('paired') == '1' and r.get('reserved') == '1' and r.get('returned_null') == '0' for r in boundary)
checks['all_exact_commits'] = len(committed) == 13 and all(r.get('exact_return') == '1' and r.get('physics_and_lifecycle_owned') == '1' for r in committed)
checks['identities_match'] = all(
    sorted((r.get('session'), r.get('lifetime'), r.get('projectile')) for r in rows[kind]) ==
    sorted((r.get('session'), r.get('lifetime'), r.get('projectile')) for r in created)
    for kind in ['FLIGHT_ADMISSION_COMMIT', 'EVENT_DESTROY'])
checks['lifetimes_unique'] = len({r.get('lifetime') for r in created}) == 13
checks['standard_ammo'] = all(r.get('ammo') == ('0006B53C' if r.get('weapon') == '00004333' else '0008ED03') for r in created)
sessions = sorted({r['session'] for r in rows['SPAWN_BOUNDARY_READY']}, key=int)
session_counts = Counter(r['session'] for r in created)
checks['ready_every_capture'] = bool(sessions) and set(sessions) == {r['session'] for r in rows['FLIGHT_SELECTOR_READY'] if r.get('ready') == '1' and r.get('boundary_ready') == '1'}
summary_groups = {
    'SUMMARY': ['unmatched', 'reused_live_address', 'overflow', 'read_failures', 'open_lifetimes'],
    'SPAWN_BOUNDARY_SUMMARY': ['null_returns', 'mismatched', 'nested', 'depth_overflow', 'other_thread', 'stale_returns', 'unscoped_creates', 'log_failures'],
    'FLIGHT_ADMISSION_SUMMARY': ['cancelled', 'failed', 'lifecycle_refused', 'physics_refused', 'slots_held', 'process_fault'],
    'PHYSICS_ADMISSION_SUMMARY': ['cancelled', 'capacity_refused', 'slots_held', 'process_fault'],
    'PHYSICS_SUMMARY': ['rejected', 'overflow', 'open'],
    'PHYSICS_ROUTE_SUMMARY': ['mismatches', 'accounting_unpaired'],
    'PHYSICS_DIAGNOSTIC_SUMMARY': ['mismatches', 'complete_failure_reports', 'report_write_failures', 'reports_omitted_by_limit'],
}
for kind, zeros in summary_groups.items():
    group = rows[kind]
    checks[kind + '_complete_clean'] = {r['session'] for r in group} == set(sessions) and all(r.get(k) == '0' for r in group for k in zeros)
for kind, counts in {
    'SUMMARY': ['create', 'destroy'],
    'SPAWN_BOUNDARY_SUMMARY': ['calls', 'paired'],
    'FLIGHT_ADMISSION_SUMMARY': ['reserved', 'committed'],
    'PHYSICS_ADMISSION_SUMMARY': ['reservations', 'committed'],
    'PHYSICS_SUMMARY': ['accepted'],
}.items():
    checks[kind + '_counts'] = bool(rows[kind]) and all(int(r.get(k, -1)) == session_counts[r['session']] for r in rows[kind] for k in counts)
checks['normal_exit'] = any(r.get('reason') == 'exit_game' for r in rows['SUMMARY'])
checks['no_failure_rows'] = not any(re.match(r'^(?:PHYSICS_REJECT|FLIGHT_ADMISSION_REJECT|FLIGHT_ADMISSION_CANCEL|SPAWN_BOUNDARY_DISABLED)\b', line) for line in lines)
checks['no_damage_replacement'] = all('damage_replacement=1' not in line for line in lines)
checks['applied_and_verified_flight'] = sum(int(r['applied_steps']) for r in rows['PHYSICS_SUMMARY']) > 0 and sum(int(r['applied_verified']) for r in rows['PHYSICS_ROUTE_SUMMARY']) > 0
checks['movement_details_clean'] = bool(rows['PHYSICS_ACTUAL']) and all(r.get('matched') == '1' for r in rows['PHYSICS_ACTUAL'])

# Protected foundation checks are read-only, including the installed pair.
install = json.loads((PACKET / 'INSTALL-3Q-result.json').read_text(encoding='utf-8-sig'))
baseline = json.loads((PACKET / 'BASELINE.json').read_text())
expected_files = dict(baseline['game_files'])
expected_files.update({r['path']: r['sha256'] for r in install['installed']})
checks['installed_and_foundation_unchanged'] = all(sha((GAME / name).read_bytes()) == h for name, h in expected_files.items()) and not (GAME / 'Data/RD.esm').exists()

lives = []
for r in created:
    ident = r['lifetime']
    lives.append({
        'shot': int(ident), 'session': int(r['session']), 'weapon': r['weapon'], 'ammo': r['ammo'],
        'committed': any(x.get('lifetime') == ident for x in committed),
        'destroyed': any(x.get('lifetime') == ident for x in rows['EVENT_DESTROY']),
        'impact_count': sum(x.get('lifetime') == ident for x in rows['EVENT_IMPACT']),
        'physics_detail_rows': sum(x.get('lifetime') == ident for x in rows['PHYSICS_ACTUAL']),
    })
result = {
    'packet': '3Q', 'native_version': 322,
    'status': 'PASS: targeted admission, flight and reload checkpoint' if all(checks.values()) else 'INCOMPLETE_OR_REVIEW_REQUIRED',
    'capture': str(capture.relative_to(ROOT)), 'log_sha256': sha(raw), 'nvse_log_sha256': sha(nvse),
    'checks': checks, 'sessions': sessions, 'shots': lives,
    'summaries': {kind: rows[kind] for kind in summary_groups},
    'applied_steps_total': sum(int(r['applied_steps']) for r in rows['PHYSICS_SUMMARY']),
    'applied_verified_total': sum(int(r['applied_verified']) for r in rows['PHYSICS_ROUTE_SUMMARY']),
    'prior_cosave_warning_count': nvse.count(b'plugin has data in save file but no handler'),
    'other_nvse_error_lines': [line for line in nvse.decode(errors='replace').splitlines() if not line.startswith('RegisterCommand ') and re.search(r'error|failed|exception', line, re.I)],
    'protected_files_verified': len(expected_files),
    'limits': ['Player firing only; no live capacity saturation, nesting, foreign-thread creation or exception proof', 'No damage replacement or contact-energy authority', 'Routine physics detail is limited to eight lifetimes per capture; summary counts remain independent'],
}
(capture / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['status', 'capture', 'checks', 'applied_steps_total', 'applied_verified_total', 'prior_cosave_warning_count', 'other_nvse_error_lines']}, indent=2))
