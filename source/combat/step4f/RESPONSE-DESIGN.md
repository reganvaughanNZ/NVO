# Packet 4F response contract, version 1

This is a definition and ownership contract, not a completed physics or damage model. Code enforces the family/delivery matrix and profile-selection boundaries. The downstream hit-resolution requirements below are the next integration contract; they are not implemented by `Select`.

## Family matrix

| Interaction | Accepted delivery | Required future response/input distinction |
| --- | --- | --- |
| Ballistic | Projectile, pellet, fragment | Per-projectile construction, mass/geometry and authoritative contact speed. Stopping and transmitted impact remain separate. Each pellet gets its own share, never the shell's full energy. |
| Piercing | Melee, thrown, projectile | Tip/contact geometry and authored piercing exposure; not bullet AP thresholds. Spear/knife examples require actual attack mapping. |
| Cutting | Melee, thrown, projectile | Edge/contact geometry and authored cutting exposure. A thrown axe may have separately budgeted cutting and blunt components. |
| Blunt | Melee, thrown, projectile | Contact area and transmitted impact; weapon damage or actor mass does not prove impact energy. |
| Blast | Explosion | Authored blast exposure, occlusion and one owner of distance falloff. Distinct from carrier impact, fragments and heat. |
| Laser | Projectile, pulse, continuous | Its own exposure/coupling definition. No conversion from vanilla damage to invented joules. Continuous beams require exposure intervals. |
| Plasma | Projectile, pulse, continuous | Separate coupling and material response from laser; no implicit shared coefficient. |
| Flame | Continuous exposure | Rate integrated over attributed exposure intervals. Particle contacts must be interpreted by a future adapter; repeated contacts are not automatic full burns. |
| External heat | Explosion, pulse, continuous | Independent thermal component; same thermal quantity category as flame, but separately bound response definitions and timing. |
| Electrical | Projectile, melee, pulse, continuous | Explicit electrical exposure/contact path and tissue/structure response. Electrical reactions are distinct from mechanical stagger. |
| EMP | Projectile, explosion, pulse, continuous | Separate electronic susceptibility and disruption ownership. Neither biological injury nor immunity is inferred by default. |

`ContactJoules` is the only physical-energy quantity named here. Other quantities are deliberately distinct authored exposure categories, with numerical units/scales and calibration still required. They must not be added together or treated as joules. The family table provides no input measurement or resistance values. Provisional gameplay tuning must retain its provenance even after numerical implementations exist.

Flamers can still use engine projectiles; `Continuous` in this contract describes the interpreted exposure, not an assumption about engine projectile classes. The later adapter must establish exposure duration and attribution. Grenade or missile movement similarly does not identify which explosion components actually exist. No speculative shrapnel or heat events are generated.

## Definitions and material authoring

A `Definition` names a family-specific surface or tissue response, condition policy and provenance. A `SurfaceProfile` names its construction and one optional binding per family. Empty means unresolved. `AuthoredCurve` declares that the later numeric response needs a reviewed curve; it does not claim the curve is already implemented. `ExplicitlyIndependent` must be an intentional family-specific design choice. No universal linear condition penalty is imposed by 4F.

These are **proposed authoring distinctions**, not calibrated profiles:

| Construction example | What later tuning must distinguish |
| --- | --- |
| Cloth/leather layers | Cutting and piercing resistance, impact transmission, heat exposure and degradation. |
| Rigid plate with backing | Projectile construction, plate response, backing/transmitted impact and partial damage to the assembly. |
| Power-armour assembly | Structural protection, padding/insulation, condition and separate electronics susceptibility. Powered armour is not automatically EMP-proof or immune to blunt transfer. |
| Hide/carapace/chitin | Natural protection with its own family responses and structural injury; not an inventory item's condition loss. |
| Robot chassis | Mechanical structure and component exposure. Electrical and EMP responses remain separate from thermal/ballistic damage. |

Material alone does not fix thickness, coverage, layers or immunity. Named custom armour can reuse a reviewed construction profile with an exact record binding; exceptional items can override it explicitly. No keyword, equip-slot mask, BIP/model toggle or traversal order supplies missing physical evidence. A visual model toggle that changes relevant protection needs an explicit state/profile mapping; it cannot silently retain an obsolete profile.

The current 4E compiler still exports coverage only. No 4F selector queries KEYWORDS, reads records, performs auto-discovery or substitutes a default for an unknown modded item. No new player dependency is introduced.

## Targets, creatures and regions

`TargetProfile` supplies a reviewed equipment policy and exact game-region mappings. Each mapped `RegionProfile` selects biological or mechanical tissue, its natural/structural surfaces and family-specific tissue responses. Different mapped regions may have different tissue kinds. Unknown regions and tissue stay unresolved.

