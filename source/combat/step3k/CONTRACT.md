# Packet 3K: observe actor-value application

Status: Native319 installed. Offline probes and main-menu guard initialization passed; user gameplay checkpoint pending. Runtime capture completed at the main menu in runtime-20260916-100050. The user authorized the assistant to launch the game while working remotely; no save was loaded, and the game was closed after capture.

The user approved a small diagnostic packet after3J. The existing3H observation joins a hit before ITR, its copied inputs, and pre-health notification, but does not measure an actor-value change. Entry damage52 later becoming requested health delta-104 remains unexplained. Callback counts are not proof of applied damage.

## Intended scope

Wrap the existing ITR2.2.2 DamageActorValue vtable chain for Character, Creature and PlayerCharacter, preserving original arguments and calling that chain exactly once. This is observation, not a new damage owner. The underlying engine method may internally scale, clamp, ignore, or trigger further changes. Record negative Health16 and body-condition25..31 calls. Other calls continue unchanged. No armour, injury, difficulty, health GMST, projectile or saved-record changes.

Read current actor value and its damage component before/after the provider call, using the matching ActorValueOwner instance at actor+0xA4 and verified class methods. Creature conditions use the observed engine remapper at8D4A80, which can map a requested condition to45; record both codes. Associate a call with a currently active hit transaction only when receiver/source identity agrees. Distinguish method-entry requested delta from the observed net value change. Do not label the ITR argument as the engine's final argument or a provider return as a single storage write.

Snapshots on the main thread only. Recheck actor identity and owner table before post-read. No pointer retained beyond a synchronous call. Nested calls mark the enclosing measurement as containing nested work. Session overlap, unsupported methods/classes, foreign hooks, nonfinite values, read failures and depth overflow must reject interpretation while preserving original execution. Detail limits must not suppress engine calls or attribution IDs. Use the current transaction lock without acquiring it while holding the new observer lock; no engine getter or original provider call under either lock.

The follow-up test uses an ordinary close-range Hunting Rifle torso hit, one close-range VATS left-leg selection, and one punch after reloading the same save. Use living human targets and report misses. No repeat of long-range misses, stress tests or the full Ultra317 review. Damage replacement stays off.

## Evidence and guard requirements

- Frozen318 source: baseline-318/manifest.json.
- Installed ITR source: OnPreDamageHandler.cpp; Hook_DamageActorValue calls a saved class-specific original and can scale health after event handlers. It forwards non-health AVs as well.
- ITR deployed thunk RVA34C1B; original-pointer RVAs7C754/7C748/7C738, class order Character/Creature/Player.
- Engine class tables1086A6C/10870AC/108AA3C, DamageActorValue slot3AC. On-disk metadata points to881130/8D49F0/93B7A0.
- Secondary ActorValueOwner tables verified via on-disk RTTI offsets0xA4 and matching class names:10869A4/1086FE4/108A974. Current-value methods at slot0C:8805F0/8D4870/93ACB0; damage-component methods at slot14:8B0D70/8B0D70/94C490.
- JIP source GameForms.h defines the owner interface; GameObjects.h places it at0xA4. JIP source hooks.h illustrates body-condition handling, but its event is not being substituted for a committed-value observation.
- The executable's method bodies are encrypted on disk. Offline disassembly of those bytes is not engine evidence. tools/read_health_route_runtime.ps1 captured only bounded code/vtable regions from the running game using QUERY_LIMITED_INFORMATION|VM_READ. The helper does not launch, call the engine, inject or write memory. The assistant separately launched through NVSE with user authorization. Captured code and table bytes were stable across two reads; no save was loaded.
- Runtime-derived guards cover the complete directly called getters/remapper and original damage-method entry prefixes. The ITR wrapper is fingerprinted with its PE relocations normalized, and its three saved original pointers and all dispatch/getter slots are checked at installation and capture start. These guards do not claim exhaustive validation of every downstream engine or plugin function. Existing downstream hooks remain intact.
- Fourteen offline checks passed. The new observer probe mocks engine reads; it does not validate real actor-value semantics. Its entry/return instruction sequences match the production object. Existing flight, copy and hit-transaction bridges are unchanged. A main-menu-only load check can establish guard installation, but only the user's live hit test can establish observed changes.

## Console cleanup

Native319 removes only the healthy PrintC flight-kit reminder. Kit batch files and explicit failure notices remain. The reminder was never an attempted automatic batch execution.

## Remaining limits

A before/after method measurement can establish net actor-value change, not by itself an exhaustive count of internal storage writes. Zero/positive/unscoped effects, dead actors, god mode, clamping, secondary callbacks and off-thread work need explicit interpretation. Final damage authority remains gated on the applicable engine path and supported scope, followed by the mass/units/contact/admission rules from the prior review. Do not prematurely close317-01 or enable damage.
