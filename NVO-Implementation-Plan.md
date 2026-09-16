# NVO intended implementation plan

Recorded 14 September 2026 from the approved plan in the task “Check GECK NVSE setup” and the workspace checkpoint documents.

NVO's overall aim is a dangerous, reactive Mojave with internally consistent Fallout rules, meaningful backgrounds, consequential injuries, and NPCs whose survival matters. The concrete implementation sequence currently being executed is the eight-step combat plan reproduced below.

## Historical position recorded 14 September

For the live packet, installation and test checkpoint, read [STATUS.md](STATUS.md). The table below is the original September 14 snapshot, not the current implementation state.

| Work | Recorded status |
|---|---|
| Alternative Start steps 1–6 | User reported successful compilation and saving. Full gameplay verification remains outstanding. |
| Background expansion | Design proposals recorded; new equipment, activities, contacts and followers have not been implemented. The console-only warning edit in Alternative Start step 7 has not been reported compiled. |
| Combat step 1: foundation | Startup and dependency checks accepted from the user's test. |
| Combat step 2A: script event capture | Two captures reviewed and accepted for initial event coverage. |
| Combat step 2B1: native build/load | Source and packet prepared; awaiting the user's build/load result. No compiled or tested native DLL is recorded. |
| Remaining step 2B: native hit observation | Pending after build/load acceptance. |
| Combat steps 3–8 | Planned; not implemented. |

**The immediate checkpoint is 2B1:** build and load NVOCombatCore, confirm plugin version 200, and review its lifecycle log. The prepared source contains no native hit hooks or damage replacement. Step 2A observes existing extender events and does not establish that the custom native core can resolve damage.

The later native observer must establish current hit context and separate projectile lifetimes. Captures showed rapidly reused projectile IDs and potentially stale hit readings. Native validation still needs NPC-to-NPC, robots, VATS, incoming damage without invulnerability, and damage applied once. The accepted shotgun capture was NPC-to-player, not a player-fired shotgun damage test.

## Donor addition assessed 17 September 2026

**Titans of The New West 2.1.51d** is a candidate for a modular power-armour presentation layer: selected models, animations, weapon handling, sounds and Pip-Boy integration. The downloaded ESP includes 61 readable script sources. Its protection/stat writes, explosion modifier, perks and movement changes must be separated from presentation before integration; NVO retains one owner for protection, injury and hit reactions. No Titans content has been installed or merged.

Use exact armour identities and explicit coverage profiles at Step 4, coordinate any new handling/reactions at Step 6, and balance power-armour backgrounds at Step 8. Prepare a single-suit presentation prototype only after the current checkpoint and further approval. Preserve the author's CC BY-NC-SA 4.0 notices and credit. See the [downloaded-source assessment](reference/titans-2.1.51d/ASSESSMENT.md) for the archive fingerprint, findings, dependencies and proposed boundaries. This assessment does not authorize damage activation or change the immediate combat packet.

## Working method

Prepare one digestible packet, explain its purpose, and supply complete files and instructions. The user transfers files, handles GECK or native compilation, and performs gameplay testing. Review the result and ask before starting the next implementation packet. Reuse the existing source inventory and API evidence to keep usage efficient.

The installed NVO.esm edited by the user is the working plugin. Workspace source snapshots and release copies are not proof of the latest compiled ESM state.

## Approved combat plan

The following is the original approved plan. Its “I” refers to the assistant preparing packets; “you” refers to the user compiling and testing. Its instruction to begin with Step 1 is historical; the current position is recorded above.

---

# NVO combat: donor-based build plan

Build toward lethal combat where ammunition, armour, anatomy and preparation determine survival. Use **BallistX as the ballistics foundation**, supported by a custom NVSE DLL, NVO.esm records and loose configuration files.

I prepare each implementation packet. You transfer it, compile in GECK and test. **We complete one packet at a time and wait for your result before continuing.**

## How we will use your references

