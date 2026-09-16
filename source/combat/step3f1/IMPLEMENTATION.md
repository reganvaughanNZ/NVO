# Packet 3F1 implementation and boundaries

The immutable3F capture `f57f04e1f1b9ce8bae6fdbf22bf25f498e413e78319ff0d93c53a286de384010` contains17 correct ammunition selections and three `applied_displacement_mismatch` rejections, on lifetimes8(AP),10(standard),13(standard). Detailed traces ended before their failures. The user confirms those projectiles missed. The capture does not identify their aiming mode or precise rejection measurements.

## Diagnostic changes

`FlightPhysics.cpp` adds one helper called only from the existing `!matched` accounting branch, after incrementing the existing mismatch count and before the unchanged rejection/return. It receives the already-validated local measurements from `BeforeAccounting`, and reads the plugin's own current `Track`. It performs **no extra engine-memory reads or writes** and does not dereference the stored controller pointers.

The helper distinguishes `vectorError > tolerance` from `positionError > tolerance`. It records expected/actual vectors, old/proposed velocity, start/end position, position delta/residual, submitted/returned local vectors, engine lifetime/travel, timestep, accepted integration time, source/weapon/ammo/private base/profile, and current controller counters/identity. Engine time/travel now comes from the failure observation, rather than a later destruction summary. Velocities are m/s, displacement/positions are game units; local controller vectors remain local coordinates. `accepted_elapsed_s` excludes the rejected proposed step. Current snapshot contacts and impacted flags were checked zero before this branch; that does not imply all possible collision/target corrections are understood.

Each of the first16 mismatches per loaded session can emit four rows. The helper does not gate on `t.logged` or the routine entry cap. It emits one detail-limit notice at mismatch17, then stops further failure detail. The normal mismatch count and rejection guard remain active. Two plugin-owned counters track complete four-row writes and reports with a failed row write; both reset with the existing loaded-session state. Diagnostic summary reports omissions separately. All new failure record names contain REJECT, so the unchanged NativeLog uses its priority reserve. No console call, message box, general per-frame log expansion or new file is added.

Conservative format-length checks reserve more than the maximum formatted width of the numeric fields and confirm every new line stays below NativeLog's766-byte payload limit. The largest bound is597 bytes. The process-wide1024-priority-row limit and disk failure remain practical delivery limits; a report is counted complete only when all four writes succeed.

## Preserved behaviour

All additions to FlightPhysics.cpp are delimited by `NVO_3F1_DIAGNOSTICS_BEGIN/END`. Removing these additions and ignoring whitespace yields the exact prior physics source token stream. The added helper only calculates/logs diagnostic values and changes its two reporting counters. Track layout is unchanged.

The following are retained: integrator equations/stages, profile values, baseline step, displacement and position tolerances, all rejection paths and subsequent control flow, collision checks, engine-read routines, hook locations and ownership checks, patch transaction/rollback logic, locks, runtime capacity and normal trace budgets. NativeLog and the other16 source/header files remain byte-identical. Plugin.cpp changes only version metadata to312/0.3.12/phase3F1; CMake's version is updated accordingly. Eight naked assembly bridges have identical compiled instruction bytes to build311. The x86 PE still exports only NVSEPlugin_Query and NVSEPlugin_Load and its DLL/PDB GUID/age pair is checked.

No stock/private record, profile INI, game setting, damage event, ammo selection or save serialization is changed. The helper runs inside the existing physics lock and ErrorGuard; the existing bridge preserves machine state. Additional disk-log work occurs on failures only, plus a ready/summary row per captured session. This is a diagnostic update, not a correction to the failing flight.

## Source and delivery

`baseline-311` preserves the pre-edit source. `SOURCE-CHECKS.json` and compiled `static-evidence.json` record verification and bounds; the package includes complete current native source, the SDK-boundary/provenance notes, notices, compiler output, disassembly and matching PDB. The installer verifies current3F records/configuration and prior build311 before changing only the DLL/PDB, with verified backups and hardlink-safe replacement. It preserves other extenders, NVO/RD, both activation files, old kits and the latest log copy. It never launches the game.

User acceptance needs a reproduced failure with complete measurements, or an honest report that it did not reproduce. Ammo persistence stays separate. The final manually selected HP shot after a save load supplies the still-missing post-load firing observation. Do not loosen tolerances or enable armour/damage authority based only on partial success or an unreproduced mismatch.
