# Packet 3N first saved-record review

Saved ESM SHA256: 8bed50dd121a557c33ac07d26263208d3eb7d3643b63932e8d485acc84e98238.
Archived intact under captures/saved-8bed50dd121a/NVO.esm. No live files rewritten.

ALTBackRichKidUDF, ALTQscript and NVOStartPreview match expected source, have changed compiled data, and retain original identities, script types and variable slots/types. ALTRichKid description matches and its other fields are unchanged. Masters remain RD-free; GMSTs unchanged; no added/removed records or remaining source registration sites were found.

ALTRichKidHit source and compiled data are unchanged from baseline, including DamageAV/Kill. This is the sole required GECK correction. FIX-ONE-SCRIPT.html copies the same complete no-op source already supplied. Keep original record and declarations. Do not restore the whole ESM or repeat the other three scripts.

## Additional save differences

All 36 additional changed records were checked with structure-aware comparisons. Details: ADDITIONAL-RECORD-DIFFS.json. No substantive field change was found:
- 2 ARMO: alternate-texture entries reordered; names, texture references and indices identical.
- 4 CELL: region entries reordered; same IDs/counts.
- 1 CONT, 4 NPC_, 1 CREA: inventory entries, spells or factions reordered. Inventory COED remains attached to the same CNTO item/count; no loose multiset comparison of ownership was used.
- 1 CREA: AIDT unused bytes only.
- 10 LVLI: LVLO unused bytes only; entry order, levels, counts and references preserved.
- 5 PERK: complete PRKE-to-PRKF effects reordered; each effect's condition order, parameters, priority and embedded script/reference order preserved.
- 2 QUST: QSTA unused bytes only.
- 6 REFR: XESP unused bytes only; parent reference and flags preserved.

Definitions checked against [xEdit FNV definitions](https://raw.githubusercontent.com/TES5Edit/TES5Edit/dev-4.1.6/Core/wbDefinitionsFNV.pas): AIDT 4043-4050, XESP 2864-2871, QSTA 7027-7033, XCLR 3920-3924, alternate textures 2753-2756, CNTO grouping 3972-3987, perk effects 5562 onward. LVLO padding verified against supplied xNVSE GameForms.h TESLeveledList::LoadBaseData at line 3145 (level0, fill2, form4, count8, fill10).

review_3n_save_layout.py records these narrow layout comparisons without rewriting anything. The verifier reports them separately as layout_only_changes; unknown changes still require review. This is static record validation, not proof of runtime retirement. Damage replacement stays OFF; native320 and configs untouched. No native build or gameplay test repeated for this save.