Examples for future record review:

- Humans/non-feral ghouls: worn equipment and regional tissue definitions; headgear independently mapped from body armour.
- Bloatflies: insect anatomy and natural surfaces. No inventory armour does not mean a human torso with no helmet.
- Yao guai and other animals: their actual reported regions, natural protection and biological tissue. Species names do not automatically establish numerical resistance.
- Robots: chassis plus mechanical target regions/components; no biological bleeding from an empty armour list. Chassis damage and worn-item wear have different owners.
- Creatures with equipment/model variants: explicitly authored state mappings, not a blanket species assumption about wearability.

The 4F synthetic `thorax=42` and `sensor=9` mappings are intentionally artificial; do not apply them to game records. A body-region report is not an internal organ coordinate. `naturalSetKnown` describes completeness of an authored definition, not a verified instantaneous hit surface.

## Selector invariants

- Whole-catalogue validation precedes selection. Bounds: 512 response definitions, 128 surfaces, 128 targets, 64 regions/target, 32 natural surface references/region and 32 worn definition IDs/query. IDs are lowercase ASCII letters/digits/underscore/dot/hyphen, 1-63 characters, exact-match and unique within each table.
- Missing family entries are valid unfinished authoring but cannot produce a complete selection. Mistyped references, duplicate identities/regions, wrong families/domains/tissue types and invalid policies reject the catalogue.
- The worn query is a **set of unique profile definitions**, not an equipment snapshot. Duplicate IDs reject. A future instance adapter must preserve each real item instance separately; it must not use this set as a count of layers or items.
- Missing worn/natural completeness, an unknown region/target, or a missing response/condition rule produces an empty, named hold. Failed selection never leaks a partially selected plan.
- A successful plan preserves biological/mechanical and worn/natural/structural distinctions plus provenance. It is unordered and contains no penetration, wound-eligibility, HP, wear or stagger outputs. Even explicit absence of surfaces does not certify bare skin at an impact.
- Each query revalidates a bounded catalogue for offline authoring convenience. This is not a proposed hot-path implementation or a benchmark. A future runtime adapter should prevalidate/cache immutable catalogues and invalidate on relevant state changes.

## Shared downstream result and ownership

The later resolver/coordinator must own one result per admitted component. The following is a required integration design, not a new NVSE command/API shipped in 4F:

1. **Identity and evidence:** session, originating event, component, application, source/target and weapon/ammunition attribution; actual reported region, mode and evidence status. Real-time and VATS follow the same response rules. A queued VATS aim region cannot substitute for actual contact.
2. **Component accounting:** carrier impact, blast pulse, fragment, heat exposure and poison payload keep separate IDs, quantities and budgets. Each pellet/fragment is independent. Continuous effects use non-overlapping exposure intervals. Do not assign the full parent attack to each component or apply range loss twice.
3. **Surface resolution:** actual region coverage, known worn and natural surfaces, instance identities, coherent condition at impact and verified layer order. 4F's definition selection cannot certify any of these.
4. **Outputs with distinct owners:** direct health and limb damage; worn-item wear keyed by instance; natural/structural damage keyed by target region/component; mechanical impulse/reaction inputs; separately gated thermal/electrical/EMP and injury/payload effects. Unknown is not encoded as zero. An explicit reviewed zero is not generic immunity.
5. **Damage and stagger:** both consume the same resolved component. Stagger is not calculated from HP loss, and absorbed energy is not automatically a knockdown. Mechanical impulse, target resistance and action state need their own rules; electrical reactions are distinct. One future reaction coordinator enforces cooldowns so pellets and bursts cannot repeatedly lock an actor down.
6. **Single application:** engine direct damage is replaced/applied once, with attacker attribution preserved. Engine DT/DR, difficulty, perks, criticals, ammo modifiers, VATS and secondary effects require explicit ownership. Donor scripts must not independently repeat the same damage or stagger. Failed penetration gates penetrating payloads/critical wound effects; heat/blast/external effects have their own rules. Continuing injuries have separately attributed applications.

The existing `AdmissionLedger`, `ShadowAdapter`, `ArmourModel` and `ImpactEnergy` remain unchanged by 4F. There is no cast/bridge from this 11-family enum into the model's old five-family array. Their existing evidence requirements are not relaxed. No 4F result can be passed directly to an engine damage function.

## What remains

Numerical per-family material/tissue rules, reviewed coefficients, game record/profile bindings, actual-hit adapters, instance snapshots and output coordination remain future work. Start by integrating the reviewed kinetic preview without enabling gameplay; expand numeric family support explicitly. Runtime damage, armour wear, advanced injuries and stagger still require their separate acceptance checkpoints.
