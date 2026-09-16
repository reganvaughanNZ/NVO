# 3G1 / native316: boundary correction and bounded impact coverage

Purpose: obtain defensible diagnostic impact-speed estimates before introducing armour calculations. The prior3G capture had eight complete, correlated contacts but zero candidates because the earlier full-step endpoint was incorrectly required to equal contact. The actual earlier endpoint/accounting match the full proposed displacement; ShowOff later relocates projectile position to contact.

## Changes

- FlightImpactModel.inl contains a pure EvaluateImpact calculation. The existing geometry tolerance is unchanged. It separately validates earlier position against start+expected, accounting delta against expected, and a single contact within the swept chord. It then uses the unchanged RK4 integrator and24 bisection iterations on local velocity copies to infer partial model time. The integrated partial position must also match contact within the same tolerance. All estimates retain contact_time_measured=0 and speed_authority=0.
- FlightImpact.inl keeps guarded optional identity/field reads and callback correlation. IMPACT_BOUNDARY reports the two new comparisons. Baseline contacts have a clear engine_baseline_contact status (even if their geometry is also invalid) and their own summary count; they never gain an estimate. Missing reads, multiple contacts, bad geometry and model-path disagreement stay unavailable.
- A separate32-lifetime cache is enrolled through one added ImpactEnroll(t) call in the existing accepted-track path. This does not alter Track. Five collision rows plus callback/possible ending rows are bounded by224 extra detail rows per load, two summary rows, and the existing global log budget. Heavy per-frame logs remain first8/64steps. Slots persist until reset, preventing later duplicates from reusing a retired entry. Omitted accepted lifetimes beyond32 are counted explicitly. Callbacks without a collision sample remain unpaired, and duplicate callbacks are deduplicated even in that case. At reset all module-owned state clears.
- Plugin/header version316 / 0.3.16 / phase3G1. No native interface or new hook; the nine existing compiled hook bridges are compared with native315. Removing the single enrollment call reproduces native315 FlightPhysics.cpp exactly. Seventeen existing source/header/build files remain byte-identical. Only the diagnostic helper, version files and that enrollment call change; the model is a new private include.

The legacy PHYSICS_NO_UPDATE and lives_without_update label counts lifetimes with zero applied NVO steps. Baseline contacts can have movement/accounting entries but no applied step. The new explicit baseline count clarifies this without altering the accepted baseline policy or legacy counters.

## Evidence and limits

Input capture018ec6d9b0b6ee5c81e4a417e14057895bc4ce1fa18aa3c2096c4386183fee15, reviewed at source/combat/step3g/REVIEW-1.md. The offline harness extracts the actual Vec/Track types and RK4 implementation and includes the same EvaluateImpact code used in the DLL. It replaces engine reads with the captured snapshot; these are not live engine-read tests. It replays all eight samples through the actual model and runtime cache, verifies seven invalid-input guards, later lifetime coverage through32, omission beyond32, duplicate handling, callback-without-collision handling, missing callback and load reset.

Saved lifetimes3-8 produce six model candidates. Model/contact gaps range0.002886-0.063388 units, all within their unchanged tolerance. Two initial unchanged-engine contacts have no candidate. Partial time and speed are estimates from the model, not physical calibration or measured engine collision timestamps. Rounded log vectors are replay inputs; live float values can differ. Input hashes and exact outputs are in build-evidence/replay/REPLAY-RESULT.json. No DLL or game is loaded by replay.

The ShowOff callback occurs after the observed damage callbacks. Its correlation cannot itself become the damage-control boundary. Unit calibration, mass/energy, first-segment ownership and eventual pre-damage integration remain future work. Unsupported/ambiguous contacts cannot use the last recorded speed as a fallback.

## Install and reversal

Install only the compiled NVOCombatCore.dll/PDB pair using the prepared, hash-pinned transaction. Existing game files are backed up before replacement; dependency/record/configuration/activation hashes are preserved. The user has authorized closing New Vegas if needed. No assistant gameplay or GECK work.

To reverse, close New Vegas and restore both native315 files from the backup named in INSTALL-3G1.md, originals/Data/NVSE/Plugins, into the matching game folder. Keep NVO.esm, NVOFlightPilot.esp, RD.esm and the other current masters/configuration active. This packet contains no records to compile or merge and no save migration.

The next user check is the short three-shot sequence in START-HERE.html. Review the new native316 log before advancing. Do not request another long-miss reproduction or broaden flight/damage rules under this packet.
