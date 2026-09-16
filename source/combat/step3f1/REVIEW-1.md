# Packet 3F1 playtest review

The diagnostic checkpoint is accepted: it captured the previously hidden long-flight failure in full. The flight fault is **not fixed**, so the complete 3F flight checkpoint remains pending. Both post-reload HP shots have linked actor hits, and the farther shot has a verified edited free-flight segment.

## Capture and shot order

Reviewed the user-run game-root log, archived unchanged at `captures/2026-09-15-3F1-77ebadbd30fd/NVOCombatCore.log`. SHA256: `77ebadbd30fd811b74b5c72e088cce8429c6f6845c846420d2e5515a110ffdc2`. Native312 / 0.3.12 / phase3F1. Two loaded sessions, one reload, six projectiles, normal exit.

| Shot | Session | Ammunition | User report | Log evidence |
|---|---|---|---|---|
| 1 | 1 | Standard .308 | Miss | Impact reference001070C1, no linked actor hit; movement checks passed. |
| 2 | 1 | .308 AP | Miss | Impact reference001070C1, no linked actor hit; movement checks passed. |
| 3 | 1 | Standard .308 | VATS miss, clarified by user | No impact callback; displacement mismatch at step392. Subsequently destroyed. |
| 4 | 1 | .308 AP | Hit, intended to miss | Linked actorFF001978, region1; baseline and one edited step verified before collision. |
| 5 | 2 | .308 HP | Close-range VATS | Linked actorFF001978, region0; collision during the initial unchanged movement segment. |
| 6 | 2 | .308 HP | Farther-away VATS | Linked actorFF001978, region0; baseline and one edited step verified before collision. |

VATS and aiming intent are user-provided context, not directly recorded mode flags. Shot4's hit is correctly linked, but the log does not establish why an intended miss hit. Misses alone are not failed flight checks. The two HP shots confirm selected HP after loading; they do not establish that the game preserves HP selection across saves.

All six selections are independently corroborated by creation weapon/ammunition/private projectile: ordinary Hunting Rifle00004333, standard0006B53C -> 0C000807, AP0013E442 -> 0C00080D, HP0013E443 -> 0C00080E. All six projectiles were destroyed and no lifetimes remain open.

## Newly captured failure

Shot3/lifetime3, session1, step392, first failure report:

- Engine projectile age5.84560537s; accepted integration elapsed5.79860043s. These counters are different and must not be substituted for each other.
- Expected displacement: `(-53.8090314, -176.442057, -39.298344)` game units.
- Actual displacement: `(-53.8046875, -176.445312, +17.9736328)`.
- Start position: `(-105027.383, -125735.789, -2065.97363)`.
- End position: `(-105081.188, -125912.234, -2048)`.
- Vector error57.2719771 against tolerance0.06863998; position residual zero.
- Submitted and returned local request identical. Controller target00C73170, 393 paired movement/accounting/controller entry/return/commit observations, reset observed, no pending controller request. Contacts/impacted observations both zero at the accounting check.
- Four failure-detail rows complete; no report-write failure or cap omission. This failure is beyond the normal 64-entry per-lifetime trace limit.

The actual displacement agrees with the observed start/end positions. Almost all disagreement with the requested movement is vertical: the projectile ends exactly at Z=-2048, despite a downward request. This is consistent with a height/terrain boundary adjustment, but **the responsible branch, boundary source, and any loaded-cell condition remain unproven**. Do not widen tolerance or treat every displacement mismatch as an ordinary boundary.

Read-only follow-up inspected the previously captured position-commit routine00575830 and accounting routine009C4E60, plus supplied JIP, ShowOff and Stewie sources. The old position-commit snapshot contains a jump at00575A7F matching JIP's `SetRefrPositionHook` installation site. Supplied JIP source gates its special synchronized-position behavior to player reference14; that alone does not implicate it in this projectile fault. No exact -2048 clamp branch was established in this review, and an old snapshot is not proof of the currently loaded instruction bytes. No game memory or installed code was changed.

The existing guard stopped subsequent NVO movement edits for the rejected projectile; its counters show153 later movement/accounting entries with no additional NVO integration. This does not restore the private projectile to its original stock configuration or prove equivalent vanilla flight.

## Verification and limits

`tools/review_combat_3f1.py` verifies the immutable capture and writes its complete evidence to the adjacent `review-data.json`:

- Summaries report400 matching edited movements and5 verified baselines, from405 applied attempts and1 mismatch. Four applied attempts end at collision boundaries and are excluded from free-flight verification.
- Independent routine-detail audit:72 matching edited movements,5 baselines,82 paired controller/reset observations,5 collision exclusions. Maximum detailed matched vector error0.00859376437 game units, at most16.64% of its allowed tolerance.
- Shot5 accounts for session2's `lives_without_update=1`: it has a paired movement/controller/accounting route but collides before baseline verification. It is not evidence of a missing callback or an additional displacement failure.
- No unmatched/reused live lifetimes, overflow, identity mismatch, read failure, unpaired accounting, invalid timing context, or report-write failure in the summaries. One reload clears transient tracking and both HP shots occur afterward.
- NVO damage replacement remains disabled. Recorded hit/health input values do not prove final health loss. The standard/AP/HP profiles still deliberately share the standard .308 flight tuning; realistic variant calibration is not claimed.

No gameplay or GECK operation was performed by the assistant. No native source, DLL, PDB, configuration, plugin record or activation file changed during review.

## Proposed next packet, awaiting permission

Trace the specific height adjustment using the existing evidence and exact engine/provider code, then prepare the smallest supported correction or explicit handling of an engine boundary. The purpose is to resolve long-flight misses without weakening the displacement guard. If the exact path cannot be established offline, identify the smallest missing read-only observation before changing flight behavior. Preserve ordinary collisions and keep damage authority disabled.

No additional gameplay test is needed before that work. HP selection persistence, physical unit calibration, the initial unchanged movement segment and contact-energy handling remain separate outstanding work. Do not advance to armour authority on this result.
