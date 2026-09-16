# Packet 3M — armour inputs and damage ownership

Status: design/reference packet, 2026-09-16. No runtime reader, new NVSE command, native damage implementation, GECK edit or installation is supplied by this packet. Native320 stays installed with damage replacement off. The original Ultra317 audit remains the baseline; this defines its requested contracts rather than claiming its runtime gates are closed.

## Decisions

1. One resolved attack component has one damage owner. Observers, visuals and diagnostics never apply an additional copy of its damage.
2. Every projectile family is part of the final NVO design. Bullet flight support is not evidence that laser, plasma, flame or explosion replacement is implemented. Each family needs its own adapter and checkpoint. Until supported, retain its existing engine behaviour.
3. Retire the Brahmin Baron's caps-based outgoing/incoming damage and instant-kill callback. Do not port it to the coordinated model. Keep the wealthy background and unrelated starting equipment/location; choose a replacement benefit during the later review of all backgrounds. Runtime retirement is still pending.
4. Keep the user health formula settings independent. Difficulty damage neutralization and NVO difficulty presets remain proposed, not activated. No hidden change to the user's difficulty slider.
5. Permadeath guides balance only. No deletion of saves, forced ironman or restriction on loading. Medicine remains recognizable and powerful; detailed physiology is deferred to the medicine step.

## Modular responsibilities

| Module | Owns | Must not do |
|---|---|---|
| Classification/profile loader | Explicit stable form keys, family, component definitions, profile revision, exceptions | Infer final behaviour solely from an editor name or weapon skill |
| Engine adapters | Guarded shot/hit identity, current ammo, verified body part, armour instances and effect context | Substitute equipped ammo after firing, stale last-hit data or nearby events |
| Flight | Family-appropriate transport, admitted projectile lifetime, collision evidence | Apply health damage or run bullet drag on a beam |
| Pure armour resolver | Material/coverage/condition response, penetration, transmitted impact and thermal dose | Call the engine, alter inventory, read globals or consult log budgets |
| Application coordinator | Admission, component identity, ownership, attributed health/limb/equipment changes exactly once | Replay the original after a partial NVO write |
| Injury service, later | Persistent biological/mechanical consequences, treatment and continuing effects | Reapply the original direct hit |
| Presentation | Visuals, sound, messages, damage feedback | Decide whether another damage event is required |

Profiles and the pure resolver use explicit schema/version identifiers. Runtime adapters are separate from calculations so profile tuning does not require rewriting engine hooks. The schema in this packet describes future inputs; no installed DLL reads it.

## Required hit envelope

- Identity: session generation, unique engine invocation, attack identity when verified, component kind, application sequence, source and target handles/identities, originating weapon/ammo forms, optional carrier lifetime. Resolve plugin filename/local ID against this load. Do not retain raw engine pointers across calls or loads.
- Component kinds: direct projectile, melee contact, blast victim, verified fragment, exposure interval, or separately attributed continuing effect. A shared weapon, ammo or trigger pull is not a unique component ID.
- Snapshot revision: classification, profile, settings and anatomy/armour versions used for this decision. A runtime configuration change cannot silently alter half of an in-flight shot's definition.
- Body information: intended VATS selection, collision-reported region and ActorHitData region remain separate optional fields. A producer-specific verified effective region is required for location-dependent replacement. Unknown or contradictory data is not automatically torso/head.
- Context: verified real-time/VATS mode, actor class/anatomy, block/critical/effect state, engine values at their named stages and source attribution. `unknown` is different from false or zero.
- Armour: the actual equipped instance per covered region, condition, coverage mapping, material response profile and layer order. Re-read/validate at impact; do not freeze the target's armour at firing time.
- Physical/model inputs: family-specific fields below, each with units, provenance and supported/unknown status. Missing required information rejects replacement before gameplay writes.

## Projectile families and armour response

