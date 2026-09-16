"""Record the user's bounded 4B stress checkpoint without changing the game."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'source/combat/step4b/stress'
CAPTURE = STEP / 'LIVE-4B-STRESS-20260916-235307.log'
EXPECTED = '555081337821fb407cb29afa59ca98b86f174766b2a108d1e1675b8849ad7ace'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(CAPTURE) == EXPECTED
text = CAPTURE.read_text()
rows = [dict(kind=line.split()[0], **dict(re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)=([^\s]+)', line)))
        for line in text.splitlines() if line]
def of(kind): return [r for r in rows if r['kind'] == kind]
snapshots = of('ARMOUR_SNAPSHOT')
assert len(snapshots) == 72
for row in snapshots:
    assert row['status'] == 'complete_with_armour'
    assert row['stable_double_read'] == row['enumeration_complete'] == '1'
    assert row['entries'] == '137' and row['equipped_armour_count'] == '2'
    items = [r for r in of('ARMOUR_ITEM') if (r['session'], r['seq']) == (row['session'], row['seq'])]
    assert len(items) == 2 and {r['form'] for r in items} == {'00020420', '00020426'}
for session, attempts, omitted in [('1',64,23), ('2',8,0)]:
    summary = next(r for r in of('ARMOUR_SNAPSHOT_SUMMARY') if r['session'] == session)
    assert int(summary['attempts']) == int(summary['complete_with_armour']) == attempts
    assert int(summary['omitted_after_limit']) == omitted
    assert sum(r['session'] == session for r in snapshots) == attempts
    hits = next(r for r in of('HIT_TX_SUMMARY') if r['session'] == session)
    assert int(hits['entries']) == int(hits['returns']) == attempts + omitted
    # Close-range contacts legitimately precede the movement observation point.
    impact = next(r for r in of('IMPACT_SUMMARY') if r['session'] == session)
    callbacks = [r for r in of('IMPACT_CALLBACK') if r['session'] == session and r['status'] != 'correlated']
    assert len(callbacks) == int(impact['unpaired_callbacks'])
    assert all(r['status'] == 'pre_movement_contact' for r in callbacks)
for row in rows:
    for key in ['snapshot_authority','armour_preview','gameplay_writes','damage_replacement',
                'speed_authority','region_authority','bare_region_verified','region_coverage_complete']:
        if key in row: assert row[key] == '0'
    if row['kind'].endswith('_SUMMARY') or row['kind'] == 'SUMMARY':
        for key in ['rejected','unstable','scope_rejected','stale_epoch','unmatched','reused_live_address',
                    'overflow','read_failures','open_lifetimes','invalid','invalid_contexts','depth_overflow',
                    'unscoped_stages','log_failures','mismatches','accounting_unpaired','failed','process_fault',
                    'slots_held','open','optional_read_failures','log_write_failures']:
            if key in row: assert row[key] == '0', row
assert len(of('STARTUP_BANNER')) == 1 and text.rstrip().endswith('LIFECYCLE exit_game')
assert all(r['weapon'] == '0008F217' and r['ammo'] == '0008ED03' for r in of('HIT_CONTEXT'))
assert [int(r['create']) for r in of('SUMMARY')] == [90,8]
plan = json.loads((STEP / 'INSTALL-plan.json').read_text())
game = Path(plan['game_root'])
pins = dict(plan['protected'])
pins.update({r['path']: r['sha256'] for r in plan['files']})
assert all(sha(game / name) == digest for name, digest in pins.items())
assert not (game / 'Data/RD.esm').exists()
report = dict(verdict='Bounded automatic-fire/inventory checkpoint passed', native_version=326,
    capture_sha256=EXPECTED, projectiles=98, hit_transactions=95, inventory_entries=137,
    stable_snapshots=72, first_session_snapshots=64, intentional_omissions=23, post_reload_snapshots=8,
    armour_reader_errors=0, movement_accounting_mismatches=0, pre_movement_callbacks=[17,5],
    installed_files_verified=len(pins), normal_exit=True, startup_banners=1,
    subjective_hitch_feedback='Not supplied', exact_frame_time_cost='Not measured',
    damage_replacement=False, authority_promoted=False)
(STEP / 'LIVE-REVIEW.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
review = '''# Step 4B stress capture review

**PASS for the bounded automatic-fire/enlarged-inventory checkpoint.** User gameplay; no assistant gameplay test or game changes.

Pinned capture `LIVE-4B-STRESS-20260916-235307.log`, SHA256 `''' + EXPECTED + '''`.

| Evidence | Before reload | After reload |
|---|---:|---:|
| Standard 9mm SMG projectiles | 90 | 8 |
| Target hit transactions | 87 | 8 |
| Complete stable armour snapshots | 64 | 8 |
| Inventory entries in every snapshot | 137 | 137 |
| Worn items in every snapshot | 2 | 2 |
| Intentionally omitted snapshots after cap | 23 | 0 |
| Reader rejections / instability / scope errors | 0 | 0 |

The 128 distinct added MISC records increased the earlier nine-entry inventory to137. Body00020420 and helmet00020426 were present in all72 snapshots. The loop stayed bounded at64 attempts in session1 while transaction accounting continued to87;23 later qualifying snapshots were intentionally omitted. Reload reset the budget and produced eight fresh complete snapshots. The user fired eight rounds after reload rather than roughly five; this is adequate and needs no repeat.

One startup banner, one save reload and normal process exit. All98 projectiles had create/impact/destroy accounting, with zero lifecycle/admission/read faults, zero movement mismatches or unpaired movement accounting, and no open lifetimes. Hit transaction entries/returns balance95/95. Three first-session projectiles did not produce a target damage transaction. The final sampled target health after reload is99969.9844; no target death is shown.

Impact diagnostics separately count17 and5 unpaired callbacks. Every one is explicitly `pre_movement_contact`, with no movement observation yet, not an armour-reader failure. Those contacts remain non-authoritative for speed under the existing Step3 contract. Broader diagnostic detail omissions after caps are intentional. No claim that all impact-speed cases are solved is made.

All14 pinned foundation/helper hashes match; RD.esm is absent. All snapshot, coverage, region, speed, armour-preview and damage-write authorities remain zero. This evidence establishes only this bounded diagnostic workload:137 entries, one humanoid and72 sampled scans. No per-scan timing exists, and the user has not supplied smoothness/stutter feedback. It does not certify exact overhead, the512-entry maximum, many-NPC concurrency, NPC-to-player consistency or uncapped production performance.

Next proposal, requiring user approval: Step4C explicit coverage/target-profile classification in preview only. Distinguish semantic body-region protection from raw equip slots, handle unknown equipment conservatively and preserve creature/natural-protection separation. Full damage remains HOLD, including exact speed and modifier-ownership requirements.
'''
(STEP / 'LIVE-REVIEW.md').write_text(review, encoding='utf-8')
status = ROOT / 'STATUS.md'
old = status.read_bytes()
heading = '''\n## Current checkpoint: Packet 4B bounded inventory/automatic-fire checkpoint PASSED

Pinned stress capture SHA555081337821fb407cb29afa59ca98b86f174766b2a108d1e1675b8849ad7ace.90 standard9mm SMG shots/87 target hits before reload;64 stable complete137-entry armour scans, then23 intentional omissions. After reload8 shots/hits and8 fresh complete scans. Both Combat Armor/Helmet retained. Zero reader rejects/unstable/scope failures, movement mismatches or open lifetimes. One banner, normal exit.14 installed hashes match; no game changes; RD absent.

Impact unpaired callbacks17+5 are all explicit pre_movement_contact, still no exact-speed authority. User hitch feedback not provided; no timing telemetry. This accepts the bounded workload only, not uncapped production or many-NPC performance. Both initial4B functional and bounded stress gates passed. All damage/armour authorities remain HOLD.

Evidence source/combat/step4b/stress/LIVE-REVIEW.md and JSON. NEXT ask before Step4C explicit armour coverage/target-profile classification in preview only; never infer coverage from equip slots, order from traversal or creature protection from missing worn armour. No new implementation approved by this test-completion message.

'''
if heading.encode() not in old:
    cut = old.index(b'\n')+1
    status.write_bytes(old[:cut]+heading.encode()+old[cut:])
print(json.dumps(report))
