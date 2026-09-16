# Step 4C classification boundary

1. Input memory must be valid caller-owned C++ objects. This pure API is not a guarded engine-memory reader.
2. Caller supplies an explicitly known EquipmentCharacter domain, complete enumeration and stable double read. Creature is unsupported even with no items. Unknown target stays unknown.
3. Catalog keys are owning-plugin basename plus nonzero24-bit local form ID. ASCII plugin names ending .esm/.esp are supported initially; other names remain unsupported. No path, wildcard, display-name or equip-slot matching is allowed. Exact origin resolution remains a future runtime obligation.
4. Every catalog profile has a positive revision, legal expected20-bit equip mask and all six explicitly authored semantic extents. Unknown values are represented by Unknown rather than omitted. Duplicate keys fail closed.
5. Input count is checked before indexing and is at most32. Every instance is nonzero and unique within the call, with finite condition in[0,1] and a legal observed slot mask. Two different instances may share a form.
6. Unknown origins/items, drift or malformed data return an empty result, even if prior items classified successfully. No partial snapshot is published.
7. Classification maps each item independently across Head/Torso/LeftArm/RightArm/LeftLeg/RightLeg. Those are semantic regions; raw engine region integers and equip bits must not be cast into them.
8. None means this authored item has no declared coverage for that region, not that the target has bare skin there. Partial means unresolved partial coverage, not a hidden fraction or random roll. Full is an authoring concept, not proof of the actual struck surface. Unknown remains unresolved.
9. Region summaries count overlapping authored extents. They are not ordered layers. Item order and instance addresses may change after loading; no cross-call cache or persistent identity is derived from them.
10. Output plugin-name views borrow catalog storage. Keep those strings alive while inspecting the result. No game pointer is returned or retained; no live objects are addressed by the API.
11. No material, penetration, energy, conversion coefficient, modifier, treatment, damage or wear is computed. No native observer, NVSE script, ShadowAdapter or ArmourModel call is introduced.
12. All gameplay, coverage-authority, at-impact, verified-layer-order, verified-bare and armour-preview capabilities are compile-time false, including on a successful classification.

The two seed profiles are provisional NVO gameplay authoring. Their FormIDs/equip masks are supported by the inspected records and capture data; the proposed anatomical extents are design choices rather than source-proven geometry. Future asset overrides require explicit compatibility decisions.
