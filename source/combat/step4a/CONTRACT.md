# Step 4A armour shadow-adapter contract

## Purpose

Packet 4A defines the evidence boundary between future engine observations and `nvo::model::Resolve`. It lets NVO calculate a non-authoritative armour preview only after the required facts are coherent. It does not acquire those facts from the engine and cannot apply its output.

`nvo::shadow::kGameplayWrites`, `nvo::shadow::Result::gameplayWrites`, and `nvo::model::kGameplayWrites` are compile-time false. `kRuntimeIntegrated` is also false. The module has no NVSE or engine headers, hook, event handler, logger, serialization, callback, installation target, or mutation API.

## Required evidence

A preview requires all of the following:

1. Nonzero session, component, application, profile, source, target, carrier, weapon and ammunition identities from a trusted adapter.
2. Verified identity and engine path ownership.
3. Verified real-time or VATS mode.
4. Independently verified collision and hit-data regions that both report the same supported body region.
5. Explicit ownership of difficulty, critical, perk, VATS and related modifiers.
6. Complete equipped-item enumeration, complete coverage knowledge, verified layer order and a coherent at-impact snapshot for the resolved region.
7. Either at least one fully profiled layer or an explicit verified-bare result for that region.
8. Exact carrier/weapon/ammunition/construction mapping tied to the same profile identity, with positive mass and diameter in explicit SI units.
9. Exact contact speed in metres per second from a verified contact/velocity producer and a separately calibrated unit convention.
10. A verified target anatomy/conversion profile.

The adapter constructs the pure model's `Context` and `Threat` itself after these checks. Callers cannot supply a pre-certified model context or set its authority flags directly.

## Regions

Collision region and `ActorHitData` region remain separate input fields. Revision 4A accepts only verified agreement. If either source is missing, the result is `region_unavailable`. If they differ, the result is `region_conflict`. It does not prefer VATS aim, hit data, collision, torso, or any invented internal organ.

This conservative rule is an initial shadow policy, not a claim that agreement makes either engine producer universally authoritative. A later runtime packet must preserve both raw observations in diagnostics.

## Armour snapshots

`enumerationComplete` means the future reader completed the supported actor's equipped-item traversal without a guarded-read failure. `regionCoverageComplete` means every equipped item that might cover the resolved region was classified. The typed layer order must be `OutermostToInnermost`, which is the order consumed by the resolver. `impactSnapshotVerified` proves the list belongs to the same coherent hit snapshot. None may be inferred from an empty result.

An empty layer list is accepted only when `bareRegionVerified` is true. A nonempty list combined with `bareRegionVerified` is contradictory and invalid. Every layer retains an instance identity, coverage, condition and exact material response. Unknown worn armour rejects the preview rather than becoming bare skin or transparent clothing.

Packet 4A contains no production armour/material table, layer-order policy, equipment reader, slot map, helmet record mapping, or condition conversion. Test layers are synthetic.

## Threat measurements

Speed evidence has four shapes: missing, exact, interval and ambiguous. Only an exact, verified, calibrated scalar can reach the current scalar armour resolver. A valid interval returns `speed_interval` without selecting its lower bound, upper bound, midpoint or mean. A malformed interval is invalid.

Therefore the 3U1 owned-step range of 354.396070–359.517095 simulation metres per second remains diagnostic. The authored 70-units-per-metre convention is not silently promoted to independent physical calibration. First-segment, pre-movement and otherwise unavailable contacts remain unavailable.

Only kinetic inputs are adapted in revision 4A. Laser, plasma, flame, blast, thrown, melee and pellet-family semantics require their own contracts. AP/HP construction can be represented only after an exact profile supplies production data; this packet supplies none.

## Result classes

- `PreviewOnly`: every gate passed and the pure resolver returned a preview.
- `WaitingForEvidence`: a supported concept lacks proof, conflicts, or has an unknown layer/profile needed for interpretation.
- `Unsupported`: the family or production profile is outside the adapter's declared scope.
- `InvalidInput`: evidence is internally contradictory, malformed, nonfinite, duplicated, or rejected by pure-model arithmetic.

A rejected result contains no partial HP, limb or wear prediction. Repeated evaluation has no side effects and does not create a hit, reservation, admission, wound or transaction.

## Boundary for Step 4B

A future engine reader must first prove a read-only, coherent equipped-armour snapshot at the observed hit boundary. It must preserve actual instance identity, record every read failure, distinguish an empty inventory result from a verified bare region, and leave gameplay behavior untouched. Step 4B must not enable health, limb, armour condition, inventory or effect writes.
