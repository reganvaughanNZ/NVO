"""Audit the immutable user-run 3F1 log without executing or modifying the game."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3f1'
SHA = '77ebadbd30fd811b74b5c72e088cce8429c6f6845c846420d2e5515a110ffdc2'
FOLDER = PACKET / f'captures/2026-09-15-3F1-{SHA[:12]}'
raw = (FOLDER / 'NVOCombatCore.log').read_bytes()
assert hashlib.sha256(raw).hexdigest() == SHA
lines = raw.decode('utf-8').splitlines()
assert lines[0].startswith('NVOCombatCore 0.3.12 | phase=3F1')
assert lines[-1] == 'LIFECYCLE exit_game'
rows = [(s.split()[0], dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)', s))) for s in lines if s]
def get(name): return [r for n, r in rows if n == name]
def vec(s): return tuple(map(float, s.strip('()').split(',')))
def distance(a, b): return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))
events = [(s.split()[3], dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)', s)))
          for s in lines if s.startswith('EVENT ')]
creates = [r for n, r in events if n == 'CREATE']
impacts = [r for n, r in events if n == 'IMPACT']
destroys = [r for n, r in events if n == 'DESTROY']
selected, created = get('FLIGHT_SELECT'), get('FLIGHT_PREVIEW')
assert len(selected) == len(created) == len(creates) == len(destroys) == 6
assert len(impacts) == 5
expected = {'hunting-rifle': ('0006B53C', '0C000807'),
            'hunting-rifle-ap': ('0013E442', '0C00080D'),
            'hunting-rifle-hp': ('0013E443', '0C00080E')}
for i, (s, c, e) in enumerate(zip(selected, created, creates), 1):
    ammo, projectile = expected[s['profile']]
    assert s['session'] == c['session'] == e['session'] == ('1' if i <= 4 else '2')
    assert c['lifetime'] == e['lifetime'] == str(i)
    assert s['ammo'] == c['ammo'] == e['ammo'] == ammo
    assert s['replacement'] == c['projectile_base'] == projectile
    assert s['weapon'] == c['weapon'] == e['weapon'] == '00004333'
    assert s['original'] == '0008F20A'
    assert s['source'] == c['source'] == e['source'] == '00000014'
    assert c['profile'] == s['profile'] and c['phase'] == 'create'
    assert e['tracked'] == e['ammo_known'] == '1' and c['projectile'] == e['projectile']
assert [s['profile'] for s in selected] == [
    'hunting-rifle', 'hunting-rifle-ap', 'hunting-rifle', 'hunting-rifle-ap',
    'hunting-rifle-hp', 'hunting-rifle-hp']
hits = get('HIT_CONTEXT')
assert [h['lifetime'] for h in hits] == ['4', '5', '6']
for h in hits:
    c = created[int(h['lifetime'])-1]
    assert h['linked'] == h['ammo_known'] == '1'
    assert h['ammo'] == h['creation_ammo'] == c['ammo']
    assert h['carrier'] == c['projectile'] and h['weapon'] == c['weapon']
    assert h['target'] == 'FF001978' and h['target_type'] == '3B'

samples = {}
for name, r in rows:
    if name in ('PHYSICS_STEP', 'PHYSICS_ARGUMENT', 'PHYSICS_LOCAL_Z', 'PHYSICS_CONTROLLER', 'PHYSICS_ACTUAL'):
        key = tuple(int(r[k]) for k in ('session', 'lifetime', 'step'))
        label = name + (':' + r['phase'] if name == 'PHYSICS_CONTROLLER' else '')
        assert label not in samples.setdefault(key, {})
        samples[key][label] = r
comparisons = []
for key, sample in sorted(samples.items()):
    step, arg, reset = (sample[n] for n in ('PHYSICS_STEP', 'PHYSICS_ARGUMENT', 'PHYSICS_LOCAL_Z'))
    enter, leave = sample['PHYSICS_CONTROLLER:virtual_enter'], sample['PHYSICS_CONTROLLER:return']
    assert enter['vtable'] == '01090594' and enter['target'] == '00C73170'
    assert reset['reset_branch_observed'] == '1'
    assert (reset['preserve'], reset['original_reset']) == (('1', '0') if step['phase'] == 'apply' else ('0', '1'))
    assert vec(arg['readback']) == vec(enter['request']) == vec(leave['request']) == vec(reset['working'])
    result = dict(session=key[0], lifetime=key[1], step=key[2], phase=step['phase'])
    actual = sample.get('PHYSICS_ACTUAL')
    result['free_flight_verified'] = actual is not None
    if actual:
        error = distance(vec(step['world_delta']), vec(actual['actual_delta']))
        assert actual['matched'] == '1' and error <= float(actual['tolerance'])
        assert float(actual['position_error']) <= float(actual['tolerance'])
        result.update(vector_error=float(actual['vector_error']), position_error=float(actual['position_error']),
                      tolerance=float(actual['tolerance']), recomputed_rounded_error=error)
    else:
        assert (key[1], key[2]) in ((1, 3), (2, 6), (4, 2), (5, 0), (6, 2)), key
        result['collision_excluded'] = True
    comparisons.append(result)
rejects = get('PHYSICS_REJECT')
assert [(r['lifetime'], r['reason']) for r in rejects] == [('3', 'applied_displacement_mismatch')]
failure = {}
for name in ('METRICS', 'MOTION', 'POSITION', 'CONTEXT'):
    found = get('PHYSICS_REJECT_' + name)
    assert len(found) == 1
    r = found[0]
    assert (r['session'], r['lifetime'], r['report'], r['step']) == ('1', '3', '1', '392')
    failure[name.lower()] = r
m, motion, p, context = (failure[k] for k in ('metrics', 'motion', 'position', 'context'))
assert (m['vector_failed'], m['position_failed'], m['routine_step_logged']) == ('1', '0', '0')
assert vec(p['end_pos'])[2] == -2048 and vec(p['position_residual']) == (0, 0, 0)
assert context['submitted_local'] == context['returned_local']
assert context['contacts_observed'] == context['impacted_observed'] == context['controller_pending'] == '0'
assert context['reset_observed'] == '1' and context['controller_target'] == '00C73170'
assert all(context[k] == '393' for k in ('movement_entries', 'accounting_entries', 'controller_entries', 'controller_returns', 'commit_entries'))
assert abs(distance(vec(motion['expected_delta']), vec(motion['actual_delta'])) - float(m['vector_error'])) < 1e-5
routes, physics = get('PHYSICS_ROUTE_SUMMARY'), get('PHYSICS_SUMMARY')
assert [r['applied_verified'] for r in routes] == ['399', '1']
assert [r['baselines_verified'] for r in routes] == ['4', '1']
assert [r['mismatches'] for r in routes] == ['1', '0']
assert [r['lives_without_update'] for r in routes] == ['0', '1']
assert [r['applied_steps'] for r in physics] == ['403', '2']
diagnostics = get('PHYSICS_DIAGNOSTIC_SUMMARY')
assert [r['complete_failure_reports'] for r in diagnostics] == ['1', '0']
summaries = [(n, r) for n, r in rows if n == 'SUMMARY' or n.endswith('_SUMMARY')]
zero_fields = set('unmatched reused_live_address overflow read_failures open_lifetimes invalid_contexts open accounting_unpaired invalid retired_during_update overlap_lifetimes thread_changes nesting_limit identity_mismatches open_samples damage_replacement timing_writes damage_writes observer_writes skipped move_untracked accounting_untracked report_write_failures reports_omitted_by_limit'.split())
for name, r in summaries:
    for key in zero_fields.intersection(r): assert r[key] == '0', (name, key, r[key])
assert len([s for s in lines if s.startswith('LIFECYCLE post_load_game success=1')]) == 2
shot_rows = [r for r in get('PHYSICS_SHOT') if r['reason'] == 'destroy']
assert len(shot_rows) == 6
assert shot_rows[4]['baseline_verified'] == shot_rows[4]['steps'] == '0'
assert shot_rows[5]['baseline_verified'] == shot_rows[5]['verified_steps'] == '1'
assert [s['lifetime'] for s in get('FLIGHT_STEP') if s['phase'] == 'collision'] == ['1', '2', '4', '5', '6']
edited = [c for c in comparisons if c['free_flight_verified'] and c['phase'] == 'apply']
data = dict(capture=json.loads((FOLDER / 'capture.json').read_text()),
    diagnostic_capture_checkpoint_accepted=True, physics_fault_fixed=False, full_3F_checkpoint_accepted=False,
    ammo_identity_at_fire_accepted=True, post_reload_HP_hits_verified=True, ammo_persistence_accepted=False,
    profile_counts=dict(Counter(s['profile'] for s in selected)), all_6_identity_pairs_corroborated=True,
    selection_sequence=[s['profile'] for s in selected], impacts=impacts, hits=hits, shot_summaries=shot_rows,
    failure=failure, boundary_clamp_cause='suspected; exact branch and boundary provenance not established',
    reported_edited_matches=400, reported_baselines=5, reported_applied_steps=405, reported_mismatches=1,
    detailed_edited_matches=len(edited), detailed_controller_pairs=len(comparisons),
    detailed_baselines=sum(c['free_flight_verified'] and c['phase']=='baseline' for c in comparisons),
    detailed_collision_exclusions=sum(not c['free_flight_verified'] for c in comparisons),
    maximum_detailed_vector_error=max(c['vector_error'] for c in edited),
    maximum_detailed_error_fraction=max(c['vector_error']/c['tolerance'] for c in edited),
    comparisons=comparisons, summaries=summaries, lifecycle=[s for s in lines if s.startswith('LIFECYCLE ')],
    damage_authority_accepted=False, game_modified=False, gameplay_tested_by_assistant=False)
(FOLDER / 'review-data.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k: data[k] for k in ('diagnostic_capture_checkpoint_accepted', 'physics_fault_fixed',
    'profile_counts', 'reported_edited_matches', 'detailed_edited_matches', 'detailed_controller_pairs',
    'detailed_baselines', 'detailed_collision_exclusions', 'maximum_detailed_vector_error',
    'maximum_detailed_error_fraction')}, indent=2))
