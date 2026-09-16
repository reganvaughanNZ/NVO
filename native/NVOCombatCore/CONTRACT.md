# Step 4B guarded armour snapshot contract

## Entry contract

The reader may run only from the existing JIP `CopyHitData` wrapper after `HitTransaction::CopyInput` returns an exact, identity-matched, process-matched, untainted, main-thread scope for the current capture session. The hit-data pointer, target process, source, target, carrier, weapon, region, and flags are read again before and after traversal. Any mismatch rejects the observation.

The armour observer must never call an engine helper, allocate through the engine, retain an engine pointer, change a hook, or write game memory. It may copy bytes through `ReadBytes`, update DLL-owned counters, and append bounded diagnostic text.

## Supported targets

- `0x3B Character`: eligible for inventory-armour observation.
- `0x3C Creature`: unsupported and skipped before the 64-snapshot Character budget.
- Every other form type: unsupported and skipped.

Unsupported does not mean unarmoured. Creature hide, shell, scales, chassis, supernatural resistance, and model-baked protection require separate profiles. A Character can also have baked model geometry that this inventory reader does not see.

## Accepted evidence

A complete snapshot requires all of the following:

1. The target FormID equals the exact transaction target and remains type `Character`.
2. The reference extra-data list is readable and internally stable.
3. Presence bits and linked-list nodes agree for exactly one `ExtraContainerChanges`.
4. The container owner is the target and its object list is available.
5. Every visited list/node/form pointer is aligned, readable, unique in its graph, and inside all traversal and probe bounds.
6. Every equipped armour instance has exactly one `ExtraWorn`, no `ExtraWornLeft`, at most one `ExtraHealth`, and a valid `ARMO` record.
7. Base health is nonzero; current health is finite and within `[0, base]`; damage threshold is finite and nonnegative; the equip mask uses only the 20 known slot bits.
8. A second full traversal produces the same identities, order, counts, fields, and values.
9. The enclosing hit boundary is unchanged and the observer was not re-entered.

A failure rejects every armour row. Partial rows are never exposed.

## Raw fields and limits

The reader copies exact-instance token, FormID, 20-bit equip-slot mask, base/current health, explicit-health status, arithmetic condition ratio, raw armour rating, raw damage threshold, 32-bit biped flags, and armour flags.

Limits per traversal are:

- 64 actor extra nodes;
- 512 inventory entry nodes;
- 1,024 item-instance nodes;
- 64 extras in one item instance;
- 8,192 item-instance extras total;
- 32 equipped armour output rows;
- 64 hash probes per pointer insertion.

The runtime attempts no more than 64 supported snapshots per load session. Unsupported targets do not consume this budget.

## Authority deliberately withheld

The following remain false even after a complete stable snapshot:

- `regionCoverageComplete`;
- `layerOrderVerified`;
- `impactSnapshotVerified`;
- `bareRegionVerified`;
- `snapshotAuthority`;
- `armourPreview`;
- `gameplayWrites`.

The biped mask describes equip-slot occupancy, not anatomical coverage. Inventory traversal order is not protection-layer order. Double reading is consistency evidence, not an atomic snapshot at committed damage time. Zero observed armour is telemetry, not proof of bare skin.

Step 4B does not call the Step 4A ShadowAdapter or ArmourModel. It cannot change health, limb health, armour condition, equipment, inventory, damage, or any effect.

## Runtime checkpoint boundary

Installation is outside this prepared packet. When separately approved, the first live checkpoint should confirm Character armour rows, helmet/body distinction, damaged condition, Creature skip accounting, reload lifecycle, and a short automatic-fire/heavy-inventory stress case. Runtime acceptance cannot promote any withheld authority gate.
