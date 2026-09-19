# Packet 4E — Shared armour profiles

Historical preparation checkpoint: **prepared offline**. This packet introduced no runtime dependency, DLL, GECK record or installed-file change. At preparation, the game used native 327 / NVO 0.3.27 from the passed 4D checkpoint. See the repository's [current status](../../../STATUS.md) for later native versions, installations and live reviews.

## Purpose and implemented behaviour

The authoring file now separates reusable coverage definitions from exact equipment bindings. An NVO-owned tag selects a definition. Multiple reviewed records can use the same definition while keeping their own owning-plugin/local-ID and equip-mask check. Explicit record exceptions can select a different definition for one item.

The new resolver validates the whole document, selects definitions, records its decisions and exports the ordinary4D coverage TSV. The shipped two-record export is byte-identical to the installed, live-tested file. Therefore there is nothing new to install or repeat in the game for this packet.

These are NVO authoring tags. They are not queried from the live JIP keyword map, and this packet does not load KEYWORDS INIs or automatically discover modded armour. Profile bindings must still be reviewed. We have adapted the classification concept with original NVO code; no donor implementation was copied into the resolver. See DEPENDENCIES.md.

## Files and layouts

Paths differ between a repository checkout and the historical extracted release:

| Contents | Repository checkout | Extracted 4E package |
| --- | --- | --- |
| Editable definitions and exact bindings | `source/combat/step4e/profiles/armour-tags.json` | `profiles/armour-tags.json` |
| Expanded authoring JSON, runtime TSV and resolution report | `source/combat/step4e/generated/` | `generated/` |
| Original NVO resolver and validators | `tools/resolve_armour_profiles.py` and its sibling tools | `Tools/resolve_armour_profiles.py` and sibling tools |
| Synthetic fixtures and native export runner | `source/combat/step4e/checks/` | `checks/` |
| Parser/classifier implementation | Active files under `native/NVOCombatCore/` and `native/NVOCombatModel/` | Historical native 327 copies under `Source/` |

The two provisional Combat Armor/Helmet definitions retain exact owning-plugin/local-ID and equip-mask checks. `generated/RESOLUTION.json` records the chosen definition, revision, tags and any exact exception. `checks/SYNTHETIC-ONLY.*` contains non-game fixture IDs and must never be installed. Packaged `Source/` is a historical standalone-check snapshot, not the active DLL project in this checkout.

## Resolution rules

1. Validate every definition, key, region, mask, rule and record first. Definitions contain only revision, six explicit extents and rationale. No material strength, damage multiplier, implicit coverage fraction or inherited default exists.
2. For each binding, collect selecting tags. Rules with profile=null are metadata only. More than one distinct selected definition is an error, including when a record exception exists. Aliases pointing to the same definition are permitted.
3. Apply a reviewed exact-record exception if present. It may replace one unambiguous selection or provide a selection when no selecting tag exists. It never hides contradictory or undeclared tags.
4. Require a selected definition for every declared binding. A typo, absent selection or conflict rejects the complete export before its TSV is touched. Unlisted equipment remains unmapped in the installed classifier.
5. Sort by case-insensitive owning-plugin/local-ID and emit unique exact records. Inventory order and load-order indices never select profiles. In-game mask drift and unknown items retain the4D hold behaviour.

The source is capped at1MiB,256 definitions,256 bindings,512 declared rules and32 tags per binding. Tags use the NVO_ namespace and at most63 ASCII identifier characters, matched case-insensitively. Local IDs are eight hex digits with a zero high byte in JSON; runtime output uses six. Output keeps the existing128KiB/256-record limits.

## How we will add custom armour

After an actual ARMO record is imported and its origin/mask reviewed, add a binding to an appropriate reviewed definition. Give a damaged or unusual variant its own definition and an explicit exception. Head and body items remain separate. A cosmetic replacement, power-armour flag, faction or display name does not establish anatomical coverage. A static power-armour tag cannot tell whether a suit is currently powered.

From the **repository root**, with Python 3 available:

```powershell
python tools/resolve_armour_profiles.py source/combat/step4e/profiles/armour-tags.json source/combat/step4e/out-candidates/NVOArmourCoverage.tsv --expanded source/combat/step4e/out-candidates/armour-coverage.json --report source/combat/step4e/out-candidates/RESOLUTION.json
```

From the root of an **extracted 4E package**:

```powershell
python Tools/resolve_armour_profiles.py profiles/armour-tags.json prepared/NVOArmourCoverage.tsv --expanded prepared/armour-coverage.json --report prepared/RESOLUTION.json
```

This writes reviewed-output candidates to the workspace, not the game. Keep input/output paths distinct. Do not install a custom export until its new records and mappings have been reviewed. Invalid input leaves an existing output TSV intact. Supporting JSON outputs are individually atomic; they and the TSV are not a multi-file transaction. Use their source/runtime hashes to identify a matching set.

## Damage and stagger

4E changes authoring only. NVO still needs verified hit surfaces, target anatomy, material response, layering, contact energy and modifier ownership before new damage can run. The planned resolved hit will feed both damage/injury and stagger, with separate response rules and reaction cooldowns. Keyword labels grant neither protection nor knockdown immunity. Unknown or partial extents stay unresolved at the actual impact surface. Creatures and baked BIP protection still need explicit target profiles.

## Verification and reversal

The original preparation recorded 54 resolver/export checks and 19 checks through the unchanged production 327 parser/classifier, all passing. All five coverage rows from the pinned 4D log retained their mapped extents. These are historical results, not a fresh rerun during this documentation update. Shared definitions, record exceptions, conflicting tags, typo handling, duplicate keys, cap limits and failed-export preservation were covered offline. This does not establish live keyword loading or performance with additional records.

The native export check can be run from the repository root:

```bat
source\combat\step4e\checks\RUN-CHECK.cmd
```

That runner supports both layouts above, but contains a fixed Visual Studio path; inspect and adapt it to your MSVC x86 installation first. It writes under `checks/out/` and does not install a DLL.

The full Python replay runner is `tools/check_armour_profile_resolution.py`. It also needs `source/combat/step4d/Evidence/LIVE-4D-20260917-010933.log`, which is intentionally excluded from Git. The packaged equivalent needs `Evidence/REFERENCE-4D.log`. A clone alone cannot reproduce that historical replay, although the profile resolver/export command above does not require the capture. Do not fabricate a replacement capture or treat the recorded counts as a new result.

No installation, live test or reversal is needed. To undo an authoring edit, restore its previous JSON and re-export to a workspace folder. The current game files and previous4D backup remain untouched. See Evidence/VERIFICATION.json for source and installed-byte checks.

Next proposal, requiring approval: explicit armour material-response definitions and target-profile boundaries in disabled preview. Keep bullet, laser, plasma, flame and blast responses separate. Do not infer these properties from a broad keyword.
