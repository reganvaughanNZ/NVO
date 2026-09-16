"""Review the archived user-run 310 reload/VATS regression. No game execution."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'source/combat/step3c5'
SHA = '484a826a0db979cd8323a6110e6be2257fd135b250f881c2414f7a3f8e689a4d'
FOLDER = PACKET / f'captures/2026-09-15-3C5-{SHA[:12]}'
raw = (FOLDER / 'NVOCombatCore.log').read_bytes()
assert hashlib.sha256(raw).hexdigest() == SHA
lines = raw.decode('utf-8').splitlines()
assert lines[0].startswith('NVOCombatCore 0.3.10 | phase=3C5')
assert lines[-1] == 'LIFECYCLE exit_game'
rows = [(line.split(' ', 1)[0], dict(re.findall(r'(\w+)=(\([^)]*\)|[^ ]+)', line)))
        for line in lines if line]

def vec(value):
    return tuple(map(float, value.strip('()').split(',')))

def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))

samples = {}
for name, row in rows:
    if name in ('PHYSICS_STEP', 'PHYSICS_ARGUMENT', 'PHYSICS_LOCAL_Z',
                'PHYSICS_CONTROLLER', 'PHYSICS_ACTUAL', 'PHYSICS_BOUNDARY'):
        key = tuple(int(row[k]) for k in ('session', 'lifetime', 'step'))
        label = name + (':' + row['phase'] if name == 'PHYSICS_CONTROLLER' else '')
        assert label not in samples.setdefault(key, {})
        samples[key][label] = row

comparisons = []
for key, sample in sorted(samples.items()):
    step = sample['PHYSICS_STEP']
    arg = sample['PHYSICS_ARGUMENT']
    reset = sample['PHYSICS_LOCAL_Z']
    enter = sample['PHYSICS_CONTROLLER:virtual_enter']
    leave = sample['PHYSICS_CONTROLLER:return']
    assert enter['vtable'] == '01090594' and enter['target'] == '00C73170'
    assert reset['reset_branch_observed'] == '1'
    assert (reset['preserve'], reset['original_reset']) == (
        ('1', '0') if step['phase'] == 'apply' else ('0', '1'))
    assert vec(arg['readback']) == vec(enter['request']) == vec(leave['request']) == vec(reset['working'])
    assert enter['dt_s'] == step['movement_dt_s'] == reset['dt_s']
    result = dict(session=key[0], lifetime=key[1], step=key[2], phase=step['phase'],
                  reset_preserved=int(reset['preserve']), request_preserved=True)
    actual = sample.get('PHYSICS_ACTUAL')
    result['free_flight_verified'] = actual is not None
    if actual:
        error = distance(vec(step['world_delta']), vec(actual['actual_delta']))
        assert actual['matched'] == '1' and error <= float(actual['tolerance'])
        assert float(actual['position_error']) <= float(actual['tolerance'])
        result.update(vector_error=float(actual['vector_error']), tolerance=float(actual['tolerance']),
                      recomputed_rounded_error=error, position_error=float(actual['position_error']))
    else:
        boundary = sample['PHYSICS_BOUNDARY']
        result.update(collision_boundary=boundary,
                      collision_candidate_difference=distance(vec(step['world_delta']), vec(boundary['candidate_delta'])))
    comparisons.append(result)

shots = [r for n, r in rows if n == 'PHYSICS_SHOT' and r['reason'] == 'destroy']
assert len(shots) == 6
assert [int(s['verified_steps']) for s in shots] == [2, 9, 3, 9, 0, 1]
assert [int(s['steps']) for s in shots] == [3, 10, 4, 10, 1, 2]
for shot in shots:
    life = int(shot['lifetime'])
    same = [c for c in comparisons if c['lifetime'] == life]
    excluded = [c for c in same if not c['free_flight_verified']]
    assert len(excluded) == 1 and excluded[0]['step'] == int(shot['steps'])
    timing = [r for n, r in rows if n == 'FLIGHT_STEP' and int(r['lifetime']) == life]
    assert timing[-1]['phase'] == 'collision'
    assert sum(r['phase'] == 'collision' for r in timing) == 1
    assert int(shot['verified_steps']) == sum(c['phase'] == 'apply' and c['free_flight_verified'] for c in same)
    assert shot['pending'] == shot['controller_pending'] == '0'
    assert shot['controller_entries'] == shot['controller_returns'] == shot['reset_entries'] == shot['movement_entries'] == shot['accounting_entries']

zero_fields = set('unmatched reused_live_address overflow read_failures open_lifetimes invalid_contexts rejected open mismatches accounting_unpaired lives_without_update invalid retired_during_update overlap_lifetimes thread_changes nesting_limit identity_mismatches open_samples damage_replacement timing_writes damage_writes observer_writes'.split())
summaries = [(n, r) for n, r in rows if n == 'SUMMARY' or n.endswith('_SUMMARY')]
for name, row in summaries:
    for field in zero_fields.intersection(row):
        assert row[field] == '0', (name, field, row[field])
routes = [r for n, r in rows if n == 'PHYSICS_ROUTE_SUMMARY']
assert len(routes) == 3
assert [r['applied_verified'] for r in routes] == ['11', '12', '1']
assert [r['baselines_verified'] for r in routes] == ['2', '2', '2']
assert sum(int(r['reset_entries']) for r in routes) == 36
assert sum(int(r['reset_preserved']) for r in routes) == 30
for row in [r for n, r in rows if n == 'SUMMARY']:
    assert row['create'] == row['impact'] == row['destroy'] == '2'
assert not any(n in ('PHYSICS_REJECT', 'PHYSICS_DISABLED', 'DETAIL_LIMIT', 'PRIORITY_LIMIT') for n, r in rows)
assert sum(line.startswith('LIFECYCLE post_load_game success=1') for line in lines) == 3

free = [c for c in comparisons if c['phase'] == 'apply' and c['free_flight_verified']]
assert len(free) == 24
data = dict(log_sha256=SHA, bytes=len(raw), lines=len(lines),
            archive=str((FOLDER/'NVOCombatCore.log').relative_to(ROOT)),
            source_last_write_local='2026-09-15T16:04:17.4867269+12:00',
            comparisons=comparisons, shots=shots, summaries=summaries,
            lifecycle=[line for line in lines if line.startswith('LIFECYCLE ')],
            timing_phases=dict(Counter(r['phase'] for n, r in rows if n == 'FLIGHT_STEP')),
            reload_checkpoint_accepted=True, final_session_vats_source='User report, not an explicit logged VATS field',
            rifle_vats_edited_free_flight_verified=False, pistol_vats_edited_free_flight_verified=True,
            damage_authority_accepted=False, game_modified=False)
(FOLDER/'review-data.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')

review = f'''# Packet 3C5 / 310 - reload regression reviewed

**Two reloads passed the observed cleanup and reinitialization checks. The reported VATS session verifies one edited 9mm free-flight segment; edited rifle free flight in VATS remains unobserved.** Repeating steps 2 and 3 did not invalidate this capture.

Archive: `{data['archive']}`. SHA256 `{SHA}`, {len(raw):,} bytes, {len(lines)} lines. Source last write {data['source_last_write_local']}. Normal exit. `tools/review_combat_3c5_regression.py` verifies this immutable capture and writes the detailed comparisons in review-data.json. The VATS label for session 3 comes from the user's completed-instructions report; the log does not explicitly identify VATS mode.

| Session | Context | Rifle applied / verified | 9mm applied / verified | Controller pairs |
|---|---|---:|---:|---:|
| 1 | Scenery, initial load | 3 / 2 | 10 / 9 | 15 |
| 2 | Scenery, repeated after reload | 4 / 3 | 10 / 9 | 16 |
| 3 | Live targets, reported VATS after second reload | 1 / 0 | 2 / 1 | 5 |

All six lifetimes have one unchanged baseline and one final collision segment. All 24 edited free-flight comparisons match. Maximum logged edited-vector error is {max(c['vector_error'] for c in free):.9g} units; maximum tolerance fraction {max(c['vector_error']/c['tolerance'] for c in free):.6f}. All six baseline comparisons match too. Each final collision segment is deliberately excluded from free-flight verification, explaining the applied/verified difference.

All 36 movement/accounting/controller/reset observations pair. Baselines retain the original local-Z reset, and all 30 edited requests preserve the submitted vector at the guarded reset branch. No reported rejection, mismatch, read/identity error, unpaired accounting, concurrent address reuse, overflow, nesting/overlap, invalid timing or log cap. The three sessions each have two creates, impacts and destructions, with no open lifetimes at either reload or exit. Reinitialization arms the same restricted pilot scope. The final session has two linked actor hit contexts with known ammunition and two hit/two health callbacks; those callbacks do not independently prove single damage application. Damage replacement stays disabled.

## Remaining evidence gap

The final rifle (lifetime 5) has one unchanged baseline followed immediately by an edited collision segment. Its guarded local-Z preservation executes, but there is no PHYSICS_ACTUAL row for an edited free-flight segment. The final 9mm (lifetime 6) has one matching edited free-flight segment before its collision. This establishes limited 9mm movement evidence, not every VATS trajectory or critical/armour rule.

Rifle collision-boundary candidate Z is -305.188477 versus intended -360.377746, about 55.19 engine units apart. It is not a verified free-flight match, and this review does not attribute the correction to a particular engine mechanism. The collision boundary also has a nonzero current delta. The next observation must distinguish pre-contact flight from collision/target adjustment; do not dismiss this row as proof of exact collision-path physics or use it to validate impact energy. The rifle's guarded caller input remained intact.

Keep build 310 installed. Propose only one farther-away live-target VATS torso shot with the private hunting rifle, with sufficient travel for an edited free-flight segment. Ask before giving the next checkpoint. No additional pistol or reload repetition is needed. If a longer shot still shows no usable free-flight observation, investigate that path instead of repeatedly asking for the same test. No wider ammunition, tracers, damage or armour work is accepted by this review.

Archived/reviewed evidence and updated checkpoint documents only. No native edits, rebuild, install, game launch, gameplay, GECK work or process-memory access.
'''
(PACKET/'REVIEW-2-RELOAD-VATS.md').write_text(review, encoding='utf-8')
checkpoint = f'''## Current combat checkpoint: 3C5 / 310 reloads accepted; rifle VATS free flight remains

2026-09-15: reviewed the user's completed regression; steps 2/3 were repeated. Immutable archive {data['archive']}, SHA256 {SHA}; {len(raw):,} bytes / {len(lines)} lines. See source/combat/step3c5/REVIEW-2-RELOAD-VATS.md. Three loads, two reloads, six shots, normal exit; all lifetimes/controller calls retire cleanly. Six baselines and 24 edited free-flight matches, 30 edits, six collision exclusions, 36 paired controller/reset calls; no reported tracking faults. Final user-reported VATS session: rifle applied1/verified0 (baseline then collision), pistol applied2/verified1. VATS mode itself is not logged. Rifle collision-boundary candidate Z differs by about55.19 units; collision-path/contact-energy semantics remain unresolved and must not be described as validated.

Keep 310. Ask before the next focused checkpoint: one longer-distance private hunting-rifle VATS torso shot to obtain edited free-flight evidence. No need to repeat pistol/reload tests. Do not advance to more ammo/tracers/armour yet. Native damage authority disabled; no game/native changes in this review. The previous accepted two-weapon non-VATS checkpoint remains valid.

'''
for path in (ROOT/'STATUS.md', ROOT/'source/combat/README.md'):
    old = path.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first, sep, rest = old.partition(b'\n')
        path.write_bytes(first+sep+b'\n'+checkpoint.encode('utf-8')+rest)
print(json.dumps(dict(review=str(PACKET/'REVIEW-2-RELOAD-VATS.md'), sha256=SHA,
                      bytes=len(raw), lines=len(lines), verified_edited_steps=len(free),
                      reloads_accepted=True, rifle_vats_free_flight_pending=True), indent=2))
