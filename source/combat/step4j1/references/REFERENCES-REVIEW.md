# Review of the three additional user reports

Use these reports as a research index and proposed authoring guidance. They do not establish record bindings, material coefficients, anatomical coverage or damage applications. All three were read in full, including every table cell and available note/header/footer/comment story. Original DOCX files were unchanged; no catalogue values or FormIDs entered profiles or native code.

The armour and creature reports describe historical 4E/native327. The weapons report explicitly defines NVO as an unrelated NVAO/WAP animation overhaul stack (paragraphs 10 and 546). Its dependencies, patch recommendations and load-order instructions do not describe this repository and are not adopted.

## Input receipts

Full report text and structured extractions remain local. This repository includes the assessment, receipts, source checks and extraction utility; paragraph references below identify the local source documents.

| Report and full extraction | Body paragraphs | All paragraphs / nonempty | Tables / rows / cells |
| --- | ---: | ---: | ---: |
| Armor and Clothing (local extract) | 792 | 798 / 794 | 16 / 168 / 693 |
| Armored Creature Variants (local extract) | 303 | 309 / 305 | 8 / 55 / 212 |
| Weapons (local extract) | 632 | 638 / 633 | 14 / 174 / 522 |

[EXTRACTION-RECEIPTS.json](EXTRACTION-RECEIPTS.json) records original SHA256 hashes, sizes, paths and extraction hashes. Companion JSON preserves paragraph/table locations and relationships. Paragraph citations below refer to document.xml, including cells. Each report contains two empty footnote and two empty endnote separator entries, but no substantive notes or comments. There are no external hyperlink relationships, drawing nodes or alternative imported content chunks. Generic community-source attributions do not verify individual claims. No page-layout acceptance is claimed.

## Useful decisions

**Reuse definitions with exact bindings.** Apparel paragraphs 19–22, 61–118 and 779–787 fit the existing 4E family-and-exception approach. Every supported ARMO still requires reviewed origin, mask and independent head/body extents. Cosmetic names, faction, condition, materials and powered state remain separate attributes. Proposed family names and assignments are research candidates.

**Preserve distinct protection owners.** Use existing worn-item, natural-protection and mechanical-structure contracts. BIP/model appearance does not prove a worn ARMO instance; absence of a player-like outfit does not prove equipment impossible. The current reader requires Character form type 0x3B; a human/non-feral-ghoul species list must not replace runtime eligibility checks. Robot, natural-surface and variant-family mappings remain unknown until explicitly reviewed.

**Organize attack research by delivery and effect ownership.** The weapon list supplies candidate pellet, beam, flame, thrown/melee, explosive, electrical/EMP and delayed-effect cases. A weapon, projectile notification, actor effect, hit transaction or copy receipt is not a committed application. Future adapters must establish component budgets, recipients, intervals and exact-once application. Vanilla damage and catalogue DT do not measure kinetic energy or material resistance.

## Selected local verification

[LOCAL-SOURCE-CHECKS.json](LOCAL-SOURCE-CHECKS.json) pins inspected sources and line references. These checks establish source contracts, not installed-record contents.

| Finding | Source and consequence |
| --- | --- |
| Equip masks and model state are separate. | JIP GameForms.h:712–800 defines 20 part bits and separate models/flags. CoverageProfiles.cpp:52–97 compares masks independently of authored extents. Reject apparel paragraphs 100–105/599/687 where full-body/head or equal-mask assumptions imply coverage. |
| Missing equipment does not mean uncovered. | ArmourSnapshot.cpp:234–237 returns UnsupportedTarget outside Character type 0x3B; CoverageProfiles.cpp:52–58 requires a creature profile. Creature paragraph 8's uncovered conclusion is incorrect. |
| Only two exact apparel bindings currently exist. | Retained armour-tags.json binds Combat Armor and Combat Helmet. Apparel paragraph 422 does not establish reinforced/Mk II support. |
| Creature data needs separate provenance. | JIP GameForms.h:925–978,1129–1153,3116–3138 separates template/effect inheritance, inventory, model lists and body-part data. This verifies available data distinctions, not blanket effect-only protection or species wearability. |
| Response and application identities remain distinct. | ResponseDefinitions.hpp:33–76 separates protection/tissue/equipment policy; MaterialPreview.hpp separates worn condition from natural/mechanical structure loss. JIP GameProcess.h:20–65 and ImpactBinding.hpp:9–30 do not prove an effect executed or identify its application. |

## Deferred work

All catalogue statistics, ammunition/DLC assignments, item availability, holdout flags, unique behaviour, creature DT/DR/HP, materials, patch history and compatibility claims remain unverified. Weapons paragraphs 23/532 versus 561 even conflict on Weathered 10mm modification support. No numeric calibration seeds are adopted.

A later small offline inventory should retain exact origin **and separate winning-override evidence**, template/effect inheritance, real worn instances where supported, model/state identity, literal regions and binding provenance. Creature/state records need their own schema, not rows forced into the ARMO-only TSV. Start with representative known apparel, one variant, one natural target and one mechanical target before expanding. This reference review added only extraction/review files; it performed no game access, builds, installation, web research or gameplay-authority changes.
