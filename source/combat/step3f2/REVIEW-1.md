# First3F2 playtest: normal movement passes; correction not exercised

The installed native313 loads and its ordinary flight checks pass. The failed-terrain correction was **not exercised**, so that checkpoint remains pending. No new native packet or game change is required for the next observation.

Capture: `captures/2026-09-15-3F2-31ccf22118c2/NVOCombatCore.log`, SHA256 `31ccf22118c2711f61712572fbd354a1e3a3de6fd8bbd7795d28eaa64ddb8c5d`,79,471bytes/354lines, last write2026-09-15T20:13:31.977070+12:00. The log has three loaded sessions, two reloads, three shots and a normal exit. User context: shot1 repeated the miss, shot2 far HP VATS headshot, shot3 same-distance miss reported as HP.

| Shot | Actual creation ammunition | Logged result | Engine projectile age at impact |
|---|---|---|---|
| 1 | Standard .308 | Impact001070C1, no linked actor hit | 0.172s |
| 2 | .308 HP | Linked actorFF001978, region1; user reports VATS headshot | 0.109s |
| 3 | Standard .308 | Impact001070C1, no linked actor hit | 0.187s |

The misses are consistent with the user's account of missing the intended target, but both projectiles hit the same reference quickly. Neither repeated the earlier six-second flight into missing-terrain handling. Reference001070C1's exact record type/name was not resolved in this review.

For shot3, both selector and creation independently identify standard .3080006B53C/private0C000807, not HP0013E443/private0C00080E. A second reload occurs immediately before it. The previously reported ammo-selection reset is a possible explanation, but this log does not record equipped ammunition at save/load and cannot establish its cause. This is not a selector/creation identity mismatch.

## Verified evidence

`tools/review_combat_3f2.py` audits the immutable capture and writes adjacent `review-data.json`.

- All three weapon/ammunition/private-projectile selection and creation pairs match. One linked HP actor hit, three matched impacts and three destructions; no open lifetimes.
- Three verified baselines and ten matching edited free-flight comparisons, independently checked against expected vectors and the unchanged tolerance. Sixteen paired controller/reset observations and three collision exclusions.
- Thirteen eligible terrain-query callbacks:4,3,6 across the three sessions. **Zero failed queries, zero corrections, zero corrected-movement verifications.** This establishes ordinary wrapper execution, not execution of its height-writing branch.
- Zero PHYSICS_REJECT, displacement mismatches, disabled physics, unpaired accounting, invalid timing contexts, identity errors, overflow or log-write failures. Reloads reset the transient captures cleanly.
- NVO damage replacement remains disabled. The recorded hit input is not a measurement of final health loss. VATS/aiming intent are supplied user context.

## One remaining observation, same build

Use the ordinary Hunting Rifle and confirm **standard .308**. From an elevated outdoor position, fire **one shot outside VATS, roughly level across unobstructed open space**, with distant terrain below the line of fire. Avoid the tank, buildings or nearby ground in the bullet's path. Do not aim steeply upward or at the ground. Wait15 seconds, then exit and report completion; no reload or HP repeat is needed.

Purpose: give one missed bullet time to leave the available terrain area and exercise the failed-query correction. The inspected terrain-query path is generic projectile movement, so a VATS miss is not required for this check. A different trajectory may still hit terrain or expire without invoking the branch; that would remain inconclusive. Do not keep repeating shots indefinitely or claim a pass from the absence of errors alone.

Read the next game-root log directly and archive it before another launch. Require a failed-query correction and matching accounting for the same session/lifetime/step, followed by clean lifetime completion. Keep native313 and its current files; no build, install or GECK edit occurred during this review.