| Reference | Role in NVO |
|---|---|
| **BallistX** | Adapt cartridge data, barrel length, velocity, drag and projectile flight. Replace its independent damage calculation with NVO’s coordinated calculation. |
| **Caliber Based Damage** | Reuse its configurable weapon classification approach. Its separate damage-changing startup script stays inactive. |
| **Physics’ Based Ballistics** | Reference for projectile configuration and compatibility; BallistX supplies the flight model. |
| **Physics’ Based Spread** | Adapt controlled-shot accuracy and sustained-fire spread, integrating injuries and weapon proficiency. |
| **Simple Bleeding** | Adapt treatment hooks and timed bleeding, correcting the configuration and unequal lethality issues found in its scripts. |
| **New Blood** | Selectively adapt creature anatomy, weapon distinctions and impact reactions into NVO’s injury system. |
| **Combat AI Tweaks** | Keep its native plugin as a dependency for decision timing and weapon-selection fixes. Add NVO morale separately. |
| **Transcendence** | Selectively reference equipment, combat styles and progression. Its supplied fatigue module requires another mod and cannot provide fatigue by itself. |
| **Vanilla SWEEP** | Later source for individual weapon effects. The supplied plugin’s TTW dependencies require adapting each selected feature. |
| **KEYWORDS** | Support explicit classifications and exceptions for modded equipment. |
| **Modern Ambient Temperature** | Later optional atmospheric input for ballistics. |
| **Base Object Swapper, Animated Greetings, Idle Variety** | Reserve for equipment distribution and later NPC presentation. |

