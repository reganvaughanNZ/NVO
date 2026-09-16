# NVO alternative start — first design and source audit

Historical proposal. See [STATUS.md](STATUS.md) for the current implemented scope and user-reported compilation checkpoint. Statements below describe the initial audit and proposals at that time.

Status: proposed design, grounded in local plugin inspection on 13 September 2026. No live plugin has been changed, no scripts have been compiled, and no in-game test has been performed.

## Player experience

Choose role → choose starting conditions → review → begin. Name and appearance are available before departure; SPECIAL, tagged skills and traits can use a valid role preset or be customized. Aim for under a minute excluding time spent editing appearance and loading the world. No mandatory tutorial room exploration, questionnaire, or repeated introductory cutscene.

Show the role's suggested build, equipment, caps, spawn area, faction consequences and challenge rules together. Back returns to choices without granting anything. A final Begin button commits the selection once. Random selects a role within the chosen category and shows its preview; it does not silently select a punishing scenario.

Main quest assumption pending user preference: keep a deliberate opt-in Courier route. The alternative start should not automatically assign the Courier identity. Preserving the donor's later Courier transition would replay the original introduction; that is a separate decision from keeping NVO's initial setup fast.

## Initial roster

All locations below are design targets; placed spawn references and local safety still need verification in GECK and the game. Faction backgrounds represent an origin, not automatic access to every faction quest or rank.

| Category | Start | Opening identity and kit | Proposed area |
|---|---|---|---|
| Standard | Wasteland Drifter | Worn revolver, knife, light clothes, modest supplies | Goodsprings outskirts |
| Standard | Caravan Guard | Caravan shotgun, work clothes, caravan wages | Mojave Outpost |
| Standard | NCR Trooper | Service rifle, uniform, military supplies; disclosed reputation effects | Safe position near Mojave Outpost |
| Standard | Legion Scout | Machete, throwing spears, light kit; disclosed NCR hostility | Eastern Mojave, away from an immediate firefight |
| Standard | Follower Medic | Medical supplies, modest sidearm; Medicine, Science, Speech build | Old Mormon Fort vicinity |
| Standard | Tribal Hunter | Spear, knife, hunting supplies; Survival, Melee, Sneak build | Southern Mojave wilderness |
| Standard | Prospector | Varmint rifle, repair supplies and salvage | Novac outskirts |
| Standard | Vault Dweller | Vault suit, 10mm pistol, limited surface supplies | Safe route out of a vault area |
| Standard | Brotherhood Exile | Worn laser pistol and technical kit; no automatic bunker access | Outside Hidden Valley |
| Standard | Freeside Hustler | Concealable pistol, street clothes, small stake | Freeside |
| Hardcore | Robbed and Left for Dead | Injured, almost penniless, knife; reachable water and medical help | Tested escape route near a settlement |
| Hardcore | Escaped Slave | Rags, minimal supplies, Legion enemies; no scripted unavoidable death | Tested eastern escape route |
| Hardcore | Chem-dependent Drifter | Explicit addiction and limited supplies; path to treatment | Freeside outskirts |
| Hardcore | Hunted Deserter | Damaged rifle and scant ammunition; former faction hostile | Tested route outside former faction territory |
| Powerful | Veteran Ranger | Strong rifle, ranger equipment, ammunition and medicine | Novac or Mojave Outpost |
| Powerful | Brotherhood Veteran | Power armor, training, energy weapon and cells | Verified safe staging area |
| Powerful | Enclave Remnant | Remnants equipment and training; no immunity to faction consequences | Verified safe western location |
| Powerful | Wealthy Mercenary | Combat armor, reliable rifle, generous caps and supplies | Freeside or Westside |

## Starting conditions

Role and starting advantage should be independently selectable where sensible. The hardcore and powerful categories offer curated presets for quick access.

- **Standard:** level 1, ordinary 40-point SPECIAL allocation, three tagged skills, valid trait choices, serviceable but limited kit.
- **Hardship:** level 1, same character creation budget, poorer equipment, fewer supplies and the clearly stated scenario handicap. A selected injury/addiction must have a feasible recovery path.
- **Established:** level 1 for the first fast prototype, significantly better equipment, ammunition, medicine and caps. Extra power comes from explicit resources, not hidden universal stat bonuses.
- **Veteran:** later extension with an optional level target and build handling. The donor raises levels using `AdvancePCLevel`, which can create repeated level-up screens; do not call that an instant preset until skill/perk progression has been implemented and tested.

Keep the engine's Hardcore survival switch separate from these starting conditions and show it explicitly. Do not silently change the user's combat difficulty setting. DLC preorder equipment must not flood hardship starts; grant only the selected starting kit and the necessary Pip-Boy items.

## Verified source and reuse

The stored source is **Alternate Start with Delayed Main Quest** by **hman101**, in Vortex's `Alternate Start With Delayed Main Quest-82319-1-60-1745944285` directory. `AltStart.esm` is 436,867 bytes. It is currently absent from the game's top-level Data directory. A second Vortex directory with `.1` also exists; it has not been independently compared byte-for-byte.

