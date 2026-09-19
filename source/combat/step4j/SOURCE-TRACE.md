# Packet 4J source trace

This packet labels observed routes into the existing actor-value provider. It does not identify a unique committed damage application. No new hook or donor DLL dependency is introduced. Runtime guard failure leaves the route unclassified and preserves the original call.

## Retained engine call windows

The retained runtime captures predate this packet. Their hashes are checked during packaging; this preparation does not read a running game. `Evidence/SOURCE-TRACE.json` pins both the complete captures and the exact guard windows used by `DamageAttribution.hpp`.

| Return address | Window start / length | Diagnostic label | Evidence and limit |
| --- | --- | --- | --- |
| `0089D82D` | `0089D80E` / 31 bytes | `health_helper_call` | The retained 3L disassembly shows Health AV16 passed into slot `3AC` inside helper `0089D6F0`. Its callers are not exhaustively classified, so this label cannot mean primary hit damage. |
| `0089BDD8` | `0089BDAF` / 41 bytes | `hitme_condition_call` | The retained 3K HitMe trace reads condition damage from HitData and invokes slot `3AC`. The diagnostic additionally requires a watched condition AV25..31. |
| `0089BB8E` | `0089BB65` / 41 bytes | `hitme_condition_call` | Another condition route in HitMe, with explosion-related branches earlier in the function. This call alone does not establish an explosive component. |

3K evidence: `source/combat/step3k/runtime-20260916-100050/hitme-0089A760.bin` and its `.txt` disassembly. Relevant text lines 1589 and 1623–1637 show the first condition path; 1349–1361 and 1461–1475 show the other path. 3L evidence: matching retained `runtime-*/hitme_tail_and_health_apply-0089BF60.bin`, disassembly lines 1944–1956. The selected full path and hashes are recorded in the generated JSON. These windows contain no absolute module-base operands requiring relocation normalization.

At observation time only the matching window is read (at most 41 bytes), after matching one of three return addresses and its AV family. Unknown caller, wrong AV, unreadable bytes or changed bytes gives an explicit unclassified witness. This is a guarded historical code observation, not a guarantee of semantics for every plugin combination.

## Donor contracts

The four local sources are rechecked against the existing `native/NVOCombatCore/sdk-reference.json` pins. Their exact paths and SHA256 values are retained in `Evidence/SOURCE-TRACE.json`.

- JIP `GameProcess.h`, lines 38–63: HitData flag `0x2000` is named `IsExplosionHit`; the carrier union can hold projectile, explosion or source actor; a critical spell/effect pointer is separate metadata. We copy original flags and scalar identity from the initial valid HitMe snapshot. Presence of an effect reference does not establish that it ran.
- JIP `GameForms.h`, lines 64–69 and 110: actor types `3B/3C`, projectile types `3D..40` and continuous beam projectile type `69`. `BGSExplosion` type `51` describes a base form and is not sufficient proof of a live explosion carrier layout. Unknown or unsupported carrier types remain unresolved/other.
- JIP `GameObjects.h`, lines 67 and 527: explosion virtual query and actor-value entry point. No new invocation of the explosion query is added.
- ITR `handlers/OnPreDamageHandler.cpp`, lines 171–209: pre-health dispatch is within the actor-value provider and exposes receiver, source, original delta and mutable multiplier. 4J reads only the first three immutable slots, matches them against the current AV observation and records counts. It neither reads nor changes the fourth multiplier. The six HitMe callsites at lines 18–20 are not given unsupported component labels.

Source contracts and disassembly inform the diagnostics. No donor implementation is copied by this packet; existing credits and component notices are retained.

## Identity and arithmetic limits

An AV call ID identifies one diagnostic provider-call interval. A transaction generation/ID identifies matching active HitMe context; `copiesObserved` counts attempts and cannot select one copy or application. Active scope does not prove primary damage, and absent scope does not prove a timed secondary effect. Explosion flags are original transaction metadata, independent of carrier type and caller route; missing context is logged as unknown rather than a false flag.

The existing before/after actor-value differences are inclusive net observations. A parent can include nested calls; pre-hit values, pre-health arguments, net health change, condition change and repeated callbacks must not be summed as independent damage. All new rows retain `component_verified=0`, `application_verified=0`, `primary_or_secondary=unresolved`, and non-additive interpretation. Actual ownership/deduplication must be established in later work before gameplay authority.

AV lifecycle generations reject stale reads and returns, including same-session reload/rearm. Old continuations remain on the bounded stack until they unwind, but cannot supply a fresh frame's parent, taint or nesting accounting. Current thread and original receiver/source guards remain required. Wrapper assembly, hook sites, installer and provider chaining are unchanged.

## Work and validation boundaries

One matching route requires at most one bounded 41-byte read. The existing maximum 16 nested frames and 96 detailed calls per session remain. Each detailed AV call now has at most four rows instead of two; no per-callback row or console message is added. Existing global log limits still apply; omitted diagnostics confer no gameplay authority. These are implementation bounds, not measured performance claims.

Standalone tests execute production observation code and assembly bridges with synthetic bounded memory/getters/providers. They do not invoke the game or load the plugin. Fresh counts and exact source/build hashes are in `Evidence/VERIFICATION.json`; unchanged model/armour-reader suites were not rerun.

For the optional inventory kit only, base `FalloutNV.esm` was read to verify the five form IDs recorded in `Evidence/TEST-KIT-FORMS.json`. No game record was modified and no game process was accessed, launched or closed. The batch does nothing until installed and explicitly run by the user.
