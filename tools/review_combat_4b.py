"""Review pinned user gameplay evidence. Does not launch or change the game."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'source/combat/step4b'
CAPTURE = STEP / 'Evidence/LIVE-4B-20260916-233442.log'
GAME = Path(r'C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas')
EXPECTED = '1d20983e4d196d41f485853e2eac64ac0eaa49daede615ba971eb696ec138501'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(CAPTURE) == EXPECTED
rows = []
for number, line in enumerate(CAPTURE.read_text().splitlines(), 1):
    if line:
        rows.append(dict(kind=line.split()[0], line=number,
                         **dict(re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)=([^\s]+)', line))))
def of(kind): return [row for row in rows if row['kind'] == kind]
snapshots, items = of('ARMOUR_SNAPSHOT'), of('ARMOUR_ITEM')
assert len(snapshots) == 4 and len(items) == 5
expected = [
    ('1','1', {'00020420': 1.0, '00020426': 1.0}),
    ('1','2', {'00020420': 0.5}),
    ('1','3', {}),
    ('2','1', {'00020420': 1.0, '00020426': 1.0}),
]
for snap, (session, seq, equipment) in zip(snapshots, expected):
    assert (snap['session'], snap['seq']) == (session, seq)
    assert snap['stable_double_read'] == snap['enumeration_complete'] == '1'
    observed = {row['form']: float(row['condition_ratio']) for row in items
                if (row['session'], row['seq']) == (session, seq)}
    assert observed == equipment
    assert int(snap['equipped_armour_count']) == len(equipment)
    assert snap['status'] == ('complete_with_armour' if equipment else 'complete_no_armour_observed')

creatures = [row for row in of('HIT_CONTEXT') if row['target_type'] == '3C']
assert len(creatures) == 1
assert sum(int(row['unsupported_target_skipped']) for row in of('ARMOUR_SNAPSHOT_SUMMARY')) == 1
assert not any(row['target'] == creatures[0]['target'] for row in snapshots)
assert len(of('STARTUP_BANNER')) == 1
assert len(of('ARMOUR_READER_READY')) == 2
assert CAPTURE.read_text().rstrip().endswith('LIFECYCLE exit_game')

authority_keys = ['snapshot_authority','armour_preview','gameplay_writes','damage_replacement',
                  'bare_region_verified','region_coverage_complete','layer_order_verified',
                  'impact_snapshot_verified','speed_authority','region_authority']
assert all(row[key] == '0' for row in rows for key in authority_keys if key in row)
errors = ['rejected','unstable','omitted_after_limit','scope_rejected','stale_epoch',
          'unmatched','reused_live_address','overflow','read_failures','open_lifetimes',
          'invalid','depth_overflow','unscoped_stages','log_failures','mismatches',
          'accounting_unpaired','failed','process_fault','slots_held','open']
for row in rows:
    if row['kind'].endswith('_SUMMARY') or row['kind'] == 'SUMMARY':
        assert all(row[key] == '0' for key in errors if key in row), row
shot_count = sum(int(row['create']) for row in of('SUMMARY'))
assert shot_count == 8
assert all(row['weapon'] == '00004333' and row['ammo'] == '0006B53C' for row in of('HIT_CONTEXT'))

receipt = json.loads((STEP / 'INSTALL-4B-result.json').read_text(encoding='utf-8-sig'))
plan = json.loads((STEP / 'INSTALL-4B-plan.json').read_text())
pinned = {row['path']: row['sha256'] for row in plan['dependency_preconditions']}
pinned.update({row['path']: row['sha256'] for row in receipt['installed']})
assert all(sha(GAME / name) == digest for name, digest in pinned.items())
assert not (GAME / 'Data/RD.esm').exists()
report = dict(packet='4B', verdict='Initial live functional checkpoint passed; stress checkpoint pending',
              capture=str(CAPTURE.relative_to(ROOT)), sha256=EXPECTED,
              shots=shot_count, armour_snapshots=snapshots, armour_items=items,
              creature_context=creatures[0], creature_skips=1, startup_banners=1,
              sessions=2, reloads=1, normal_exit=True, audited_installed_files=len(pinned),
              native_version=326, damage_replacement=False, authority_promoted=False,
              limitations=['Four humanoid hits rather than five; half condition and helmet removal appear together.',
                           'All eight projectiles used hunting rifle and standard .308, not the requested 9mm.',
                           'VATS on creature is user-reported; the observed Creature skip is mode-independent.',
                           'No automatic-fire, heavy-inventory, NPC-to-player or ghoul evidence.',
                           'Creature collision region1 differs from hit-data region0; existing region authority remains0.'])
(STEP / 'LIVE-REVIEW-1.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
review = '''# Packet 4B: first live review

**Initial functional checkpoint passed. Stress/performance checkpoint remains pending.**

Pinned log: `Evidence/LIVE-4B-20260916-233442.log`, SHA256 `''' + EXPECTED + '''`.

| Load / snapshot | Worn equipment | Condition | Evidence line |
|---|---|---|---|
| 1 / 1 | Combat Armor + Combat Helmet | 400/400 and 50/50 | 76 |
| 1 / 2 | Combat Armor only | 200/400 | 138 |
| 1 / 3 | No worn armour observed | No bare-skin authority | 199 |
| 2 / 1 | Combat Armor + Combat Helmet restored | 400/400 and 50/50 | 518 |

All four snapshots completed both stable passes with zero reader rejections, unstable reads, scope rejections, stale epochs or omitted samples. One Creature hit (type3C, targetFF00196F) was skipped before the humanoid budget, consistent with the user's VATS bloatfly kill. No humanoid armour row was generated for that creature. Its recorded health crossed below zero. It is not necessary to hit another bloatfly outside VATS for this gate.

Two load sessions, one reload, one startup banner, normal exit. Eight projectile lifetimes: four humanoid hits, one creature hit and three other impacts. All were hunting rifle00004333 with standard .3080006B53C. This differs from the six landed hits/9mm requested, but supplies all four required equipment states; half-condition and helmet removal were observed together. It is not a full-helmet half-condition isolation test. No repeat is needed for this narrow inventory checkpoint.

Lifecycle and hit transaction summaries report no open calls/lifetimes, invalid calls, movement mismatches, unpaired movement accounting, read failures or admission faults. All authority/preview/damage-write fields remained0. Close contacts still report non-authoritative engine-segment evidence and `paired_model_unavailable`; this is expected under the retained Step3 limits, not newly granted energy authority. The creature has contact-region1 versus hit-region0; preserve that disagreement and do not infer human anatomy.

The worn-item traversal order reverses after reload, and an old item-address token is reused by a different item. This supports the existing rule: tokens are call-local and inventory order cannot define protection layers. Combat Armor logs raw biped_flagsCDCDCD08, matching its source record bytes; only explicitly understood flag bits may acquire later meaning.

All12 inspected installed dependency/helper hashes match the recorded versions; RD.esm remains absent. This review changed no game file and launched no process. It does not establish frame-time performance, large-inventory behaviour, NPC-to-player consistency, ghoul coverage, material/coverage mapping, creature armour or production damage readiness.

**Next, subject to user approval:** a short automatic-fire check against a humanoid carrying many distinct inventory entries. Purpose: exercise the bounded double traversal and diagnostic sample cap under load before adding semantic coverage. Do not advance to4C or enable damage from this result.
'''
(STEP / 'LIVE-REVIEW-1.md').write_text(review, encoding='utf-8')
status = ROOT / 'STATUS.md'
old = status.read_bytes()
heading = '''\n## Current checkpoint: Packet 4B initial live functional check PASSED; stress checkpoint pending

Pinned user capture SHA1d20983e4d196d41f485853e2eac64ac0eaa49daede615ba971eb696ec138501. Four stable Character snapshots: full body+helmet; body200/400 with helmet removed; no worn armour; full body+helmet restored after one reload. One Creature skip matches user-reported VATS bloatfly kill. Eight hunting-rifle/.308 projectile lifetimes, not requested9mm; adequate equipment evidence, no repeat for that difference. One banner, normal exit, zero reader rejections/unstable reads or lifecycle faults. Authority and damage replacement remain0.12 installed files verified; RD absent; no game changes.

Evidence: source/combat/step4b/LIVE-REVIEW-1.md and JSON. Only basic functionality accepted. Heavy-inventory/automatic-fire performance and all-actor coverage remain untested. Ask before preparing a short same-packet stress checkpoint; no4C/damage promotion. Raw tokens are call-local: post-reload reuse and reordered armour observed.

'''
if heading.encode() not in old:
    cut = old.index(b'\n') + 1
    status.write_bytes(old[:cut] + heading.encode() + old[cut:])
print(json.dumps(dict(verdict=report['verdict'], shots=shot_count, stable_snapshots=len(snapshots),
                     creature_skips=1, installed_files_verified=len(pinned), damage_replacement=False)))