| Family | Transport/input | Armour response and gameplay meaning | Key correctness requirement |
|---|---|---|---|
| Ordinary bullets, AP, HP, slugs | Existing explicit cartridge/weapon pairing; mass kg, diameter m, supported impact velocity m/s, construction | Penetration response depends on construction, impact and material/condition. A stop may transmit bounded blunt trauma. HP expansion is distinct from AP penetration | AP/HP identity never inherits standard construction silently; no second vanilla ammo damage/DT multiplier |
| Buckshot / multiple kinetic carriers | Mass and velocity **per pellet**, actual live carrier identity | Each pellet resolves against the armour/body region it hits | Do not give every pellet the cartridge's total mass or collapse same-frame hits |
| Lasers, including Tri-beam | Verified beam or pulse semantics; authored energy dose/range response per component; no bullet gravity or G1/G7 drag | Material-specific thermal/ablation response. Reflection/resistance is profile data, not a universal bypass or immunity | Three actual beam components remain distinct; beam visuals are not new hits. No invented slug mass |
| Plasma, including Multiplas | Keep finite travel, collision and carrier multiplicity. Authored plasma payload/heat delivery and decay profile | Thermal/ablation injury and optional explicitly authored impact response. Armour can resist it differently from both bullets and lasers | Plasma is not automatically explosive, hitscan or ballistic. Do not manufacture bullet penetration from carrier speed |
| Flame / continuous emitters | Verified source-target exposure intervals; authored dose rate and game-time duration | Heat shielding, exposure and optional ignition; burns can occur without a puncture | Frame-rate-independent accumulation, no duplicate projectile+effect damage, pause/load boundaries defined |
| Rockets, missiles, grenades, mines | Family-specific launch/flight, fuse, impact and explosion identity; retain existing guidance/fuse behaviour until owned | Distinct direct impact, blast and verified fragmentation components. Blast transmission is separate from bullet penetration | No assumed projectile↔explosion join; one blast evaluation per target/application. No synthetic fragment damage if the engine already supplies it |
| Thrown physical weapons / darts / bolts | Explicit modded profile; mass, shape, contact speed if kinetic; payload if present | Piercing/cutting/blunt response and separately gated payload | Projectile-carried wound poison requires successful penetration; do not classify by appearance alone |
| Electrical / sonic / radiation / alien or modded effects | Explicit family adapter and authored effect data; unknown forms stay unchanged | Appropriate material/anatomy response, with robot/mechanical and biological effects distinguished | No silent fallback to a bullet formula. Radiation/exposure is not automatically direct HP damage |
| Melee / fists | Verified contact and authored proficiency/weapon/condition inputs; no projectile mass requirement | Cutting, piercing and blunt channels, including transmitted impact through armour | No fabricated firearm energy or second on-hit DamageAV call |

The current `FlightPreview::SnapshotOf` accepts only missile references/type1 and exact pilot profiles. That engine class includes more than the colloquial word “missile”; it is not a sufficient damage-family classifier. No expansion of that runtime filter occurs here.

## Units and provenance

- Internal kinetic calculations use kg, m, s, m/s and J. `E = 0.5 * mass_kg * speed_mps^2` measures incident kinetic energy; it is **not** the complete penetration formula and is **not** directly a number of HP.
- `1 grain = 0.00006479891 kg`; `1 inch = 0.0254 m`. Converted donor inputs and their original rows are retained in `PROFILES.reference.json`. They are game-tuning choices from the supplied BallistX5.4 data, not measured specifications of fictional weapons.
- The existing `70 units/metre` remains a donor convention, not a verified runtime calibration. Time is simulated game time, not wall-clock time. VATS/time scaling, engine speed multipliers and first-segment behaviour require an adapter contract that applies each conversion exactly once.
- A calibrated physical/contact contract is required before kinetic authority. A geometry-rejected sample, first contact before owned integration, multiple contacts, or an absent speed is `unsupported`, not zero, last-frame velocity or muzzle velocity.
- Contact-derived incidence requires a verified surface normal. A body-region-only model may deliberately omit angle effects under an explicit profile version; it must not invent a normal or claim precise plate intersection.
- Energy weapons initially use named **NVO dose units**, an authored game balance quantity. Do not label them joules without a justified conversion. Profiles keep pulse dose, delivered fraction and interval dose rate separate. No dose values or armour thresholds are invented in this packet.
- Each material response curve declares its input/output units, supported projectile constructions and anatomy/coverage assumptions. Ballistic coefficient belongs to flight drag; it is not an armour-penetration coefficient. Inventory ammo weight is not necessarily projectile mass.

## Resolution sequence

