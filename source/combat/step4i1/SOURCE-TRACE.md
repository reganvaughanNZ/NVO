# Source trace: reload callback gap

The accepted4I capture (`source/combat/step4i/LIVE-REVIEW.json`) records2callbacks per stream before reload and0after, while the third native transaction/copy/contact and health-change observations remain. Neither registration success nor native provider return establishes callback emission.

Local authoritative source files and hashes are recorded in `Evidence/SOURCE-TRACE.json`. Existing pinned inputs match `native/NVOCombatCore/sdk-reference.json`; additional lifecycle/table sources are explicitly recorded. No donor binary is rebuilt or changed.

## What the source rules out

In xNVSE `EventManager.cpp:984–999`, Set clears the removed flag on a matching callback, returning true; an active duplicate returns false. Deferred removal at1119–1127 erases only entries that remain removed. Ordinary remove/readd before the deferred drain is therefore intentionally supported, not an established bug.

`FlushOnLoad` at1309–1318 clears whole callback maps for flagged events. `Serialization.cpp:748–763` and `Core_Serialization.cpp:106–120` put the flush before PostLoadGame; `Hooks_SaveLoad.cpp:147–158` puts new-game flush before the NewGame notification. `Hooks_Gameplay.cpp:942,953` sends MainGameLoop before the event-manager drain. The normal source path does not demonstrate a later flush deleting NVO's first-main-loop registration.

ITR's `OnPreDamageHandler.cpp:260,265` registers flush-on-load events; `ITR.cpp:583,694` reinstalls its probes after load and updates them in MainGameLoop. `internal/EventDispatch.cpp:19–60` uses priority−9999 and refreshes after roughly31update calls. A refresh just before NVO registers can transiently cache no listeners. A missing sentinel itself fails open because the xNVSE query returns false and ITR negates it. Neither theory establishes the observed lasting gap.

ITR also gates emissions on thread, reentrancy, positive hit damage/negative health delta and selected target conditions. These private live gates were not captured. Their state must not be invented from the old log.

## Public API and recovery semantics

Basic Set uses priority1 (`EventManager.cpp:2241–2244`). `IsEventHandlerFirst` is public (`PluginAPI.h:1219–1222`, `PluginManager.cpp:149–166`): table index11, x86offset44, no leading interface version. The inspected6.4.8 source supports it; this is the existing minimum. `EventManager.h:759–824` checks the exact callback and `EventManager.cpp:1943–1945` ignores removed entries. True establishes membership at that instant; false also covers competing handlers.

There is no exported exact-membership Boolean. The array-returning conflict API is unnecessary here and its empty-event behavior differs from its documentation. 4I1 uses a positive witness plus bounded idempotent Set, preserving ambiguity. It cannot claim absence when First=false, or failure when Set=false. It repairs a missing/removed registration by adding/reviving it and cannot duplicate an existing one under the inspected contract.

`DispatchEventAlt` returns Normal even when no callback runs (`EventManager.h:918–994`). A fabricated ITR damage event would also invoke third-party handlers. 4I1 never dispatches one. No private event containers, provider variables, hook bytes or return multipliers are touched.

This is a targeted recovery/diagnostic packet, not a proven root-cause fix. If live registry presence survives but emission still disappears, the next investigation is the pinned provider's actual dispatch gates. Damage must remain disabled meanwhile.
