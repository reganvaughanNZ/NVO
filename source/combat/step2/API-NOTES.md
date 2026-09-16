# Packet 2A implementation evidence and limits

Sources were inspected locally, read-only. Local source and installed DLL versions can differ; this inspection establishes the API contract used for preparation, not successful execution. The user performs compilation/runtime checks.

## API contracts used

| Source | Evidence used |
|---|---|
| JIP `internal/hooks.h`, `OnHitEventHook` | Global hit callbacks invoked on the struck actor, without UDF arguments. |
| JIP `functions_jip/jip_fn_actor.h` | SetOnHitEventHandler takes callback, add/remove flag and optional actor. GetCurrentAmmo reads the source actor's current ammo entry. |
| JIP `nvse/GameObjects.cpp`, `Actor::GetHitDataValue` | Damage, attacker, hit object, weapon and armour flag are read from lastHitData. The hit object is preserved as a raw form ID, not assumed to be a base projectile or safely cast to a projectile reference. |
| JIP `internal/patches_cmd.h` | GetHitLocation implementation and hit-context restriction. |
| JIP `functions_jip/jip_fn_projectile.h` | Read-only projectile reference distance, lifetime and damage getters. |
| ShowOff `SHOWOFF-NVSE/Events/ShowOffEvents.h` | OnProjectileCreate calling reference is projectile, arguments source and weapon. OnProjectileImpact adds target. OnExplosionHit calling reference is explosion, arguments target then source. GetExplosionHitDamage reads the event's damage pointer. |
| xNVSE `nvse/nvse/Commands_Scripting.cpp` | GetSelfAlt returns thisObj; used to retrieve the calling reference. |
| xNVSE `nvse/nvse/Commands_Script.cpp` | CompileScript returns cached loose UDFs unless forced. The packet never forces recompilation. |
| JIP `internal/jip_core.cpp`, `JIPScriptRunner` | `ln_` loader runs on load/new game. It compiles partial script source, so the loader has no GECK quest block. |
| JIP `functions_ln/ln_fn_utility.h` | GetINIFloat resolves supplied filename under Data/Config. |
| JIP `functions_jip/jip_fn_utility.h` | WriteStringToFile arguments are path, append flag, format string and format arguments; returns 1 on successful file open/write path. |
| JIP `internal/jip_core.h`, `AuxVarInfo` | `*` selects temporary variables; following `_` selects global namespace. Prefix `*_NVODiag` is owned only by this packet. |

Source roots and exact SHA-256 hashes are recorded in `manifest.json`. Function/record names in this table are existing extender APIs, not new NVO native commands.

## Capture boundary

No gameplay setters are called. The only writes are four diagnostic temporary auxiliary variables (enabled/count/limit/writer), the diagnostic log, and handler registration/removal. No timers, projectile cache, background world scans, damage interception, serialization or hooks are added to NVOCombatCore.

Records are bounded by a configured global row allowance per initialization. Handlers check enabled before formatting strings. The writer opens/appends/closes each row; this is deliberately short diagnostic capture, not intended as a permanent combat telemetry service. Callback order and multiplicity remain evidence to gather, not assumptions to build damage authority on. The bootstrap quest's bCombatEnabled remains 0.

Shotgun pellet independence, explosive impact versus blast, attacker attribution, hit data freshness and exact ammo association still require the user's capture and later native instrumentation. No conclusion about damage being applied exactly once can be drawn solely by counting these callback rows. Direct inspection/review was performed, but no compilation, automated tests or gameplay checks were run.

## Dependencies and credit

Uses xNVSE by the xNVSE team, JIP LN NVSE by jazzisparis/luthien, and ShowOff xNVSE by Demorome. JohnnyGuitar remains part of the accepted NVO foundation but this packet adds no JohnnyGuitar commands. No donor implementation source or third-party binary is bundled in this packet. Retain the existing packet 1 donor credit and permission notices when later adapting donor gameplay.

Latest inspected game-root nvse.log reported xNVSE 6.4.8, JIP LN NVSE 5730, JohnnyGuitarNVSE 525 and ShowOffNVSE Plugin 184 loaded correctly. This is an observed setup, not a promise of support for every older version. The packet requires the listed APIs and was prepared against that setup.
