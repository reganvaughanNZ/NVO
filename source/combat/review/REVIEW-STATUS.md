# Pre-damage review status

## Current checkpoint: Packet 4A offline armour shadow adapter PREPARED

Step4A adds a pure typed evidence adapter to `native/NVOCombatModel`; it is not linked into `NVOCombatCore`. A preview now requires exact hit/component/application and carrier/weapon/ammunition/profile identity, verified path and real-time/VATS mode, agreement between collision and hit-data regions, modifier ownership, a coherent complete equipped-armour snapshot in outermost-to-innermost order, exact calibrated contact speed, and verified kinetic/target profiles. Unknown armour cannot become bare skin, region disagreement cannot become torso, and interval speed cannot become a midpoint.

Standalone x86 `/W4 /WX` checks pass:48 adapter checks and45 existing armour-model checks, with zero failures;10,000 repeated shadow previews are deterministic. All profiles and coefficients remain synthetic. Native325's71-file snapshot is unchanged. No DLL, hook, engine reader, log path, production armour table, game/GECK/configuration/`NVO.esm` change, installation or gameplay test exists in this packet. Damage authority remains HOLD.

Packet: `source/combat/step4a`; release: `release/NVO-Combat-Packet-4A-Offline-Shadow-Adapter`. NEXT: ask before Step4B, a guarded read-only engine-side equipped-armour snapshot reader. Step4B must still perform no health, limb, condition, inventory or effect writes.
## Current checkpoint: Packet 3V Step 3 closure audit EXECUTED

The prepared Ultra-assisted audit was revalidated and formally recorded. All 71 files in the native325/3U1 source snapshot match their pinned SHA-256 values, both raw 3U1 captures match their recorded hashes, the installed pair remains verified, and damage replacement remains OFF with zero damage hooks.

Step 3 is closed only as a bounded ballistic-flight and diagnostic foundation for the nine exact `select_on_fire` bullet profiles. This does not claim all vanilla ammunition, authoritative contact energy, armour, injury, VATS/critical policy, or laser/plasma/flame/explosive/thrown/melee/pellet support. Unsupported cases retain the complete engine or mod path.

Ultra317 damage-authority HOLD remains. A future Step 4 packet may begin a guarded read-only armour shadow adapter using the existing pure `NVOCombatModel`; Packet 3V implemented no adapter, DLL, game, GECK, configuration, or `NVO.esm` change and requires no gameplay test. Evidence and decision: `source/combat/step3v`; release: `release/NVO-Combat-Packet-3V-Step3-Closure-Audit`.

Any older text below saying that the Ultra review or Step 3 closure audit has not yet occurred is historical.

NEXT: ask before preparing the first Step 4 read-only shadow-adapter packet. Do not activate damage or broaden projectile ownership silently.
2026-09-16 update: Packet3I startup/Player record repair is now approved and prepared, with user application/GECK compilation pending. See ../step3i/CHECKPOINT-PREPARED.md. Native318 remains installed and damage disabled. Findings03/04 require saved-record and live startup verification; no new full audit. The older next-proposal wording below is historical.

2026-09-16: the independent Ultra audit of native317 is complete. Packet3H/native318 has now passed its prescribed live entry/copy/return diagnostic: [3H review](../step3h/REVIEW-1.md). Finding317-01's earlier-input observation is verified on the observed route; terminal application acknowledgement and downstream scaling remain unresolved. The material pre-damage gate remains **HOLD**, with damage replacement disabled.

See [the frozen Ultra review](ULTRA-317-REVIEW.md) and [findings register](ULTRA-317-FINDINGS.json). Their original findings remain intact; this status records subsequent progress. Older PRE-DAMAGE-REVIEW.md and INDEX-317.json preparation language is historical. Frozen audit indexes and artifacts are unchanged.

Next proposal awaiting approval: separate foundation record/startup ownership repair, preserving the user's health GMSTs and required references. Then close remaining application, model/region and admission contracts before damage implementation. No further gameplay repetition requested for 3H. Review only new code/fixes and affected invariants; do not repeat the whole Ultra audit without a concrete new reason.
