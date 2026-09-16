# Packet 4B: first live review

**Initial functional checkpoint passed. Stress/performance checkpoint remains pending.**

Pinned log: `Evidence/LIVE-4B-20260916-233442.log`, SHA256 `1d20983e4d196d41f485853e2eac64ac0eaa49daede615ba971eb696ec138501`.

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
