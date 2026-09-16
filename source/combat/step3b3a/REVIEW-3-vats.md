# Packet 3B3A VATS repeat — bounded observer checkpoint accepted

User sequence: first load, Hunting Rifle pilot in VATS targeting head, torso, left/right arms, left/right legs and weapon; second load, 9mm pilot. The conversation identifies this as the repeat VATS check for both weapons. VATS use is user-attributed; this DLL does not log an explicit VATS-mode bit. The precise mapping of the prior stress capture's final two runs/shots is no longer needed to assess this new capture.

Read game-root log directly and archived on 2026-09-15 at `captures/2026-09-15-3B3A-vats-2e0346c2642c/`. SHA256 2e0346c2642c2e3e8dbb9a6a02f515fceb9533431c81627f8205cb65b6851ec8, 290,562 bytes, last write 12:04:28.694082 local. 1,452 lines, header 0.3.4 / phase 3B3A. Successful first load, successful same-process reload, and normal exit_game. Process-wide log limit was not reached. Native/game files were not changed by this review.

## Recorded results

| Evidence | Hunting Rifle, first load | 9mm, second load |
|---|---:|---:|
| Matched private projectiles created / destroyed | 13 / 13 | 17 / 17 |
| Recorded impact callbacks for those projectiles | 12 | 17 |
| Timed lifetimes, all completed | 8 | 8 |
| Timing steps | 20 | 16 |
| Valid moving steps | 4 | 0 |
| Pilot hit-input contexts | 9 | 16 |
| Requested region categories present | All 7 | All 7 |

Both pilot weapons generate contexts for torso=0, head=1, left arm=3, right arm=5, left leg=7, right leg=10 and weapon=14. Mapping verified in supplied JIP GameForms.h BGSBodyPartData enum; exact source paths and hashes are stored in analysis.json. The body-part indices refer to engine regions, not internal organs or precise anatomical coordinates. Every one of the 25 pilot contexts is linked to its projectile lifetime with matching recorded/current ammunition: 0C000803 for rifle, 0C000802 for pistol.

The four rifle moving steps agree with configured engine-unit speed within 0.000149%. All other timed steps are initial no-motion or collision. Each of the eight timed pistol shots goes directly from startup/no-motion to collision on the next sampled call. Those rows are correctly excluded from free-flight speed comparison; do not infer independently calibrated pistol speed during VATS or a hitscan conversion from this. Prior ordinary-flight speed acceptance remains valid.

All 16 timed lifetimes close without invalid reads, overlap, blocked/pending updates, per-shot step caps or nesting-limit hits. Both final timing/preview summaries have zero open samples, identity mismatches and read failures. Hit-context and damage-event summaries have zero invalid entries. No live-address reuse or table overflow is reported. The private rifle lifetime 86 has a matched destruction with no preceding impact callback; this is a completed retirement, not a missing destroy. Its exact termination cause is not logged, so do not assume every fired projectile hit an actor.

## Boundaries and remaining qualifications

Each capture starts with two unpaired ordinary-NPC impact/destruction callbacks, weapon 0007EA24, without a creation captured in that session. They are separate from the private pilot tracking, consistent with the previously observed loaded-save boundary. Ordinary projectile lives remain at first reload (one) and final exit (two), while private timing/preview samples are closed. Do not mistake shutdown/capture reset for proof of a leak or claim zero unmatched callbacks overall.

Session 2 reaches the classic event stream's 600-row cap. Independent hit-context, flight-preview, timing and final summaries continue, including later weapon-region hits, so the targeted region-input evidence survives. The overall logger does not truncate this run. No new stress repeat is needed.

Critical and weapon-break flag inputs occur in the capture; these are observed input records, not proof of NVO damage application, penetration, limb impairment or balance. The JIP-only 0x80000000 flag is labelled ArmorPenetrated in supplied GameProcess.h and must not be mistaken for a VATS flag or new NVO penetration result. Weapon-region inputs must remain distinct from actor body injuries. Logged health/limb numbers are input context, not measured committed losses. No native damage or flight writes are enabled. This test does not establish future gravity/drag behaviour in VATS, in-flight reload safety, unobserved concurrent return paths, engine metres or frame-rate performance.

## Decision and next step

Accept the bounded observer checkpoint under the user's stated VATS test conditions: correct private weapons/ammunition, all seven requested hit-region categories for both weapons, completed sampled lifetimes and reload/exit recovery. This new capture addresses the prior stress log's truncation and run-identification gap. Do not request another unchanged baseline test.

Keep installed 304 and the existing NVO.esm / NVOFlightPilot.esp configuration. Ask before preparing the next gravity-and-drag pilot, whose purpose is bullet drop and velocity loss for these same two private profiles. Verify supported velocity/vector write ownership and units before enabling flight, and preserve bounded logging capacity for future reload/exit diagnostics as needed. Leave damage/armour/injury systems disabled until their own implementation and validation checkpoints. This review prepared and installed no new packet.
