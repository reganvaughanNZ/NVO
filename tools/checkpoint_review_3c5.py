"""Record the reviewed 310 checkpoint without changing the installed build."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'source/combat/step3c5'
FOLDER=PACKET/'captures/2026-09-15-3C5-da21de37bf4f'
data=json.loads((FOLDER/'review-data.json').read_text())
sha='da21de37bf4f35d5330c29084c54c80ec5c76e9903f7878e285984ad55ccbf82'
assert data['log_sha256']==sha==hashlib.sha256((FOLDER/'NVOCombatCore.log').read_bytes()).hexdigest()
assert data['limited_two_weapon_flight_checkpoint_accepted']
applied=[c for c in data['comparisons'] if c['phase']=='apply' and c['free_flight_verified']]
maximum=max(c['vector_error'] for c in applied)
fraction=max(c['vector_error']/c['tolerance'] for c in applied)
omission_outside=sum(c['omission_error']>c['tolerance'] for c in applied)
review=f'''# Packet 3C5 / 310 - user flight test accepted

**Accept this limited two-weapon, non-VATS flight checkpoint. The prior local-Z loss is corrected in these observations.** This is not blanket acceptance of all projectile types or final physical calibration.

Archived game-root NVOCombatCore.log under `captures/2026-09-15-3C5-da21de37bf4f/NVOCombatCore.log`: SHA256 `{sha}`, {data['bytes']:,} bytes, {data['lines']} lines, last write {data['source_last_write_local']} local. Archive read was stable and the log ended with normal exit. `tools/review_combat_3c5.py` parses the evidence, verifies pairing/counts, and independently compares the rounded logged intended/actual vectors. Details in review-data.json.

## Outcome

One successful load, rifle then pistol, private weapons/ammunition/projectile bases correctly identified. Both hit scenery 00106B5E, with one matched impact and destruction apiece. Reuse of dynamic reference FF001993 occurred after destruction, not concurrently.

| Evidence | Hunting rifle | 9mm pistol |
|---|---:|---:|
| Unchanged baseline matches | 1 | 1 |
| Edited free-flight steps matched | 2 | 8 |
| Edited collision segments | 1 | 1 |
| Controller entry/return pairs | 4 | 10 |
| Reset branch observed | 4 | 10 |
| Reset skipped for applied vector | 3 | 9 |
| Pending calls at destruction | 0 | 0 |

There were 12 movement-input edits. Ten were free-flight segments and all passed the unchanged actual-displacement tolerance. Each projectile's final edited segment encountered collision and was correctly excluded from free-flight comparison: the engine truncated movement at the obstacle. The 12 applied versus 10 verified counts are therefore explained, not missing verification of freely travelling segments.

Maximum logged vector error across applied free flight was {maximum:.9g} engine units; the highest error/tolerance ratio was {fraction:.6f}. Position-accounting error was zero in the verified rows. Omitting local Z would exceed tolerance in {omission_outside} of the {len(applied)} applied free-flight samples. The new branch preserves the intended component with a measurable effect on actual motion.

## What this establishes

All 14 observed controller calls dispatch through vtable 01090594 to C73170. PHYSICS_LOCAL_Z confirms that C73517's reset branch actually executes. Baselines replay it; all 12 edited requests preserve their already-copied local vector. Request values match submitted input and remain unchanged after controller return. The checked frame/stack/identity/timestep/rotation contracts succeeded in these samples. Actual movement now matches the full integrated vector, rather than the old omission pattern.

The independent timing observer reports 16 samples: two startup/no-motion, 12 moving (including two baselines), and two collisions. Movement speed decreases during flight while base speed/multiplier remain unchanged, consistent with NVO's displacement-based drag. Model endpoint speed is not itself an independent engine velocity measurement. Logged m/s values still assume the configured 70 engine units per metre.

No reported rejection, mismatch, read/identity failure, unpaired accounting, overflow, live address reuse, nesting/overlap or log cap. No open projectile lifetimes or pending controller calls at exit. All updates used one worker thread distinct from the initialization thread; that is permitted by the existing per-lifetime handling, not an error. Damage authority remained disabled and the scenery test produced no actor damage contexts.

## Remaining limits and next check

This run contains one load and no new reload, VATS, NPC firing or stress coverage of the correction. Keep the existing 310 build for a short reload/VATS regression before wider ammunition coverage or tracer changes. Ask the user before giving that next checkpoint; no new DLL/GECK work is required merely to obtain those observations.

The intentional first unchanged segment per lifetime remains a pilot limitation. Unit scale, cartridge tuning and fixed atmosphere are not independently calibrated by this run. Collision-step trajectory/energy at the exact impact time is not validated by free-flight matching; do not substitute commanded engine travel counters or the cached pre-collision speed for a future penetration calculation without resolving that distinction.

Review only: archived evidence and checkpoint documents/tools. No native edits, build, install, game launch, GECK work, gameplay or process-memory access. Installed version 310 and user test files remain unchanged. The additional donor review is separate and did not activate those mods.
'''
(PACKET/'REVIEW-1.md').write_text(review,encoding='utf-8')
checkpoint=f'''## Current combat checkpoint: 3C5 / 310 two-weapon flight accepted; reload/VATS check proposed

2026-09-15: user completed the instructed 310 test. Archive source/combat/step3c5/captures/2026-09-15-3C5-da21de37bf4f/NVOCombatCore.log, SHA256 {sha}, 50,833 bytes / 228 lines, last write {data['source_last_write_local']} local. Review source/combat/step3c5/REVIEW-1.md and review-data.json. One load, rifle then pistol, both private combinations hit scenery00106B5E and destroy normally. 14 controller/reset observations: two original baselines and 12 preserved applied vectors. Both baselines and all ten free-flight edits matched; two final collision segments are intentionally excluded. Rifle verified2/applied3, pistol verified8/applied9. Zero rejections/mismatches/unpaired/read/identity/overflow/nesting/overlap/open-life/pending-call faults reported; normal exit. Max applied vector error {maximum:.9g}, max tolerance fraction {fraction:.6f}. This directly confirms reset-branch execution and preserved local Z reaching actual movement in the tested path.

Accept limited non-VATS two-weapon gravity/drag pilot, not all flight/damage/calibration. Damage disabled. Keep 310 installed. Propose short reload/VATS regression using the same build before broader cartridge or tracer scope; ask before instructions/next packet. Initial unchanged segment per lifetime and fixed units/atmosphere remain limitations. Exact collision-time velocity/energy remains future work; engine travel counter includes commanded collision segment and is not a substitute for contact-time energy. No assistant native/game changes, builds/installs, gameplay/GECK/memory access this review.

Additional sources reviewed separately: reference/ballistics-donors-20260915/REVIEW.md. PBB/CBD uploads identical to previous archives. ESP-less tracer source has missing small_rifle_projectile.nif (archive has small_rifle_tracer.nif), shared shotgun projectile rewrite, other shared projectile settings and speed-based timers. No donors activated. Prefer selected permitted original tracer assets with NVO visual ownership later; ESP-less author terms require permission for reuse. This does not change current acceptance checkpoint.

'''
for p in (ROOT/'STATUS.md',ROOT/'source/combat/README.md'):
    old=p.read_bytes()
    if checkpoint.splitlines()[0].encode() not in old:
        first,sep,rest=old.partition(b'\n')
        p.write_bytes(first+sep+b'\n'+checkpoint.encode()+rest)
print(json.dumps(dict(review=str(PACKET/'REVIEW-1.md'),accepted=True,applied_free_flight=len(applied),omission_exceeds_tolerance=omission_outside),indent=2))
