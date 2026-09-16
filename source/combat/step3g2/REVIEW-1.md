# Packet 3G2 / native317: first live review

2026-09-15. The new hit join worked for both actor hits. Neither actor hit had an accepted impact-speed estimate. This establishes useful diagnostic behavior, not readiness to replace damage. The requested Ultra foundation review is next; no additional gameplay test is requested by this review.

## Preserved evidence

Capture: `captures/2026-09-15-3G2-5c4e764753b7/NVOCombatCore.log`, 205,918 bytes, SHA256 `5c4e764753b73c258a176e4270b5b5bdbf8255ac6d35c097daa259cf89fcca63`. Last write 2026-09-15 23:08:03.831135 +12:00. Two identical reads and unchanged size/time before archiving. `capture.json` preserves the user's exact report; `audit.json` contains the reproducible field and arithmetic checks from `tools/audit_flight_capture.py`.

One loaded session, normal exit, eight ordinary Hunting Rifle/standard .308 creates, impacts and destroys. Both actor contexts preserve source, target, projectile lifetime, weapon and creation ammunition. No unmatched events, reused live addresses, overflow, invalid contexts, read failures, open lifetimes, movement mismatches or summary errors. Forty-nine movement/accounting entries reconcile as seven verified baselines, 34 verified applied movements and eight collision samples. No damage replacement.

## Shot sequence

| Shot / lifetime | Recorded impact | Diagnostic result |
|---|---|---|
| 1 | Scenery `00122CA9`, corresponding to reported rock | Engine baseline collision; no accepted NVO speed |
| 2 | Scenery `001070C1` | Candidate 783.361416 m/s |
| 3 | Scenery `001070C1` | Candidate 783.361976 m/s |
| 4 | Scenery `001070C1` | Model path differs; estimate rejected |
| 5 | Scenery `001070C1` | Candidate 774.121797 m/s |
| 6 | Scenery `001070C1` | Candidate 774.230330 m/s |
| 7 | Actor `FF001978`, head region 1 in both records | Joined before impact callback; contact geometry rejected |
| 8 | Same actor, torso region 0 in both records | Joined before impact callback; contact geometry rejected |

The sequence corroborates the reported repeated VATS misses followed by a head hit and a first-attempt ordinary torso hit. Firing mode, intended VATS selection, displayed hit probability and the reason for missing are not captured. Do not claim high skills guarantee a hit, blame the misses on NVO, or infer the VATS trajectory is correct from this evidence alone. The final long-distance torso description is consistent with lifetime 8; there is no additional ninth projectile in this capture.

## What the join established

Both actor contexts report `collision_paired=1`, `callback_seen=0`, matching contact/hit positions, known matching identities and regions. Both remain `candidate_available=0`. Zero region differences in this capture does not settle the earlier316 head/contact discrepancy or establish a universal armour-region policy.

For shot 7, logged contact offset from the movement chord is 0.0955443553 engine units against tolerance 0.0532188073. For shot 8 it is 0.0834210156 against 0.0532332973. Both full movement endpoint and accounting checks pass. Later contact position is unchanged. Rounded-log recomputation preserves these rejection decisions. The failure is not a missing join or late callback: the underlying contact geometry falls outside the current model's allowed path. Tolerances are unchanged; this review does not justify widening them.

There are four accepted scenery speed estimates and four unavailable results: one engine baseline collision, one model-path rejection and the two actor geometry rejections. Eight callbacks pair with all eight captures; no duplicates or capacity omissions. The head/torso hit-data health fields (416/208) are observed input, not proof of applied health loss and not NVO replacement damage.

## Next gate

Run the already authorized, bounded Ultra review against native317, its exact deployed files, active loaders/profiles and representative evidence. Include contact geometry, first-step/unknown-input policy, engine units, ownership, VATS/body-region semantics and the future pre-damage handoff. Separate code defects from missing evidence and unimplemented future systems. Damage implementation and activation remain gated. No source, DLL, profile, ESP/ESM or game state is changed by this review.
