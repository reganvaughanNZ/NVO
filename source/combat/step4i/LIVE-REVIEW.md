# Packet 4I live review: copy association passed, callback follow-up required

Reviewed the user's completed two-hit/reload/one-hit capture. Pinned log SHA256: `97a8bc9a614b926b950e2797267007648e81b6fe090759ebf9e9a876e8e80fc2`. Full machine-readable joins and file verification are in [LIVE-REVIEW.json](LIVE-REVIEW.json); the raw log remains local and excluded from Git.

| Hit | Session / generation | Transaction / copy | Armour sequence / epoch | Result |
| --- | --- | --- | --- | --- |
| 1 | 1 / 3 | 1 / 1 | 1 / 4 | Exact copy, complete equipment and contact joined |
| 2 | 1 / 3 | 2 / 1 | 2 / 4 | Exact copy, complete equipment and contact joined |
| 3, after reload | 2 / 6 | 3 / 1 | 1 / 7 | New generation and reader epoch; all joins matched |

All three use the standard 9mm pistol/ammunition (`000E3778` / `0008ED03`) against the same living Character target, with both reported region IDs equal to 0. Combat Armor and Combat Helmet (`00020420`, `00020426`) were fully enumerated at full condition. Their instance tokens changed and traversal order reversed after reload without confusing the copy joins. The first two projectiles reused a reference ID but retained distinct lifetimes.

There were no copy-scope rejections, stale snapshots, region disagreements, transaction leaks, diagnostic omissions or recorded movement mismatches in this capture. One startup banner and a normal exit were recorded. All three speeds remain observed engine-segment estimates; none qualifies as exact contact speed. This validates only the narrow diagnostic copy association, not atomic impact state, component/application ownership, all weapon types or performance under stress.

## Separate reload gap

Session 1 delivered two ITR pre-hit and two pre-health callbacks. Session 2 logged successful handler registration, but the third hit delivered neither callback. Native transaction, copy, armour, contact and actor-value observations continued; the actor-value log records health reduction after that third hit. This is a missing diagnostic stream, not evidence that damage stopped.

A separate source review confirms copy validity does not depend on those callbacks. Current registration code removes/readds handlers on activation; local xNVSE source explicitly revives readded callbacks, so a deferred-removal bug is **not** established. ITR flush-on-load events and listener-probe readiness are potential investigation boundaries, but their live state is absent from this capture. The callback module itself is unchanged from retained native322. Cause remains unestablished.

Next proposed packet: **4I1**, diagnose and restore reliable ITR callback emission across reload before advancing the damage pipeline. Do not repeat the unchanged 4I copy test or claim callback readiness from a registration return alone. Preparation/install remain separate approvals.

The installed DLL/PDB and 13 protected game plugins/configuration files still match installation evidence; RD.esm remains absent. Review used read-only game access and did not launch/close the game, install files, rebuild code or enable gameplay writes. The 530 offline checks remain historical preparation evidence, not fresh runs during this review.
