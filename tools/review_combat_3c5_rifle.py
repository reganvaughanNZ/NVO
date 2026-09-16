"""Validate the archived user rifle/VATS follow-up; never run the game."""
from pathlib import Path
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'source/combat/step3c5'
SHA = '5ffa63f073d093706363e8d88de583b08e87f8ef1d5dda49295f728cf86d4c0b'
FOLDER = PACKET/f'captures/2026-09-15-3C5-{SHA[:12]}'
raw = (FOLDER/'NVOCombatCore.log').read_bytes()
assert hashlib.sha256(raw).hexdigest() == SHA
lines = raw.decode('utf-8').splitlines()
assert lines[0].startswith('NVOCombatCore 0.3.10 | phase=3C5')
assert lines[-1] == 'LIFECYCLE exit_game'
rows = [(line.split(' ', 1)[0], dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)', line))) for line in lines]
def select(name):
    return [row for kind, row in rows if kind == name]
def vec(value):
    return tuple(map(float, value.strip('()').split(',')))

samples = {}
for name, row in rows:
    if name in ('PHYSICS_STEP', 'PHYSICS_ARGUMENT', 'PHYSICS_LOCAL_Z', 'PHYSICS_CONTROLLER',
                'PHYSICS_ARGUMENT_RETURN', 'PHYSICS_ACTUAL', 'PHYSICS_BOUNDARY'):
        key = tuple(int(row[field]) for field in ('session', 'lifetime', 'step'))
        label = name + (':'+row['phase'] if name == 'PHYSICS_CONTROLLER' else '')
        assert label not in samples.setdefault(key, {})
        samples[key][label] = row
comparisons = []
for key, sample in sorted(samples.items()):
    step = sample['PHYSICS_STEP']
    request = sample['PHYSICS_ARGUMENT']['readback']
    reset = sample['PHYSICS_LOCAL_Z']
    enter = sample['PHYSICS_CONTROLLER:virtual_enter']
    leave = sample['PHYSICS_CONTROLLER:return']
    assert enter['vtable'] == '01090594' and enter['target'] == '00C73170'
    assert request == reset['working'] == enter['request'] == leave['request'] == sample['PHYSICS_ARGUMENT_RETURN']['argument']
    assert reset['reset_branch_observed'] == '1'
    assert (reset['preserve'], reset['original_reset']) == (('1', '0') if step['phase'] == 'apply' else ('0', '1'))
    assert enter['dt_s'] == reset['dt_s'] == step['movement_dt_s']
    actual = sample.get('PHYSICS_ACTUAL')
    item = dict(session=key[0], lifetime=key[1], step=key[2], phase=step['phase'], free_flight_verified=actual is not None)
    if actual:
        error = math.dist(vec(step['world_delta']), vec(actual['actual_delta']))
        assert actual['matched'] == '1' and error <= float(actual['tolerance'])
        assert float(actual['position_error']) == 0
        item.update(vector_error=float(actual['vector_error']), recomputed_rounded_error=error,
                    tolerance=float(actual['tolerance']))
    else:
        item['collision_boundary'] = sample['PHYSICS_BOUNDARY']
    comparisons.append(item)

shots = [row for row in select('PHYSICS_SHOT') if row['reason'] == 'destroy']
assert [int(row['verified_steps']) for row in shots] == [1, 3, 3]
assert [int(row['steps']) for row in shots] == [2, 4, 4]
for shot in shots:
    same = [item for item in comparisons if item['lifetime'] == int(shot['lifetime'])]
    excluded = [item for item in same if not item['free_flight_verified']]
    assert len(excluded) == 1 and excluded[0]['step'] == int(shot['steps'])
    timing = [row for row in select('FLIGHT_STEP') if row['lifetime'] == shot['lifetime']]
    assert timing[-1]['phase'] == 'collision' and sum(row['phase'] == 'collision' for row in timing) == 1
    assert shot['controller_entries'] == shot['controller_returns'] == shot['movement_entries'] == shot['accounting_entries'] == shot['reset_entries']
    assert shot['pending'] == shot['controller_pending'] == '0'
    assert shot['baseline_verified'] == '1'
for row in [r for r in select('FLIGHT_PREVIEW') if r['phase'] == 'create']:
    assert (row['weapon'], row['ammo'], row['projectile_base']) == ('0C000801', '0C000803', '0C000805')
summaries = [(name, row) for name, row in rows if name == 'SUMMARY' or name.endswith('_SUMMARY')]
zero_fields = set('unmatched reused_live_address overflow read_failures open_lifetimes invalid_contexts rejected open mismatches accounting_unpaired lives_without_update invalid retired_during_update overlap_lifetimes thread_changes nesting_limit identity_mismatches open_samples damage_replacement timing_writes damage_writes'.split())
for name, row in summaries:
    for field in zero_fields.intersection(row):
        assert row[field] == '0', (name, field, row[field])
assert not any(name in ('PHYSICS_REJECT', 'PHYSICS_DISABLED', 'DETAIL_LIMIT', 'PRIORITY_LIMIT') for name, row in rows)
assert [r['applied_verified'] for r in select('PHYSICS_ROUTE_SUMMARY')] == ['1', '6']
assert sum(int(r['reset_entries']) for r in select('PHYSICS_ROUTE_SUMMARY')) == 13
assert sum(int(r['reset_preserved']) for r in select('PHYSICS_ROUTE_SUMMARY')) == 10
assert [r['create'] for r in select('SUMMARY')] == ['1', '2']
assert all(r['create'] == r['impact'] == r['destroy'] for r in select('SUMMARY'))
assert sum(line.startswith('LIFECYCLE post_load_game success=1') for line in lines) == 2
applied = [c for c in comparisons if c['phase'] == 'apply' and c['free_flight_verified']]
assert len(applied) == 7
data = dict(sha256=SHA, bytes=len(raw), lines=len(lines), comparisons=comparisons, shots=shots,
            archive=str((FOLDER/'NVOCombatCore.log').relative_to(ROOT)), summaries=summaries,
            vats_source='User reports VATS test; no direct VATS mode field in log',
            limited_rifle_flight_checkpoint_accepted=True, full_vats_physics_accepted=False,
            damage_authority_accepted=False, game_modified=False,
            source_last_write_local='2026-09-15T16:22:41.9349888+12:00')
(FOLDER/'review-data.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(archive=data['archive'], sha256=SHA, bytes=len(raw), lines=len(lines),
                     applied_verified=len(applied), baselines_verified=3,
                     max_vector_error=max(c['vector_error'] for c in applied),
                     max_tolerance_fraction=max(c['vector_error']/c['tolerance'] for c in applied),
                     limited_rifle_flight_checkpoint_accepted=True), indent=2))
