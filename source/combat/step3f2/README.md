# NVO Combat Packet 3F2 — failed terrain query correction

Purpose: stop a tracked NVO bullet from being raised to the engine's default terrain height when no valid terrain height was found. Shot3 in the previous test was a VATS miss, as clarified by the user.

Build313 / 0.3.13. Only NVOCombatCore.dll and its matching PDB are replaced. Keep NVO.esm, RD.esm, NVOFlightPilot.esp and the existing INIs active as before. No GECK edits or compilation are required.

The loaded engine code shows a terrain query that initializes its result to -2048 and can return false. Generic movement ignores that bool and raises the candidate position when the returned height is more than30 units above it. This matches the previous failure's geometry. The new log must establish that the failed-query path is reached in the test and that corrected movement passes the unchanged displacement check.

The correction applies only to a verified private projectile with an already accepted baseline and an active NVO movement step, no observed impact/contact, a failed terrain query, its expected default result, and a candidate displacement within the existing tolerance. It changes one checked stack-local height result. Successful terrain queries and collision handling stay with the engine. No damage rules change.

Open START-HERE.html for the short test. The log remains Fallout New Vegas/NVOCombatCore.log. A confirmed miss is useful; a hit or failure to reproduce must be reported honestly. HP selection persistence is still unresolved; select HP again after loading.

Rollback: with the game closed, restore both previous DLL/PDB files from the installation backup listed in Installation/INSTALL-3F2.md. Keep the existing3F records/configuration. The backup returns native312. No saves are deleted or modified by the installer.