BallistX permits adaptation with credit. Simple Bleeding also requires derivative mods to have open permissions; the plan assumes NVO will meet that condition. Retain donor credits and applicable notices. [BallistX permissions](https://www.nexusmods.com/newvegas/mods/70341), [Simple Bleeding permissions](https://www.nexusmods.com/newvegas/mods/92796).

## Digestible implementation steps

1. **Establish the combat foundation.**  
   Prepare a dependency manifest, separate native project and a small NVO startup controller. Report missing dependencies once through the console. Inventory overlapping donor loaders so each enabled feature has one owner.

2. **Observe hits before changing damage.**  
   Build the native core initially in diagnostic mode. Record attacker, target, weapon, ammunition, body region and damage context. Your checks establish that ordinary bullets, shotgun pellets, melee and explosions are identified correctly before damage replacement is enabled.

3. **Introduce BallistX projectile flight.**  
   Start with existing New Vegas ammunition: barrel length, velocity, gravity and drag. Track active projectiles directly and cache their profiles. Replace the donor’s unconditional three-second projectile deletion. Use fixed atmospheric conditions initially; add weather integration later.

4. **Make armour control the result.**  
   Introduce one calculation for penetration, transmitted impact, health damage, limb damage and armour wear. Helmets protect the head independently. Material, coverage and condition affect protection. Penetrating wounds and projectile-carried poison require penetration; blunt transfer, blast and external heat use separate rules.

5. **Add wounds and advanced medicine.**  
   Introduce bleeding, limb impairment and serious trauma using separate human, animal, mutant and robot profiles. Robots receive mechanical damage rather than biological bleeding. Standard treatment handles ordinary wounds; scarce advanced stimpaks rapidly repair serious biological injuries, as you selected.

6. **Complete weapon behaviour.**  
   Add cutting, piercing, blunt, laser, plasma, explosive, fire and poison profiles. Integrate spread, injury penalties and controlled bursts. Use selected New Blood and SWEEP features through the same damage system, with cooldowns preventing repeated knockdowns from trapping actors indefinitely.

7. **Add tactical judgement and morale.**  
   Configure Combat AI Tweaks conservatively, avoiding exaggerated melee lunges and automatic prioritization based on hidden health. NVO confidence will respond to observed weapons, protection, wounds, nearby allies and casualties. Add retreat first; surrender follows as a separate packet.

8. **Balance starts against the completed combat rules.**  
   Tune background equipment and proficiency around these mechanics. Powerful starts gain meaningful advantages through equipment and experience; exposed vital areas remain dangerous. Permadeath stays a design assumption without save deletion or loading restrictions.

## Architecture and compatibility

- **NVO.esm** supplies editable records, equipment, effects and presentation; **the native DLL** owns projectile state and hit resolution; **loose profiles** supply tuning and compatibility mappings.
- The native interface exposes combat status, resolved-hit information, injury queries and treatment requests to scripts. These are new NVO interfaces, not assumed existing NVSE commands.
- Apply direct hit damage once through the engine’s damage path. Bleeding and other continuing injuries use separately attributed effects.
- Preserve attacker attribution and process each shotgun pellet independently. Distinguish an explosive projectile’s impact from its explosion.
- Unknown equipment retains its existing behaviour until classified. Unsupported native hooks leave damage replacement disabled and produce a console diagnostic.
- Persist injury state through NVSE save serialization. Rebuild transient projectile state after loading.
- **VATS uses the same armour and injury rules**, without extra player damage protection. Critical effects cannot bypass a failed penetration decision.
- Initial anatomy uses the body regions the game actually reports. Anatomical vulnerability profiles must not claim precise internal-organ coordinates.

## Your checks and delivery format

Each packet contains complete copyable scripts, exact GECK record instructions, required loose files, expected results and reversal instructions. No fragile “replace line 146” edits.

Your checkpoints cover:

- New game and reload without duplicate initialization or intrusive warnings.
- Bare head versus helmet; intact versus damaged armour; ordinary versus armour-piercing ammunition.
- Player-to-NPC, NPC-to-player and NPC-to-NPC injury consistency.
- Shotguns, explosions, robots, VATS and modded weapons without duplicated damage.
- Bleeding attribution, advanced treatment, injury persistence and recovery.
- Retreat behaviour without repeated weapon switching or knockdown loops.

**Begin with Step 1: the combat foundation and dependency packet.** Native hit control is a new development task; it must pass your diagnostic checkpoint before it becomes the authority for damage.


---

## Related Alternative Start and background direction

The existing start system is based on **Alternate Start with Delayed Main Quest by hman101**. RD.esm was excluded; The Living Desert has not been integrated in this upgrade pass.

The user-reported compiled changes are:

1. NVO.esm filename checks in the donor quest scripts.
2. Roleplay, Hardcore and Powerful background menus with donor IDs retained.
3. Original descriptions supplemented by selected start warnings and optional Courier information.
4. Quick and Custom setup. Quick preserves the current name and appearance and selects level 1; remaining character choices use the existing setup flow.
5. Clearer Mojave Express flier text explaining that signup begins the Courier story and leaving keeps the job optional.
6. Random Start reads the supplied configuration's DLC-exclusion setting.

The background expansion proposes thematic inventories, practical occupations, personal contacts, followers where appropriate, and lasting consequences across the donor's 58 origins. These are future additions, not completed background mechanics.

The recommended first prototypes are **Prospector, Brotherhood Exile and NCRCF Convict**. Start with equipment, then one usable activity, then a contact and consequences. The Prospector prototype begins with survival and salvage equipment, followed by one authored salvage job and buyer. Final equipment balancing belongs after the combat rules are accepted.

Hard exile and outlaw restrictions should persist. Resources, expertise, individual contacts and alternative ways to survive can improve without reinstatement, pardons or generic reputation resets. Other hardships must be classified individually as recoverable or permanent. Powerful origins gain concrete advantages while retaining meaningful vulnerability.

NVO is intended for hardcore, single-life play, with no save deletion, loading restrictions or forced permadeath mechanism. Becoming the Courier remains optional.

## Broader project vision

The user's 14 September Dialectic suggestion has been assessed in [Dialectic integration proposal](NVO-Dialectic-Proposal.md). Proposed role: optional AI conversations and NPC context alongside NVO's authored mechanics, beginning with one Prospector contact. This is a candidate integration, not an approved implementation packet or a change to the combat sequence.

Earlier NVO discussions also proposed deeper reputation, intimidation and reactions to drawn or aimed weapons; meaningful SPECIAL and skills; and more reactive communities, factions, trade and settlements. These remain broader design ambitions. They do not have an accepted implementation sequence in the current combat checkpoint and should not be treated as already built.

## Source references

- Approved eight-step plan: user message beginning “PLEASE IMPLEMENT THIS PLAN: NVO combat: donor-based build plan” in “Check GECK NVSE setup”.
- [Current project checkpoint](STATUS.md).
- [Combat implementation checkpoints](source/combat/README.md).
- [Current native build/load packet](native/NVOCombatCore/README.md).
- [Combat subsystem ownership and donor audit](source/combat/step1/OWNERSHIP.md).
- [Background expansion proposals](NVO-Background-Expansion.md).
- [Historical Alternative Start design](NVO-Alternative-Start.md), interpreted using the later corrections in STATUS.md.
- Broader vision: earlier “Summarise NVO Project” discussion.

This document records the existing direction and status; it does not authorize or implement the next packet.
