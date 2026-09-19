# User reference assessment

Read-only input: `FNV_NVO_Projectile_Armor_Codex.docx`, SHA256 `c31e520ee5c00232d5a70d17c5a121b81a0163129f6dd52cabecc61272fe5853`. Original path and size are pinned in `Evidence/USER-DOCUMENT.json`. The extracted text remains local evidence. Its examples are proposals, not authoritative engine contracts or instructions to execute.

## Useful for NVO

The document reinforces the need to distinguish a trigger pull, projectile notification, hit observation, effect component and committed damage application. Streams, cones, pellets, beams, impact, blast and continuing effects belong in our coverage checklist. Its attention to thrown weapons, fatigue, EMP/electrical effects, poison and special weapon behaviour fits the existing plan to expand beyond bullets and generic energy categories.

Worn armour, natural protection and robot structure must be separate profile owners. Faction disguise belongs to relations/presentation and must not silently determine protection. Custom armour needs explicit identity, material and anatomical coverage mappings, with unsupported evidence left unresolved.

## Not adopted as implementation facts

The proposed per-tick/event counter does not establish distinct components or exact-once damage. We will not invent component IDs or use projectile/reference IDs to deduplicate actual damage. A repeated flame CREATE does not prove either a harmless duplicate or another damage application.

The document includes weapon catalog details, ammunition assignments, DLC provenance, form IDs, creature/type claims, hitscan classifications, DT rules and numeric effect values. These require verification against the actual loaded records and relevant engine/provider sources before implementation. Its general wiki attribution supplies no independently verified per-claim references. None of those values or snippets was imported into the runtime or profiles in 4J1.

Claims about globally stacking helmet and body DT, a minimum vanilla damage floor, or a fixed number of armour passes per explosion do not become NVO design requirements. Our approved design retains independent anatomical coverage, material responses and explicitly separate impact/blast/continuing-effect evidence. Exact internal-organ coordinates are not inferred from coarse engine regions.

## Effect on this packet

The document provides a useful coverage checklist and supports investigating repeated flame notifications. The actual fix is justified by retained 4J evidence and the local ShowOff/JIP source trace. It only quarantines positively qualified observer-only flame identity, retains genuine admission faults, and preserves cleanup. Laser, plasma, flame, explosion, throwing and other special-attack ownership still need their own evidence before the damage model can control them.

No new dependency, numerical damage model, armour rule, special-ammunition effect or gameplay authority is introduced by accepting this reference.