This is not Roleplayers Alternative Start, which was an initial search guess. The applicable source is [Nexus mod 82319](https://www.nexusmods.com/newvegas/mods/82319). Its published permissions allow modification and asset use, prohibit uploading the original file to other sites, prohibit conversion to another game and prohibit sold use. Record hman101 in credits for adapted work. These are the permissions displayed at inspection time, not a separately located license bundled with version 1.60.

The read-only extractor found 123 SCPT records and 274 embedded source blocks across script, quest and other records. This is a record inventory, not a compiler or complete dependency analyzer. `reference/altstart-inventory.json` holds the source inventory and file hash for local reference.

| Source editor ID | Observed role | NVO treatment |
|---|---|---|
| `ALTStartQ` / `ALTStartQscript` | Sequenced background, appearance, SPECIAL, tags, traits, survival and level menus, then equipment and relocation | Basis for a shorter controller with previews and a single commit |
| `ALTBackgroundMenu` | Builds background selection from a form list and confirms the choice | Adapt category/preview approach; retain stable IDs independent of display order |
| `ALTBackList` / `ALTBackUDFList` | Parallel background descriptions and function list | Replace fragile positional coupling with explicit preset definitions or validated matching lists |
| `ALTBackNCRTrooperUDF` | Outfit, reputation changes, faction relationship, starting marker and weapon lists | Reference for role-specific gear and consequences |
| `ALTBackSlaveUDF` | Minimal gear, Legion hostility, spawn marker and perk | Reference for a deliberately difficult origin |
| `ALTStartingGearUDF` | Adds gear according to wealth and tagged skills | Adapt to deterministic kits shown in the preview |
| `ALTStartUDF` / `ALTGO` | Holds or restores main-quest actors and references; handles later Courier transition | Treat as a separate, interdependent quest system |
| `ALTMojaveExpressBoardScript` | Player opt-in to become Courier | Retain only if the chosen NVO main-quest policy requires it |
| `ALTLevelQscript` | Advances player levels until the chosen target | Optional later feature; requires progression testing |

The delayed-main-quest system modifies dialogue, quests, actors and scripts well beyond the start menu. Copying only `ALTStartQscript` into RD.esm will not reproduce it. Direct FormIDs in the extracted inventory include the source plugin's master index and must not be pasted as universal runtime IDs. The donor also lists the base game, all story DLC and all four preorder packs as masters; importing records requires resolving their actual references.

Existing NVO loose scripts `NVO_InitAltStartBridge` and `NVO_FinalizeAltStartCourier` already observe the donor's later Courier transition and apply an NVO origin once. That bridge is not a complete alternative-start controller. A new NVO start should explicitly commit its own origin once rather than pretend that every origin completed the Courier transition.

## RD.esm baseline finding

RD.esm currently has six records including its header: a Player override, `PlayerHelp` ability (display name `God`), `ReganGear` leveled list, `Regan` perk and a `PowerArmorTraining` override. It contains no quest or embedded script records.

The Player override's DATA contains base health 550 and seven SPECIAL values of 9; DNAM contains +100 skill offsets. This decoding follows the [xEdit FNV NPC record documentation](https://tes5edit.github.io/fopdoc/FalloutNV/Records/NPC_.html). Actual in-game values can also be affected by later overrides and scripts. The presence of the God ability and custom perk alone does not establish that they are currently applied to the player.

Before balancing starts, restore a normal player baseline in the working development plugin and make strong bonuses conditional on the powerful preset. Preserve the user's current RD.esm first. Do not balance hardcore scenarios by merely reducing equipment while these universal player offsets remain in force.

## First implementation milestone

Build three complete paths first: Drifter / Standard, Escaped Slave / Hardship, Veteran Ranger / Established. Once the whole start-to-world transition works, expand the roster above.

Proposed new records: `NVOStartQuest`, `NVOStartController`, category and preset MESG records, three tested persistent spawn markers, deterministic kit lists and an explicit committed-state variable. These names are planned records; they do not exist yet.

Controller sequence: new-game eligibility → pending choices → optional character customization → preview → validate all required forms → apply baseline and chosen build → grant kit once → set origin and scenario consequences → move to tested marker → restore controls/Pip-Boy → mark finished. Keep progression saved, do not apply on ordinary existing-save loads, and separate menu preview from every inventory/reputation/world mutation. Define recovery for an interrupted commit so reloading neither duplicates gear nor strands the player with disabled controls.

Compile through GECK Extender against the correct masters. Test a fresh new game for each of the three paths, then save/reload after arrival. Verify final stats, inventory, faction reactions, Pip-Boy, controls, spawn safety, no second kit grant and no setup restart. Test Back and customization cancellation. If keeping delayed Courier progression, separately test opting in later and the existing NVO origin bridge.

No active GECK file has been overwritten. These notes are the design and implementation map, not a playable release.
