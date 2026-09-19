# 4G numerical contract and limitations

## Definition and evidence binding

`MaterialPreview::Evaluate` takes a 4F catalogue, a numeric catalogue and independently supplied impact evidence. It re-runs definition selection. A previously successful symbolic plan is never accepted as proof of a resolved hit.

Required evidence: verified session/source/target/carrier/weapon/ammo/profile/component/application identity; engine path and mode; matching verified actual hit-data/collision region IDs; complete modifier ownership; verified target-profile binding; complete worn/natural/coverage snapshot with verified impact timing and outer-to-inner contact order; unique instance keys and verified surface bindings; explicit contact or miss state; condition for each contacted surface; exact mapped projectile construction, mass, diameter and calibrated authoritative contact speed. Missing/ambiguous/interval speed holds the preview. A valid interval is not collapsed to its midpoint or an endpoint.

These flags are evidence contracts for a later adapter. Fixtures setting them true do not demonstrate that the game currently supplies them. Double-reading inventory does not certify atomic impact timing. Region IDs remain integers bound to a target profile, never cast to the legacy `model::Region` enum. No organ coordinate or mesh-derived thickness is inferred.

The snapshot contains distinct instances. Its worn profile IDs are deduplicated only for definition lookup. All actual instances remain ordered for numerical work. Each mapped natural/structural profile must have exactly one region-specific state entry in this revision; absent or extra entries hold the preview. Multiple natural substructures need separately named profile bindings. Verified misses remain part of completeness checks but contribute no stopping or wear. If every surface is missed/absent, explicit bare evidence is required. Bare evidence combined with any contacted surface also holds.

Numeric entries are matched to exact 4F response IDs, Ballistic family, surface/tissue domain, provenance, condition law and biological/mechanical tissue kind. Missing selected numeric entries hold. Duplicate, misspelled, nonfinite, negative or mismatched supplied rules reject the whole request. All four construction thresholds must be explicitly defined; zero is valid, missing is not zero. All supplied rules are validated, including unused ones. No undocumented default coefficients exist.

## Condition law

An `AuthoredCurve` uses 2-8 points spanning condition 0 through 1, with strictly increasing condition coordinates and nondecreasing scale in [0,1]. Full-condition scale must be 1. Interpolation between points is linear. Intermediate points can therefore represent a nonlinear piecewise response. Scale at zero may explicitly be greater than zero; that is an authored residual-protection assumption, never an implicit benefit.

`ExplicitlyIndependent` requires an empty curve and uses a scale of 1. Actual condition still limits condition loss. It does not overwrite the snapshot's condition. `Unresolved` never supplies a numerical response.

The legacy preview also preserves actual condition: its capacity is resistance multiplied by condition, and the same condition limits wear. Forcing item condition to one would be an anti-pattern that neither path implements; only the new independent response's **protection scale** is one.

Profiles are labelled SyntheticFixture, ProvisionalGameplay or ReviewedGameplay in 4F; the numeric entry must retain the same label. A reviewed gameplay rule is not thereby a measured physics model. This packet provides only synthetic profiles in checks, with no armour record bindings.

## One component's provisional calculation

Let projectile mass be `m` kilograms and exact contact speed be `v` metres/second:

```text
incidentJ = 0.5 * m * v * v
remainingJ = incidentJ

for each verified contacted surface, outermost first:
    capacityJ = stoppingJ[construction] * conditionScale(condition)
    stoppedJ = min(remainingJ, capacityJ)
    transmittedJ = stoppedJ * transmittedFraction
    retainedJ = stoppedJ - transmittedJ
    conditionLoss = min(condition, stoppedJ * lossPerStoppedJ)
    remainingJ -= stoppedJ

healthPreview = remainingJ * tissueCoupling * directHpPerJ
              + sum(transmittedJ) * transmittedHpPerJ
regionalPreview = healthPreview * regionalLossPerHp
```

`stoppingJ[construction]` is an **authored scalar threshold** for Ball/AP/HP/Pellet, not a universal material penetration law. Diameter is verified metadata but does not yet modify that threshold. No incidence, thickness, contact area, penetration depth, ricochet, fragmentation or deformation model is claimed. The only physical energy input is the supplied mass/speed expression; protection and HP conversions remain explicit gameplay approximations.

