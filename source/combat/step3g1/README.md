# Packet 3G1: corrected impact-speed diagnostics

Native316 / 0.3.16 corrects the collision boundary comparison and records impact details for the first32 accepted projectile lifetimes per load. This establishes model estimates for future armour inputs. It does not enable damage replacement or change flight rules.

Offline replay of your prior log produces six eligible model estimates within the existing tolerances; both first-segment contacts remain unavailable. Seven invalid-input checks and bounded cache/reset/duplicate/later-shot checks passed using the actual C++ model and cache logic with captured snapshots. These checks do not replace the live checkpoint.

Only NVOCombatCore.dll and its matching PDB are replaced. Keep NVO.esm and NVOFlightPilot.esp active with their current masters and configuration. No GECK work or new dependency.

Follow START-HERE.html for three shots: one close solid object, one live target outside VATS at roughly your previous final headshot distance, and one live target at similar distance using VATS. At most one replacement per missed check. Wait three seconds between impacts and20 seconds after the last shot, then exit normally and report shot order. No reload or stress test needed. I will read the game-root NVOCombatCore.log directly.

Expected new details: IMPACT_BOUNDARY validates the full endpoint/accounting, IMPACT_MODEL reports a model estimate or an explicit unavailable reason, and IMPACT_CALLBACK correlates contact. IMPACT_COVERAGE_SUMMARY reports baseline contacts and any lifetimes beyond32. Existing PHYSICS_NO_UPDATE/lives_without_update terminology can include first-segment contact; it is not by itself a missing hook. No new console output.

Installation/IMPLEMENTATION.md explains the bounds and reversal. Installation/INSTALL-3G1.md records the two-file backup after installation. Source, donor notices and replay evidence are included. Estimates remain non-authoritative and physical units remain uncalibrated.
