# 3G review: contacts observed; speed estimate needs a diagnostic correction

The log corroborates actor hits on shots 2, 5 and 10. Shot 10 records a critical head hit, consistent with the user's reported final VATS headshot kill. Contact capture and callback pairing worked for all eight detailed lifetimes. No contact-speed model candidate passed: native315 incorrectly requires the earlier full movement endpoint to equal the contact point. This is a diagnostic assumption to correct before armour uses speed; it is not evidence of a flight displacement failure.

## Evidence and shot accounting

Capture: `captures/2026-09-15-3G-018ec6d9b0b6/NVOCombatCore.log`, SHA256 `018ec6d9b0b6ee5c81e4a417e14057895bc4ce1fa18aa3c2096c4386183fee15`. Stable across two reads, 204,414 bytes / 841 lines, last written 2026-09-15T21:52:02.847128+12:00. Header identifies native315 / phase3G. One loaded session, no reload, normal exit.

All ten selected/created projectiles are player Hunting Rifle 00004333, standard .308 0006B53C, private projectile 0C000807. All ten have matched impact and destruction events. Repeated reuse of address FF001994 is sequential; lifetime identities remain distinct and no live-address reuse error occurs.

| Shot | Logged result |
|---|---|
| 1 | Solid-object contact 001055E0, region -1, on the first unchanged movement |
| 2 | Linked actor hit FF001978, region 0 (torso), on the first unchanged movement |
| 3, 4 | Impact on 001070C1, previously identified as the mobile-home trailer; no linked actor hit |
| 5 | Linked actor hit FF001978, region 1 (head), not flagged critical |
| 6, 7, 8, 9 | Impact on trailer 001070C1; no linked actor hit |
| 10 | Linked actor hit FF001978, region 1 (head), critical=1 |

Region names follow the earlier 3B3A body-region checkpoint. The user confirms shots 1 and 2 followed instructions, is certain only of the final VATS headshot kill, and was unsure whether another later shot hit. Shot 5 supplies that additional actor-hit evidence. The log does not independently identify VATS mode or confirm death. Its pre-hit health field is 416 and pre-health requested delta is -832 for shot 10; neither is a measured final HP loss. Damage replacement remains disabled. A subsequent unlinked blast context has zero damage fields and unknown source; it must not be counted as another rifle shot or treated as proven duplicated damage.

The detailed impact observer is capped at the first eight physics lifetimes. Shots 9 and 10 retain ordinary creation/impact/range/hit evidence but have no IMPACT_GEOMETRY or IMPACT_MODEL record. Do not claim a final-shot contact-speed measurement. Its recorded 5,448.18652 travel units are an engine counter including a full collision step, not exact source-to-contact distance. The user's maximum VATS engagement distance is not a measurement of the projectile's configured maximum range.

## What the collision data establishes

All eight collision samples have validity mask31, a single reported contact, and no optional read failure. All eight later callbacks have mask15, matching target/region and unchanged contact coordinates. Callback position equals that same contact in every sample. There are no duplicate collisions/callbacks, unpaired callbacks, missing callbacks or log write failures.

Independent recomputation from logged vectors shows that **earlier projectile position equals start plus the full proposed displacement**, within the existing tolerance, for all eight samples. Accounting delta also matches that full displacement. Endpoint errors range from 0.000473 to 0.007512 engine units; tolerances range from 0.051900 to 0.072599. However, endpoint-to-contact gaps range from 165.154 to 1,819.923 units. Native315's `pointGap <= tolerance` prerequisite therefore rejects every candidate.

This matches the supplied ShowOff source: `UpdateProjectilePosition` copies the first impact position into the projectile before dispatching its impact callback. See ENGINE-FINDINGS.json for the source path/hash; the helper is at ShowOffEvents.h:880. Earlier full-step position and later contact position are different boundary observations. Treating their difference as numerical error was incorrect.

Seven of eight contact points lie within the proposed chord at the existing tolerance. Shot 2 is the exception: off-chord distance 0.139530 exceeds tolerance 0.052894. Both first shots are also unchanged engine baseline contacts, with no verified prior NVO step. They remain separate, unavailable model cases. The six applied-step contacts, shots 3-8, have valid chord placement; the prospective partial-time model still needs evaluation against those saved inputs before any candidate can be accepted. Do not widen tolerances or silently substitute the beginning/end velocity to obtain a pass.

The reused audit helper now reports endpoint, accounting, chord and callback comparisons separately. It does not grant candidate acceptance or recompute a contact speed. `review-data.json` retains these conclusions alongside the raw audit.

## Movement and scope

There are 58 paired movement/accounting entries: eight verified baselines, 40 verified applied movements and ten collision exclusions. All 48 applied attempts comprise the 40 verified free movements plus eight applied collision movements. No rejects, mismatches, unpaired accounting, invalid hit contexts, read failures or open lifetimes are reported. The detailed ordinary rows independently cover six baselines and 33 applied movements; other matches have aggregate coverage.

`lives_without_update=2` is explained by shots 1 and 2 colliding in their first unchanged segment. Their PHYSICS_NO_UPDATE records each show one movement and one accounting entry, with zero NVO writes. The source increments this counter when applied steps are zero; it is not proof that those shots missed the hooks. A later diagnostic should label first-segment contact distinctly without altering baseline policy in this correction.

All 30 range observations are valid, with no range change/read/log failure. There were 48 eligible terrain queries and no failed query. This run does not re-exercise the already accepted 3F3 terrain correction, nor does it invalidate that acceptance.

## Decision and proposed next packet

Accept contact observability and callback correlation for the eight sampled lifetimes. **Do not accept contact-speed authority.** Keep native315 installed until the user approves Packet 3G1. No native/game/configuration/save or GECK changes were made during this review; no assistant gameplay occurred.

Proposed 3G1 purpose: correct the diagnostic boundary comparison so armour will eventually receive a supported impact-speed estimate. First evaluate the corrected geometry and partial-time calculation offline against this archived capture. Validate full endpoint against expected displacement/accounting, contact against the swept segment, and later callback against the same contact. Retain explicit baseline/ambiguous cases, existing tolerances, and speed/damage authority=0. Keep the patch diagnostic-only. Address bounded impact detail coverage so later successful shots do not silently fall beyond the first-eight limit, and clarify the baseline-contact counter. Reuse existing hooks; broaden them only if source and replay evidence establish a need.

No repeat of this unchanged packet is requested. Ask before preparing/installing 3G1; any later user check should be short and target the corrected diagnostic. Physical unit calibration, cartridge mass/energy, first-segment model ownership and eventual pre-damage integration remain separate prerequisites. The ShowOff callback currently follows damage, so its correlation alone cannot become the damage-control boundary.
