# Native317: deployed state and legacy record ownership

Read-only follow-up to the 3G2 playtest and Ultra foundation review, 2026-09-15. No game files changed. `DEPLOYED-317.json` records the installed hashes, activation lists, loose NVSE file inventory and embedded plugin source inventory. `MASTER-CLOSURE-317.json` adds the required RD master. Raw RD subrecords and a comparison of Player overrides are retained separately.

The deployed DLL and PDB match the 3G2 release and installation receipt. All 53 protected files match their pre-installation hashes, including plugin records, profiles and activation lists. The activation list names FalloutNV.esm, NVO.esm and NVOFlightPilot.esp; NVO.esm also requires the DLC masters and RD.esm. The private pilot contains two weapons, two ammunition records and eleven projectiles, without scripts.

The loose NVSE startup directory contains only the ITR MCM loader (plus Vortex markers). No loose BallistX, Physics Based Ballistics, Caliber Based Damage or legacy NVO combat loader was found. This is a directory and embedded-source inventory, not proof of all archive/native execution. The live log likewise explicitly leaves BSA/execution auditing unverified.

## Findings from required records

- The foundation script is in **RD.esm**, not NVO.esm. RD quest `01000DBF`, `NVOCombatBootstrapScriptQ`, references script `01000DBE`; quest DATA begins with flags byte 1. The script has 1,230 bytes of compiled data and retains repeated initialization/status PrintC calls on load. Its source is copied verbatim to `RD.esm-NVOCombatBootstrapScript.txt`. This identifies a concrete source for the earlier console-spam report; the combat log itself does not capture those console lines.
- RD overrides the base Player record: its DATA health is **550**, compared with **100** in FalloutNV.esm, and its seven SPECIAL bytes are 9 rather than 5. NVO.esm has no Player override. RD also inserts its `ReganGear` leveled item into the Player inventory. These are real inherited base-record changes. The current save's resolved health and the user's earlier exact 596 HP are not proven by the base record alone.
- RD contains `PlayerHelp` and a large `Regan` perk, plus a Power Armor Training override. Their presence alone does not prove they are applied; the Player record has neither PRKR nor SPLO fields. Do not attribute the live 416/208 hit inputs to these perks without tracing application.
- NVO retains the Brahmin Baron hit script `ALTRichKidHit`. `ALTBackRichKidUDF` registers it for player attacker/target OnHit callbacks; `ALTQscript` also contains its registration. The function separately calls DamageAV health or Kill according to carried caps. This is a conditional second damage path that a future coordinated resolver must migrate or explicitly exclude. It is not evidence that the user's current test character runs this background.
- NVO's five GMSTs include health level/endurance tuning. Leave these user-authored settings intact during this review; record their values in the master-closure evidence before future balancing.

## Implication for the next packet

Bring a deliberate RD dependency/record migration ahead of damage balancing. Preserve necessary NVO startup behavior and references while removing unintended inherited Player overrides through reviewed record changes. Do not delete RD.esm or just remove its master entry. Existing saves may retain actor changes, so file cleanup alone cannot promise to reset a saved character.

The next implementation scope is subject to the Ultra findings and user approval. Native317 and all game records remain unchanged here. No gameplay, GECK compilation or new test request was performed.