1. **Admit before changing anything.** Validate the engine path, identities, component deduplication, profiles, capacity, settings ownership and all required family inputs. Unknown equipment, unresolved region/effects or unowned modifier combinations preserve their full original path.
2. **Determine coverage.** Map only a verified engine body region through the target's body-part/anatomy profile. Head protection comes from the helmet's mapped coverage; body armour does not implicitly protect the head. A coarse “whole reported head region” profile must say so. No internal-organ coordinate claims. Unknown equipment in a relevant slot is not bare skin.
3. **Resolve each layer.** Use material, supported threat construction, coverage and condition. For kinetic threats calculate incident energy/momentum from supported inputs, then the authored material response yields residual energy, stop/penetration and bounded transmitted impact. Energy cannot increase through a passive layer. For laser/plasma/heat use the matching dose/ablation response, not the kinetic curve. For blast use its separate exposure/transmission model.
4. **Resolve target response.** Convert the residual threat and transmitted effects into direct HP, body-condition loss and equipment wear through explicit anatomy/profile tuning. Biological bleed/puncture trauma and wound-delivered poison require their relevant wound/penetration condition. Blunt transfer, external heat and blast do not. Robots receive mechanical consequences rather than bleeding. Max-health multipliers are not a substitute for this model.
5. **Own effects and modifiers.** Consult `MODIFIER-OWNERSHIP.json`: never layer a second DT/DR, location multiplier, difficulty multiplier or AP/HP damage rule over a value that already includes it. Critical damage/status that would bypass a failed penetration decision must be suppressed or reinterpreted by an explicitly supported rule; an unclassified damaging critical effect rejects replacement.
6. **Apply once and acknowledge.** The application adapter must intercept a proven boundary, preserve source attribution, and commit the planned direct HP/limb/wear changes once. This packet does not select an unverified write address or treat the public ITR scalar as a complete replacement API. The current pre-provider scope and post-scaling AV observer supply evidence, not permission to write.
7. **Schedule continuing consequences separately.** Continuing injury/exposure records keep source and cause identities, own their tick cadence and serialization, and cannot be mistaken for another direct hit. Healing queries/treatment APIs arrive in the physiology packet, not as assumed existing NVSE commands.

## Failure, capacity and timing rules

- State progression: `unclassified → admitted → resolved → application_started → acknowledged`. Before `application_started`, rejected input routes wholly to the existing engine. Once any gameplay write begins, never replay original damage as “fallback”; stop duplicate work, report the fault and preserve the single-owner record. Engine side effects are not assumed transactionally reversible.
- Gameplay admission and exact-once state are independent of diagnostic detail budgets, console output and file-log failures. Allocate/reserve required capacity before opting into replacement. Stack overflow or missing support cannot borrow an older hit's context.
- Reserve flight tracking **before** substituting a private projectile. Current pilot post-selection rejection does not restore stock flight; that finding remains open. Do not claim an unchanged flight fallback until it is implemented.
- Keep unique component/application sequence separate from carrier lifetime. Repeated hits may legitimately share a carrier; pellets/beams may share one trigger pull. No time-window deduplication. Unverified explosion/component identity stays on the engine path.
- Classify at firing where needed, validate again at impact, retire at acknowledged completion/destruction. On load rebuild transient projectile state and invalidate old session references. Do not serialize raw pointers. Long-lived injury state will use versioned NVSE serialization with resolved form handles.
- Same armour/anatomy rules for real-time and VATS. Resolve actual supported hit region rather than requested aim. The separate VATS player-protection modifier must be traced/owned before claiming equal protection. Unknown VATS mode is not real-time.

## Difficulty and progression

3L showed `008808A0` applying the receiver-based difficulty multiplier before `DamageActorValue`; the current index0 uses NPC2/player0.5. Neutralizing the ten health-damage settings is a proposed later configuration policy, not a blind divide-by-two. Effective values may change during a session and must be sampled or invalidated at an appropriate boundary before replacement; future tests record actual values.

The selected difficulty can later drive resource availability, restrained enemy accuracy/reaction, and recovery/treatment forgiveness. This is separate from penetration and anatomy. Global neutralization also changes unsupported attacks' engine damage and therefore requires an explicit installation/rollback and compatibility decision; it cannot be called unchanged fallback. Preserve original settings today. Health-level/Endurance GMSTs remain as the user configured them.

Proficiency, weapon condition, perks and ammo effects need per-effect dispositions. Conditions may affect reliable firing/accuracy/energy according to their profile, but no modifier is applied twice. AP/HP and energy max-charge/overcharge variants require exact identity and separate construction/dose/wear definitions. No automatic reuse of standard-ammo behaviour just because a projectile base is shared.

## Acceptance before enabling damage

The next work is a **disabled** pure resolver/admission implementation with deterministic offline fixtures. It may calculate would-be outcomes but cannot call engine mutation APIs. It must reject missing/NaN/negative inputs and mixed units; maintain passive-layer energy/dose bounds; show separate head/body coverage; distinguish AP/HP and non-kinetic families; and produce the same decision when logs are full or disabled. Per-family adapters need targeted runtime evidence afterward.

Only then use compact user checks for the affected paths: human/robot, outgoing/incoming/NPC-to-NPC, helmet/body/condition, pellets/multi-beam, plasma, timed flame, direct-impact versus blast, VATS and reload. Reuse previous identity/reload evidence where applicable; do not repeat the old long-distance miss/stress suite. Prior tests did not certify current full damage authority for those families.

Before any damage activation: retire the Baron callback and registrations in compiled records; settle units/contact/admission and region producers; verify the exact application boundary and modifier owners; run a targeted follow-up against Ultra317. Separate user approval enables a narrowly declared scope. Unsupported families continue functioning through the engine until their replacement is ready.