Transmitted joules are a subset of stopped joules, not additional incident energy. Within floating-point rounding, incident = residual + transmitted + retained. Wear is an authored state-change proxy based on stopped energy, not another energy deduction. This revision uses the legacy coarse direct-to-target transfer fraction: it does not simulate attenuation of that transfer through subsequent layers. This limitation must be reviewed before production material calibration; coefficients must not be presented as transferable physical constants.

Each layer keeps incoming/stopped/outgoing/transmitted/retained values, so ordering and ownership can be audited. A surface after a stopping layer still returns a zero-loss row. Layer state is immutable during one component; later components must supply the appropriately updated snapshot. This packet does not advance condition between calls or schedule repeated applications.

Finite, nonnegative inputs and bounded fractions are required. The shared kernel accepts at most 64 contacted surfaces. Overflow or a late failure returns an empty result rather than earlier partial damage or wear. A zero-speed contact is valid zero energy. The standalone model's older kinetic calculation now calls this same kernel; its explicit linear condition behavior remains unchanged for supported bounded inputs.

## Output owners and future stagger

| Output | Intended future owner |
| --- | --- |
| Worn condition loss | Exact worn item instance; bounded by its snapshot condition. |
| Natural structure loss | Target + actual region + natural-surface key/profile; no inventory mutation. |
| Mechanical structure loss | Target + region + chassis/component key/profile; separate from terminal target health. |
| Biological HP/regional loss | Biological target's direct-health and regional channel. |
| Mechanical HP/regional loss | Mechanical target's direct-health and regional channel; biological fields remain zero. |
| Penetration/wound/payload preview flags | Eligibility evidence only, not an instruction to apply effects. |

Structure losses are normalized surface-state changes, not extra HP damage to add on top of target health loss. Their future persistence/application owner must avoid turning two views of the same chassis health into duplicate damage. No such writes or persistence occur here.

`protectionPenetrated` requires at least one contacted protective surface and positive residual energy. A bare hit may have positive biological wound eligibility while not claiming armour penetration. Mechanical targets never gain biological wound/payload eligibility. Biological blunt injury may produce health loss even when penetrating-wound eligibility is false. These remain coarse preview distinctions, not organ injury simulation or a completed medicine system.

**Consumer rule:** `!protectionPenetrated` does not establish that the target was protected, that the attack was blocked, or that no wound is eligible. First require `status == PreviewOnly`; a rejected result's default false flags convey no outcome. Then inspect the contacted-surface rows, residual energy and the separate biological wound/payload flags. A valid positive-energy bare hit and a projectile fully stopped by protection both have a false penetration flag, for different reasons. Zero-energy contacts also have a false flag.

The legacy `ArmourModel::Preview::armourPenetrated` flag has broader semantics: kinetic input with positive residual energy, including bare hits. It is not interchangeable with 4G's `protectionPenetrated`; consumers must not alias the names or use either flag as a general protection/wound gate. No gameplay consumer is introduced by this packet.

Future damage, wear and reactions consume this same admitted component identity and attribution. This packet exposes no stagger, force or impulse; energy alone cannot be substituted for an impulse, and HP loss is not a knockdown rule. A later reaction coordinator must incorporate target resistance, state and cooldowns, especially for pellets/bursts. Difficulty, perks, criticals, VATS, ammunition modifiers and secondary effects remain behind the shared modifier-ownership gate. No multiplier is added again here.

The pure function is intentionally repeatable. Repeating a preview does not admit or apply another hit. Exact-once admission/application remains a separate coordinator responsibility. Every pellet/fragment needs its own component identity and mass/profile; full-shell energy must not be assigned to each pellet. An explosion's blast and heat never enter this kinetic function as duplicate projectile energy.

## Still required for runtime use

Authoritative contact input, complete coherent impact snapshots and actual surface coverage; reviewed game-profile/condition bindings and coefficients; supported family-specific adapters; engine ownership and the one-application path; attributed persistent injury/structure state; reaction scheduling and acceptance checks. No new bridge is linked into the native DLL by 4G, and a passing fixture cannot enable it.
