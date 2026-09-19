# Impact evidence binding contract, version 1

This is an offline contract used by MaterialPreview version 2. No current native producer satisfies its complete success path. `VerifiedExactContact` and `VerifiedAtImpact` are reserved producer contracts exercised by synthetic fixtures only. Their names are requirements, not evidence that those producers have been implemented.

## Independent inputs

The consumer constructs `expected` from its current capture scope. Contact and snapshot producers preserve their stamps when capturing the corresponding payloads. Never relabel a cached payload with the current stamp at consumption time. Equality cannot detect three identically stale stamps if the consumer itself uses stale context. These values are trusted provenance assertions, not cryptographic proof.

| Field | Meaning and limit |
| --- | --- |
| generation, session | Current producer lifecycle and loaded-world scope; must change/invalidate as applicable on reset/reload. |
| transaction, copyOrdinal | Supported provider-call identity and exact observed copy within it; neither means committed damage. |
| lifetime | Tracked projectile lifetime; a reused address or form ID is insufficient. |
| component, application | Explicit supported attack component and resolution application; neither is inferred from transaction/log order. |
| profile | Exact selected kinetic profile identity; existing profile binding must also pass. |
| source, target, carrier, weapon, ammo | Nonzero actor/projectile/equipment identities for this supported ballistic path. |
| region, mode | Literal agreed engine region in 0..255 and verified real-time/VATS mode. No legacy-region enum cast. |

All identifiers must be present and all three stamps equal field by field. The expected stamp must also match existing identity, region and mode inputs. Region zero is valid; zero identifiers and unknown mode are not. This contract is for the existing ballistic material bridge; it does not assume every future melee, flame or explosion application has a projectile or ammunition.

## Capture and producer qualification

An independently verified exact copy scope and hit-to-contact position association are required. Collision-data reread agreement alone does not establish the latter. Current owned-step intervals, segment mean speeds, point-model estimates and muzzle speeds are explicitly unqualified, even if an interval is narrow or zero-width. Current stable equipment snapshots are explicitly unqualified for impact-time authority.

Only the reserved exact-contact/at-impact kinds pass this additional gate. Existing gates still require verified identities/path/mode, agreed raw regions, modifier ownership, kinetic profile/units/contact/speed, complete surface sets, target and item bindings, actual contact, condition and layer order. `ImpactBinding::Validate` by itself does not produce a ready material result or run those other checks.

Snapshot tokens are valid only within the bound capture. `Result.impactScope` accompanies successful surface outputs; no token becomes a persistent inventory/serialization identity. Failed checks leave output identity, scope, energy, damage and surface changes empty/default. They retain only the diagnostic rejection reason.

## Limits and implementation boundaries

The comparison is fixed-size scalar work with no allocations, engine calls or stored cache. The containing material evaluator still uses its existing containers; this is not a live performance benchmark. There is no apply function or DLL linkage.

Do not generate component/application IDs by renaming diagnostic context, incrementing counters without proven semantics, or treating copied HitData as committed actor loss. Exact-once admission and engine modifier ownership remain separate work. Diagnostic sample budgets must not control gameplay eligibility, silently reuse previous inputs, or turn omissions into bare anatomy/zero speed.

Native integration must first establish reliable component and copy semantics, immutable payload ownership, lifecycle invalidation and contact/at-impact qualification. If exact scalar contact input cannot be established, keep the scalar path unavailable or design a separately reviewed interval model. Do not choose an endpoint or midpoint to satisfy an exact-speed API.
