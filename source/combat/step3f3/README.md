# Packet 3F3: firing-range diagnostics

This packet records the range assigned to each sampled bullet, alongside its age, travel and impact state. It helps explain why recent misses ended earlier than the original long VATS flight. Native version: 314 / 0.3.14.

Only NVOCombatCore.dll and its matching PDB are updated. Keep NVO.esm and NVOFlightPilot.esp active with their existing masters. No GECK compilation, new dependency or configuration change is needed.

Follow START-HERE.html for the short user check. Compilation/static checks do not establish gameplay success. The terrain correction remains unverified until a failed query is corrected and the following movement matches.

New FLIGHT_RANGE rows appear in NVOCombatCore.log in the Fallout New Vegas game root. They are bounded to creation, first impact and destruction for at most 32 sampled lifetimes per loaded session. A summary records unavailable optional reads and log failures. Range telemetry never controls physics or writes to game objects.

Source details and evidence are in Installation/IMPLEMENTATION.md and ENGINE-FINDINGS.json. Existing donor credits and notices remain included. Once installed, Installation/INSTALL-3F3.md identifies the exact backup and reversal instructions.
