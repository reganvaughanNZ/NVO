# Step 3 closure audit

## Audit boundary

This audit reviewed NVO Combat Core 0.3.25, its current flight profiles, the standalone `NVOCombatModel`, the pre-damage review, Ultra 317 findings and follow-ups, and the live evidence through Packet 3U1. `INDEX.json` records the exact files and hashes. The audit did not load New Vegas, change native source, build a binary, install files, or modify game records.

All 71 files pinned by the 3U1 source snapshot matched their current SHA-256 values. Both raw 3U1 log captures also matched their pinned hashes.

Evidence is separated into three levels:

- **Live:** produced by the installed DLL during a controlled game run.
- **Offline:** replay, parser, static or pure-model evidence without an engine write.
- **Design:** a contract or intended rule that has not yet been established at a gameplay authority boundary.

## Closure decision

Step 3 is accepted as a **narrow bullet-flight transport and diagnostic foundation** for the exact profiles selected by `NVOFlightPreview.ini`. This closure does not mean all New Vegas ammunition is covered, that every collision carries exact physical energy, or that NVO controls damage.

The accepted foundation provides:

- exact configured-profile admission instead of a broad weapon-family guess;
- reservation before private projectile substitution and stock fallback on refusal;
- a fixed 128-entry native flight pool with bounded impact and hit-query diagnostics;
- projectile motion integration and cleanup across reload boundaries;
- separate actor/reference and world/reference classification;
- preservation of actor identity in the 3U1 actor capture;
- a live world-contact classification and an explained terrain clamp in the 3U1 recheck;
- no new hooks in 3U1 and no damage hooks in the installed build.

The integrator preserves the observed first segment, then applies gravity and G1/G7 drag using the projectile's parent delta. Its scale of 70 game-coordinate units per NVO simulation metre is an authored convention supported by internal consistency checks, not a measured real-world calibration. Terrain correction is scoped, and retirement remains engine controlled rather than restoring the donor's unconditional three-second deletion.

The 3U1 recheck proves that the reader can classify a world contact and correlate the relevant callback. It uses a baseline engine segment, so it does not prove an NVO-owned terrain-contact interval or exact contact energy. The actor/reference row has an owned-step speed range, but its `speed_authority` remains zero. Those distinctions are deliberately retained in the closure.

## Accepted live evidence

The installed native pair reports version 325 and matches its PDB. Damage replacement is disabled and the DLL reports zero damage hooks. Fifty-three protected files were verified by the installation evidence.

The first 3U1 capture (`7337bf485a5cb219ec4cd4e2bfc37121a0936e3c5bd5091dba801b3ca3de65a2`) preserved the actor/reference join. Its owned-step speed interval is diagnostic rather than authoritative.

The recheck capture (`01a7dd5ef0cdaba00a97b950b1e02dd366c4d45ef3f9002a546bc2952a5454ea`) contains one close 9 mm landscape contact classified as World, with no body region, a correlated callback and an explained terrain clamp. That is enough to accept classification; it is not enough to authorize energy or damage.

Packet 3R demonstrated admission refusal, reservation rollback, stock fallback and continued operation by holding 127 inert reservations and presenting one real shot. It did not measure 128 simultaneous live projectiles, broad multi-NPC combat cost, exception paths, reentrancy, or every possible calling thread.

## Content coverage

The active configuration contains eleven sections: nine automatically selectable profiles and two pilot-only profiles. The selectable set is 9 mm pistol, hunting rifle, 9 mm SMG, service rifle, 10 mm pistol, .357 revolver, .44 revolver, hunting-rifle AP and hunting-rifle HP.

AP and HP identity can select a flight profile, but their construction, penetration, tissue effect and armour response do not exist in the active system. Unknown ammunition and equipment keep their existing engine or mod behavior.

Laser, plasma, flame, explosive, thrown, melee and pellet-specific behavior are not included in this Step 3 closure. They require explicit family adapters later. An explosive projectile's travel and its explosion must remain distinct events when that family is implemented.

## Damage-authority blockers

NVO cannot become the damage authority until these questions are resolved at the actual engine boundary:

1. **Single application point.** Identify the full-context, exact-once engine boundary that produces committed health and limb loss. The observed provider-call return is acknowledgement, not proof of committed actor-value change.
2. **Scaling ownership.** Define how difficulty, VATS, criticals, perks and other modifiers enter the calculation exactly once. Earlier observations are diagnostic and do not yet form an application contract.
3. **Impact state.** Obtain or deliberately bound contact time, contact point, speed and energy. Current range estimates and baseline-engine segments must not be silently promoted to exact inputs. Pre-movement contacts remain unavailable.
4. **Anatomy authority.** Preserve both collision region and `ActorHitData` region until a tested policy explains disagreement. The system must not invent internal-organ coordinates the engine does not report.
5. **Gameplay admission.** Move gameplay-critical hit and injury state to a ledger independent of bounded diagnostic caches. The existing `AdmissionLedger` is an offline model and is not linked into the native core.
6. **Equipment context.** Resolve the struck armour instance, helmet/body coverage, material, condition, ammunition construction and explicit compatibility profile before replacing damage.
7. **Unsupported families.** Each projectile and melee family needs its own admission, attribution, fallback and double-application tests.

## Existing Step 4 groundwork

Step 4 is not starting from zero. `native/NVOCombatModel` already contains a pure armour resolver, an offline admission ledger and impact-energy checks. They are intentionally unlinked from `NVOCombatCore` and have no game write path.

A future Step 4 packet may add a guarded **shadow adapter** that supplies fully validated inputs to the pure resolver and logs the prediction alongside engine behavior. That adapter must remain read-only, must reject missing or ambiguous context, and must have diagnostic capacity separate from any future gameplay ledger. This audit does not implement it.

## Stability assessment

Current runtime state is comparatively low risk because damage replacement is off, unsupported equipment follows the engine path, storage is bounded and 3U1 added no hooks. The fixed pool prevents unbounded projectile ownership.

The main known performance concern is diagnostic logging: file open/write/close work is synchronous and occurs under locks. It is acceptable for narrow diagnostics but should not remain on a hot production path. The 3R capacity test establishes fallback behavior rather than a universal performance ceiling. A later activation gate needs real concurrent-projectile and multi-actor measurements with production logging disabled or buffered.

Physics work can scale with frame delta: RK4 may take up to 60 substeps at the accepted 0.25-second ceiling, while contact diagnostics can add a 24-iteration point search and reintegration. Fixed arrays bound memory, but locks, scans and guarded reads still have CPU cost. A post-selection fault stops later substitution and editing for that projectile but can leave the already-private projectile under engine control; the fault latch also survives reload. Those cases need explicit activation policy and fault-path evidence.

## Related resolved and partial items

RD.esm is absent from the accepted record state, and current startup ownership no longer depends on it. Brahmin Baron registrations were retired from the current compiled records and verified on the tested new-game/reload path. Migration from saves made before that retirement remains unverified; it should be handled as an explicit save-compatibility policy rather than treated as an active new-game blocker.

The earlier distribution evidence caveat remains separate from this technical closure. Existing notices are retained, but the exact permission scope for copied BallistX numeric drag data should be archived or the disputed data replaced or separated before making a broad redistribution-license claim. This is not a legal conclusion and does not block private diagnostic work.

## Result

The Step 3 transport foundation is closed within the stated profile boundary. Damage activation remains on **HOLD**. The next safe engineering task, after separate approval, is the read-only Step 4 shadow adapter and profile contract described in `GATES.md`.
