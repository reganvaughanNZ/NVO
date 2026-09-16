# Packet4E — Shared armour profiles

Prepared offline. No new runtime dependency, DLL, GECK record, or installed file change. The game continues using native327 / NVO0.3.27 from the passed4D checkpoint.

## Purpose and implemented behaviour

The authoring file now separates reusable coverage definitions from exact equipment bindings. An NVO-owned tag selects a definition. Multiple reviewed records can use the same definition while keeping their own owning-plugin/local-ID and equip-mask check. Explicit record exceptions can select a different definition for one item.

The new resolver validates the whole document, selects definitions, records its decisions and exports the ordinary4D coverage TSV. The shipped two-record export is byte-identical to the installed, live-tested file. Therefore there is nothing new to install or repeat in the game for this packet.

These are NVO authoring tags. They are not queried from the live JIP keyword map, and this packet does not load KEYWORDS INIs or automatically discover modded armour. Profile bindings must still be reviewed. We have adapted the classification concept with original NVO code; no donor implementation was copied into the resolver. See DEPENDENCIES.md.

## Files

- profiles/armour-tags.json: editable source, containing the two provisional Combat Armor/Helmet definitions and exact bindings.
- generated/armour-coverage.json: expanded exact-record authoring compatible with the4D compiler.
- generated/NVOArmourCoverage.tsv: output accepted by the current DLL; identical to the installed file.
- generated/RESOLUTION.json: each record's selected definition, revision, tags and whether an exact exception applied.
- Tools/resolve_armour_profiles.py: original NVO resolver and CLI; uses Python's standard library and the included NVO validators.
- checks/SYNTHETIC-ONLY.*: non-game fixture IDs for verifying custom records and exceptions. Never install these.
- Source/: unchanged parser/classifier source copied from native327 solely to make the standalone export check reproducible. This is not a replacement DLL project.

## Resolution rules

1. Validate every definition, key, region, mask, rule and record first. Definitions contain only revision, six explicit extents and rationale. No material strength, damage multiplier, implicit coverage fraction or inherited default exists.
2. For each binding, collect selecting tags. Rules with profile=null are metadata only. More than one distinct selected definition is an error, including when a record exception exists. Aliases pointing to the same definition are permitted.
3. Apply a reviewed exact-record exception if present. It may replace one unambiguous selection or provide a selection when no selecting tag exists. It never hides contradictory or undeclared tags.
4. Require a selected definition for every declared binding. A typo, absent selection or conflict rejects the complete export before its TSV is touched. Unlisted equipment remains unmapped in the installed classifier.
5. Sort by case-insensitive owning-plugin/local-ID and emit unique exact records. Inventory order and load-order indices never select profiles. In-game mask drift and unknown items retain the4D hold behaviour.

The source is capped at1MiB,256 definitions,256 bindings,512 declared rules and32 tags per binding. Tags use the NVO_ namespace and at most63 ASCII identifier characters, matched case-insensitively. Local IDs are eight hex digits with a zero high byte in JSON; runtime output uses six. Output keeps the existing128KiB/256-record limits.

## How we will add custom armour

After an actual ARMO record is imported and its origin/mask reviewed, add a binding to an appropriate reviewed definition. Give a damaged or unusual variant its own definition and an explicit exception. Head and body items remain separate. A cosmetic replacement, power-armour flag, faction or display name does not establish anatomical coverage. A static power-armour tag cannot tell whether a suit is currently powered.

From this packet's root, with Python available:

```powershell
python Tools/resolve_armour_profiles.py profiles/armour-tags.json prepared/NVOArmourCoverage.tsv --expanded prepared/armour-coverage.json --report prepared/RESOLUTION.json
```

This writes reviewed-output candidates to the workspace, not the game. Keep input/output paths distinct. Do not install a custom export until its new records and mappings have been reviewed. Invalid input leaves an existing output TSV intact. Supporting JSON outputs are individually atomic; they and the TSV are not a multi-file transaction. Use their source/runtime hashes to identify a matching set.

## Damage and stagger

4E changes authoring only. NVO still needs verified hit surfaces, target anatomy, material response, layering, contact energy and modifier ownership before new damage can run. The planned resolved hit will feed both damage/injury and stagger, with separate response rules and reaction cooldowns. Keyword labels grant neither protection nor knockdown immunity. Unknown or partial extents stay unresolved at the actual impact surface. Creatures and baked BIP protection still need explicit target profiles.

## Verification and reversal

54 resolver/export checks and19 checks through the unchanged production327 parser/classifier pass. All5 coverage rows from the pinned4D log retain their mapped extents. Shared definitions, record exceptions, conflicting tags, typo handling, duplicate keys, cap limits and failed-export preservation are covered offline. This does not establish live keyword loading or performance with additional records.

No installation, live test or reversal is needed. To undo an authoring edit, restore its previous JSON and re-export to a workspace folder. The current game files and previous4D backup remain untouched. See Evidence/VERIFICATION.json for source and installed-byte checks.

Next proposal, requiring approval: explicit armour material-response definitions and target-profile boundaries in disabled preview. Keep bullet, laser, plasma, flame and blast responses separate. Do not infer these properties from a broad keyword.
