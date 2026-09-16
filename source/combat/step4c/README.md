# Step 4C — explicit armour coverage profiles

Prepared offline. No installation, GECK compilation or gameplay test is required for this packet. Native326 / NVO0.3.26 remains installed and damage replacement remains disabled.

## What changed

`native/NVOCombatModel/CoverageProfiles.hpp/.cpp` classifies complete, stable equipped-item evidence against explicitly authored profiles. This is a pure coverage classifier, separate from the Step4A damage shadow adapter. It reports candidate coverage and preserved condition; it calculates no penetration, damage, wear or wound.

The editable source is `profiles/armour-coverage.json`. Its strict compiler generates offline fixtures used by the C++ checks. It is not an installed runtime INI/JSON loader yet: changing it requires regeneration and rechecking, and cannot alter the running game.

Two starting profiles cover the exact gear already exercised by the user:

| Item | Head | Torso | Arms | Legs |
|---|---|---|---|---|
| Combat Armor | None from this item | Partial | Partial | Partial |
| Combat Helmet | Partial | None from this item | None from this item | None from this item |

These are **initial NVO authoring proposals**, not measured mesh coverage or calibrated protection. Partial means the item may cover only part of the region, or includes different protective surfaces. It assigns no probability, protected fraction, thickness, material, facing, or skin/plate decision. The body proposal includes clothing and armour portions; this does not give trousers the resistance of a chest plate. Mesh/material review and the eventual coarse-region gameplay policy are still needed before those values affect combat.

No profile currently asserts full regional coverage. The classifier can represent explicitly authored full or unknown coverage; synthetic fixtures check those cases without granting any gameplay authority. No profile equates a coarse head hit with a helmet hit or an exposed-face hit.

## Matching and failure behaviour

- Match an exact owning-plugin name plus local FormID. Plugin-name case is normalized for comparison. A runtime load-order byte is never silently stripped to invent ownership.
- Compare the expected equip mask only to detect drift. The mask does not generate coverage and cannot identify material or an anatomical surface. Overrides changing visuals without changing the mask still need an explicit compatibility review; this is not an asset fingerprint.
- Retain each exact call-local instance and its condition, including zero condition. Neither condition nor DT decides semantic coverage here.
- Unknown equipment, unresolved origin, changed equip mask, incomplete enumeration or unstable input returns a named refusal with no partial item rows.
- Reject duplicate profile keys, duplicate instance tokens, invalid/nonfinite condition, malformed keys or masks, excessive counts and invalid extents.
- Preserve overlapping potential coverage without choosing a layer order. Empty equipped inventory never proves bare anatomy or absence of model-baked protection.

The runtime reader is bounded at32 worn items; this classifier enforces the same bound. Catalogs are limited to256 profiles. It has no engine memory reader, NVSE commands, hook, logger, file loader, serialization or mutation API. Catalog validation currently occurs per pure call; future integration should validate once into an immutable catalog, not add repeated registry-validation cost to every hit.

## Creatures and model parts

`EquipmentCharacter` is an equipment-observation domain, not a biological species claim. Humans and non-feral ghouls represented by Character can supply this evidence once origin/type resolution is proven. Their inherent protection and any toggled/baked BIP geometry remain outside worn inventory.

Creature inputs explicitly return `creature_profile_required`, even with empty inventory. Bloatflies, robots, yao guai and other Creature records must receive separate natural-protection/anatomy mappings later. This packet gives none of them zero protection and maps none of their body parts to human regions automatically.

## Verification and limits

The standalone C++ checker compiles for x86 with `/W4 /WX`. It exercises exact mapping, removal, partial/unknown/overlapping coverage, invalid input, count limits and atomic rejection. It replays all76 real snapshots from the user's two pinned4B captures and checks10,000 deterministic repetitions. Separate authoring checks exercise malformed JSON/profile definitions.

Replay tests classify already captured data only. They do not test live FormID-origin resolution, mesh coverage, exact contact surfaces, creature profiles, NPC-to-player consistency, always-on overhead or gameplay balance. The current4B snapshots still cannot satisfy the4A adapter's coherent at-impact, complete coverage, layer order, exact-speed, material, target-profile and modifier-ownership requirements. No authority flag is promoted and neither ArmourModel nor ShadowAdapter is called.

## Delivery and reversal

`START-HERE.html` summarizes the result. The package includes the new module, checks, authoring source, generated fixtures, pinned replay metadata and results. See `CHECKS.json` and `SOURCE-SNAPSHOT.json` for hashes and the exact verification result. NativeCore source and14 installed foundation/helper files are verified unchanged against the recorded4B baselines. No game rollback is needed because nothing was installed.

Suggested next packet, only after approval: diagnose exact owning-plugin/local-ID resolution for observed armour and report these coverage classifications in the live log. Keep partial coverage unresolved and damage off. Do not skip the outstanding material, hit-surface, coherent-snapshot and modifier gates.
