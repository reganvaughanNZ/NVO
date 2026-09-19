# Packet 4I1 live review — passed within the requested scope

The completed check contains one standard9mm torso hit before reload and two after. All three received one ITR pre-hit and one pre-health callback inside their corresponding native transaction. The previous callback gap did not recur in this capture.

Pinned capture: `Evidence/LIVE-4I1-20260919.log`,82781 bytes,343 lines; SHA256 `2c04f852df0896178b71129e2e15ade1ed4b02c27ee0f1582b9215608ea45857`. `tools/review_combat_4i1.py` reparses the capture and records structured evidence in `LIVE-REVIEW.json`. An independent read-only review agrees with the bounded pass.

| Session / transaction | Pre-hit / copy / pre-health stage lines | Copy generation / reader epoch | Return line |
| --- | --- | --- | --- |
| 1 / 1 | 78 / 81 / 101 | 3 / 4 | 107 |
| 2 / 2 | 208 / 211 / 231 | 6 / 7 | 237 |
| 2 / 3 | 280 / 282 / 302 | 6 / 7 | 307 |

Each callback stage matched identities, read valid arguments and remained untainted. Each transaction returned with one pre-hit, one copy and one pre-health observation. Callback summaries at142/342 report1/1 before reload and2/2 afterward, with zero invalid arguments.

Both registrations were positively present after every registry check. Each session performed exactly four checks: binding and loops2,32,64. The initial Set added/revived each callback; subsequent checks observed existing registrations without adding/reviving them. All scheduled checks finished before that session's tested hits. No callback-gap request or recovery was needed, so the recovery branch was not exercised live. The cause of the old failure and permanent prevention remain unproven.

The three copy/armour/contact joins remained valid. The same target `0011A8D9` wore full-condition Combat Armor `00020420` and Combat Helmet `00020426`; instance tokens changed across reload and the reader epoch advanced4→7. The order remained helmet then body in this capture; order is not armour layering. Weapon/ammunition `000E3778`/`0008ED03`, reported hit/contact region0 and unique projectile lifetimes agree throughout.

No scope, inventory-read, transaction, callback-validation, correlation, movement-diagnostic or log failure appears in the relevant summaries. No open lifetimes remain. One startup banner was logged; the log ends with normal exit. All three contact-speed results remain observed engine-segment estimates, not exact impact speed. No model-owned flight steps were used for these short contacts.

Fresh read-only file checks matched the installed DLL/PDB and21 protected game/dependency/configuration files to installation evidence. RD.esm remains absent. No code change, build, fixture rerun, installation, game launch/close or gameplay write occurred in this review. The138 offline checks are prior preparation evidence.

**Accepted:** native329 callback delivery and diagnostic copy association for these three standard9mm humanoid torso hits across one reload. **Not accepted by this evidence:** all weapon families, gap-triggered recovery, exact contact speed, coherent at-impact armour, component/application identity or committed damage. Damage, wear and stagger authority remain disabled.

Next, ask before returning to native damage-component/application diagnostics, to distinguish primary hits and secondary effects without counting damage twice. No unchanged repeat of this callback test is required.
