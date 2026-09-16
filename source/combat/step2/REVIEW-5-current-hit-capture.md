# Packet 2B3 capture review - 15 September 2026

Result: partial diagnostic pass. The guarded copy-input observer and ammunition reader ran successfully. Body-hit coverage and same-process reload remain unverified. Damage replacement stays disabled; further implementation requires user agreement.

## Evidence and accepted observations

The five user-named logs plus the newer `logs/JohnnyGuitarNVSE.log` are archived in `captures/2026-09-15-2B3-e5f160c3dba7/`. Its `analysis.json` contains original timestamps, hashes, parsed rows, form lookups and consistency checks. NVO capture SHA-256: `e5f160c3dba7c148e736128a50f142ffc96e76495593cf1ef7acb25fefb33279`.

- NVOCombatCore 0.2.2 / integer 202 loaded under xNVSE 6.4.8. Both JIP 57.30 copy slots and the separate projectile-ammo guard passed.
- One successful save load, one capture session and an exit_game notification appear. No second load or new game appears. Exit notification does not exclude a later shutdown crash.
- All 600 printed provider-event sequence numbers are consecutive: 92 CREATE, 90 IMPACT, 91 DESTROY, 161 HIT_NOTICE, 160 HIT_OBJECT_NOTICE and six BLAST rows.
- Bookkeeping continued past the text cap: final totals are 141 creations, 140 impacts, 141 destructions and zero open lifetimes. No unmatched lifetimes, address reuse while live, overflow or read failures were reported. Printed lifetime associations also match independently.
- All 37 context sequence numbers are consecutive, with zero invalid contexts. Twenty-eight contexts were printed after the provider text cap. The independent 200-context limit was not reached.
- Four contexts link to projectile lifetimes with ammunition matching their creation snapshots: two 9mm SMG / 9mm rounds, one Bozar / 5.56mm AP, one laser pistol / energy cell. The final link to lifetime 136 demonstrates lifetime tracking after provider text stopped.

## Coverage limits

Thirty-three contexts are explosions with region -1. The other four are projectile contexts with region 14. Supplied ITR source identifies region 14 as Weapon (`FakeHitHandler.cpp` mapping and `OnPreDamageHandler.cpp` explanation). All four have zero health damage and positive limb damage. They are not evidence of head, torso, arm or leg wounds; their zero health values are consistent with weapon hits.

Explosion contexts include the grenade APW and Esther. All 37 context sources are the player, including 20 self-blast contexts. Eight explosion contexts target Vendortron with zero health/base damage. Self-blasts do not establish NPC-to-player damage, and a robot reference alone does not establish robot injury behaviour.

Printed provider events include .357 revolver, 9mm SMG, Bozar, anti-materiel rifle, grenade APW and 45 chainsaw hit-object notices. No melee context accompanies those notices. No shotgun or fists are identifiable in printed provider rows; unprinted later activity cannot be reconstructed. Many early targets are placed REFR objects, not actors. Form lookups use installed base records; the GRA file-internal index 01 is mapped to the observed 07 prefix as in the previous capture, not independently established through a complete current load-order export.

Every context reports caller RVA 004A52F4. One copy-input path does not establish all damage paths. Coalesced classic notices cannot be compared one-for-one with context counts or used to infer duplicated damage. The missing ordinary body/melee contexts may reflect test conditions or observer coverage; this capture does not establish the cause.

Outstanding: ordinary anatomical body hits, shotgun pellet contexts, melee, NPC-to-player and NPC-to-NPC damage, meaningful robot damage, VATS, same-process reload and actual damage application exactly once. Do not enable damage authority on this evidence.

## Extender logs

Current nvse.log confirms these integer versions loaded correctly: Anh 131, ITR 20202, JIP 5730, JohnnyGuitar 525, NVO 202, ShowOff 184, SUP 855 and ZeGaryHax 0. ITR OnMCMUpdate precompiled successfully; no script precompile failures appear. Successful loading alone does not establish every function's compatibility.

The supplied root JohnnyGuitar log dates to June 2025 and reports 516. The root kNVSE log dates to 29 August 2026. These are historical data, not today's loaded-plugin evidence. kNVSE is absent from today's xNVSE loaded-plugin list.

The newer `logs/JohnnyGuitarNVSE.log` reports 525 and the existing FadeToBlackAndBackQuickHalfsISFX editor-ID collision between OldWorldBlues.esm 0400C6DD and DeadMoney.esm 02014085. The same pair was documented before this DLL installation. No NVO record is named; this is not a dependency version mismatch.

nvse.log line 2253 reports `plugin has data in save file but no handler` during preload. The line does not identify the plugin. Successful load and subsequent quicksave do not prove every plugin's saved state restored. NVOCombatCore 202 implements no serialization, so this is not evidence of a failed NVO injury-state restore. The supplied newer xNVSE source has different, more explicit warning text and cannot identify this installed binary's unlabelled warning. Retain it for focused follow-up; do not delete or rewrite saves to suppress it.

## Proposed next packet, pending approval

Continue Step 2 with a small diagnostic coverage packet to distinguish ordinary body hits, weapon hits, melee and blasts through an appropriate additional observation point. Reuse available extender interfaces after verifying installed-version coverage. Compare with the existing copy observer without damage writes, and preserve bounded detail across a reload. Include a short controlled live-target check so geometry hits, weapon hits, immunity and already-dead targets cannot masquerade as missing actor-damage events.

Only workspace documentation and archived evidence changed. No DLL, ESM, game configuration or save was modified. No build, GECK operation or gameplay test was performed by the assistant.
