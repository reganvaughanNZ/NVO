# User compilation and runtime review

The user reports that NVOCombatBootstrapScript compiled successfully and that the game displayed nonfatal errors during their test. Two still images were supplied; no video file was available for this review. The name-entry still alone does not establish a malfunction or show the complete Alternative Start flow.

The inspected game-root nvse.log, modified 2026-09-13 22:40:39 local time, reports xNVSE 6.3.10 and successfully loaded JIP LN NVSE version 5730 plus ZeGaryHax. It does not report loading JohnnyGuitar or ShowOff. The active NVSE/Plugins directory likewise has neither DLL. Older logs or INI files with those names are not evidence that the plugins loaded for this run.

## Reported failures

All three paths are older loose files under Data/NVSE/user_defined_functions/NVOCombat, not sources delivered in combat packet 1:

- NVO_EmitImpactFeedback.txt
- NVO_OnAltStartCourierStage.txt
- NVO_RecordTacticalImpact.txt

All use AuxTimerStart; the first two also use AuxTimerTimeLeft. Those commands are registered by ShowOff, as confirmed in the local ShowOffNVSE.cpp source. ShowOff was absent during this run, establishing a missing-command compile blocker. The available log does not provide line-by-line compiler diagnostics, so additional errors after dependency repair remain possible. These failures do not prove the functions were actively called: xNVSE precompiles loose UDF files during startup.

falloutnv_error.log also reports an unavailable script command numbered 12778. The inspected log does not identify its script or command name, so no exact attribution is made. It also contains animation/model and faction warnings outside this packet's startup controller.

## Correction within packet 1

The original bootstrap checked only the older registered name `JIP NVSE Plugin`. This installed JIP identifies itself as `JIP LN NVSE`, and xNVSE looks up plugin names directly. The replacement source now accepts either name. The corrected TXT, copy-button page and packet ZIP are synchronized. The user must recompile this updated source for the correction to reach their ESM.

This review ran no tests, builds or game sessions and changed no installed files. It does not establish that the bootstrap quest is attached/running correctly or that the entire Alternative Start flow passed gameplay checks. No new hit diagnostics have been implemented.

Recommended next action, pending user agreement: a small dependency-repair packet for JohnnyGuitar and ShowOff, with exact files and destination. Review the legacy loader situation before enabling additional combat systems. No deletion, quarantine or installation was performed during this review.
