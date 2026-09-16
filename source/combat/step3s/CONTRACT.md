# Impact-energy contract, revision 1

## Scope and authority

`nvo::energy::Evaluate` is a pure offline evaluator. `Result::damageAuthority` is a compile-time false constant. There is deliberately no conversion to `nvo::model::Threat`, no setter that lifts calibration, and no live-DLL linkage. Valid arithmetic cannot certify the source of its inputs. A later reviewed adapter must supply independently verified data before armour can interpret it.

## Profiles and identity

Only two exact canonical weapon/ammunition/original-projectile combinations are available. Canonical keys include the originating plugin and local ID. The current log adapter recognizes these exact FalloutNV.esm records, then joins each session's unique FLIGHT_PROFILE row to the observed weapon, ammo and selected private base. It never strips an arbitrary load-order byte. `profileMappingVerified` is the trusted adapter's assertion, not a public configuration override or proof made by the arithmetic function.

AP, HP, other weapon models, shotgun pellets, unknown equipment and non-bullet families do not inherit a profile from a shared calibre or similar name. In particular, the five SMG contacts in the replay are intentionally outside this first energy-profile scope even though SMG flight already works. This does not disable their existing flight.

The calculation carries capture ID, session, lifetime, movement step, actual projectile, source, target, weapon, ammo and actual base. Contact and velocity identities must agree and be populated. The offline adapter joins companion rows by capture/session/lifetime/step and requires uniqueness. Speed rows do not independently repeat every identity field; they inherit the uniquely paired contact row's scalars. This is diagnostic association, not a new engine identity proof, hit-component token or deduplication ledger. Replaying twice repeats previews; it does not apply twice.

## Units and time

- Donor cartridge column 4 is mass in grains, confirmed against the hash-verified Help.txt; it is the projectile's mass, not cartridge/case weight. Standard 9mm = 115 grains = 0.00745187465 kg. Standard .308 = 147 grains = 0.00952543977 kg.
- Donor diameter is inches; 0.0254 converts inches to metres. Diameter is preserved metadata, not used to calculate armour defeat here.
- Current flight uses an authored donor convention of 70 engine units per metre. It is not independently calibrated as a physical world scale. Different/unknown scale rejects this revision instead of silently reinterpreting speed.
- The speed label is metres per **simulation** second under that convention. Time is the parent BulletProjectile update delta used by the current integrator, not wall time, GameHour or the separately observed adjusted movement delta. Positive dt is at most 0.25; estimated contact time must be within that same step. No second VATS/time multiplier is applied here. Whether the selected delta gives the intended physical interpretation in VATS remains open.
- `0.5 * massKg * speed * speed` yields **conditional** joules if those spatial/time assumptions hold. Model speed is not a measured instantaneous impact speed. Numbers are not fed into armour or labelled calibrated by this packet. There is no credible uncertainty interval yet.

## Contact producer and geometry

Only a logged model estimate for an NVO-applied segment with verified baseline, complete single-contact snapshot and exact scalar join can yield a conditional estimate. Missing/nonfinite input, multiple contacts, unowned movement, mismatched endpoints/accounting or out-of-segment fractions reject it. Model path gap and off-chord distance must fit the existing tolerance; no thresholds were widened.

Existing tolerance is `0.002 + max(abs(start coordinates))*0.0000005 + length(expected displacement)*0.00002`, in engine units. It is a diagnostic coordinate-error budget, not a measured confidence bound. Engine full-step position/accounting are checked against the full endpoint; collision position is a separate field. The binary search estimates time along the integrated path. Its 24 iterations are numerical precision, not 24 independent physical observations.

Contacts before any movement and during the unchanged first segment remain unknown. Never substitute muzzle speed, last-frame speed, average distance/time, or proposed full-step speed for missing contact speed. There is no zero-damage fallback. Current live damage remains the engine/installed-mod result because this module is offline.

Contact region, ActorHitData region and intended VATS aim are separate observations. The energy module does not remap any of them, infer organs, correct VATS misses, or establish armour coverage. The four successful conditional estimates in this packet are prior scenery contacts. Actor contacts remain unavailable in these captures.

## Completion boundary

This packet completes the donor-mass/input-validation subtask, not frozen finding ULTRA-317-05. Remaining: establish or explicitly adopt and validate the world/time convention; justify contact producer/tolerance across supported runtime paths; handle first-segment contacts with evidence; independently pair the result at the eventual authoritative damage boundary. Debug capture limits of 32 lifetimes/64 hit rows must never become gameplay eligibility limits. Unknown attacks continue their existing behaviour until a supported producer exists.

Other independent gates remain: full pre-damage carrier/ammo context, terminal acknowledgement and exact-once component handling, scaling/difficulty ownership, region/armour coverage, exceptional post-selection fallback, and family-specific support. This contract grants none of those.
