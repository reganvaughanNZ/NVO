# Packet 4D — Armour identity and coverage diagnostics

Installed with approval. NVO 0.3.27 / native327 is hash-verified; the live exact-origin and authored-coverage checkpoint passed; see LIVE-REVIEW.md. The assistant has not launched the game or run a gameplay test.

Purpose: join the existing guarded worn-armour snapshots to exact, editable coverage profiles. This is the foundation for custom armour records, including separate power-armour suits and helmets. It logs authored regional coverage and condition; it does not decide whether a particular impact struck a plate or exposed skin.

## Files and scope

The completed installation changed exactly three paths in Data/NVSE/Plugins: NVOCombatCore.dll, its matching NVOCombatCore.pdb, and NVOArmourCoverage.tsv. The first two replace native326; the text file is new. No GECK records, scripts, ESM, ESP, flight settings or load order change. NVO.esm and NVOFlightPilot.esp remain active as before.

The DLL adds a read-only loaded-mod table snapshot and a bounded text-profile loader. The table is read twice and checked for stable pointers, names, indices and counts. It identifies a record's owning plugin and local ID. It does not identify or approve the winning override. Dynamic FF forms are unresolved. Unsupported names, layouts, corrupt reads or malformed configuration disable these new classifications and leave the existing game path intact.

Configuration is read and validated once per activated session, not per hit. A full game restart is recommended after edits. The input file is capped at 128 KiB and 256 profiles. Names must be printable ASCII, at most 128 characters, and end in .esm or .esp. Duplicate keys reject the entire catalogue. No live configuration reload command or merging of multiple profile files exists yet.

The runtime uses an immutable prepared catalogue with bounded linear matching, not per-hit parsing or allocation. It reuses complete snapshots from the existing 64-attempt humanoid diagnostic budget. Its own 64-result cap is an additional bound. Incomplete raw samples retain the existing rejection logs. Creature targets retain the existing unsupported-target route. No new engine hook is installed.

## Meaning of the log

- ARMOUR_COVERAGE_READY: whether origin resolution and profile loading succeeded for this session.
- ARMOUR_ORIGIN: copied owning-plugin/local-ID identity of each worn armour item. winning_override_verified=0 remains explicit.
- ARMOUR_COVERAGE: classified_only, unknown_equipment, origin_unresolved, record_mismatch or another explicit hold reason. A single unknown worn item prevents a partial successful result.
- ARMOUR_COVERAGE_ITEM: authored six-region extents, revision and observed condition for each item. Equip-slot masks only check record drift; they never generate coverage.
- ARMOUR_COVERAGE_SUMMARY: bounded counts, including holds and log failures. This is written to the game-root NVOCombatCore.log, not a repeating console message.

Only the two provisional Step4C Combat Armor/Combat Helmet profiles ship. Body: partial torso/limbs, no head. Helmet: partial head only. These are NVO authoring proposals, not measurements. Partial remains unresolved at the actual hit surface. No worn armour is an empty equipment classification, not proof of bare anatomy or absent natural protection.

## Damage and stagger boundary

Armour coverage authority, material response, layer-order authority, verified bare regions, armour-model preview, damage replacement and stagger writes remain disabled. The separate Step4A ShadowAdapter and ArmourModel are not linked into the DLL. This packet cannot establish actual protection, damage balance or performance of a future always-on system.

See CUSTOM-ARMOUR.md for authoring and the proposed shared damage/stagger result. See TITANS-ASSESSMENT.md for the requested donor assessment. The latter introduces no dependency or donor code.

## User checkpoint

Use the four-hit, one-reload instructions in START-HERE.html. Existing 4B test-kit BAT files are reused. No new GECK compilation is required. Confirm ready=1, two known identities, helmet removal, empty inventory without a bare claim, then fresh classifications after reload. Future custom records need their own in-game identity and profile checkpoint before any authority is enabled.

## Reversal

Before installation, preserve native326's DLL and PDB and any existing NVOArmourCoverage.tsv in a dated workspace backup. To undo, close New Vegas, restore that pair, and restore the previous TSV or remove only the TSV introduced by this packet. Backup: backups\combat-install-4D-20260917-005034-7393db93. Receipt: Evidence/INSTALL-result.json. The existing TSV was absent before installation. Load a normal save to discard test-target inventory/health changes made by the manually run BAT helpers.

## Validation

See Evidence/VALIDATION.json and SOURCE-DIFF.json. Offline coverage/origin/parser and production-integration fixtures passed under x86 /W4 /WX. Existing classifier checks and recorded 4B replay checks passed. DLL/PDB identity and exports were statically inspected; existing hook/flight/reader sources were compared to the frozen 4B release. Those preparation checks were read only. The subsequent three-file installation verified 51 other files unchanged, retained RD absence and backed up native326. Vortex was left running; no process was closed. No game launch, GECK use or live custom-armour test occurred.
