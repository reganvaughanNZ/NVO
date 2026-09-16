# Packet 3H: pre-provider call contract

## Purpose and boundary

Ultra finding317-01 showed `ITR:OnPreHitDamage` before the existing JIP copy-input join. Native318 observes six exact game E8 call sites that currently enter the inspected ITR2.2.2 HitMe thunks. Input is the caller's ActorHitData pointer, receiver in ECX and a stack attack-class argument. Each ITR thunk returns with RET8 and calls its recorded original once. Source and installed binary agree. ENGINE-FINDINGS.json pins the six sites, complete127-byte thunk fingerprints, relocations and recorded-original locations. No general signature scanning or unsupported target chaining.

An entry copies the existing0x64 hit layout and readable form identities before ITR dispatch. It obtains ammunition from the existing guarded projectile layout and matches a current creation lifetime by pointer/form/source/weapon/ammo. Missing or nonprojectile carriers stay unknown. No equipped-ammo substitution. The packet logs identity, numeric damage context and raw region/flags; remaining copied fields are not promoted to gameplay inputs.

## Transaction states and identity

1. `HIT_TX_BEGIN` and `HIT_TX_DATA`: before ITR; a process-wide monotonic ID and parent ID identify this invocation. A creation lifetime is separate and may be absent or shared by more than one invocation.
2. `HIT_TX_STAGE stage=itr_pre_hit`: callback within the same thread's top call scope. Provider arguments lack a hit pointer, so even matching target/source/weapon is labelled `scope_only`.
3. `HIT_TX_STAGE stage=copy_input`: compares the actual copy-input pointer and identities against entry, and checks receiving process. Only an untainted, valid same-pointer match is labelled `exact_input_pointer`. Otherwise it remains scope-only; no nearest-time search or parent fallback.
4. `HIT_TX_STAGE stage=itr_pre_health`: a scoped health-delta input. It may include nested script/effect health loss and cannot establish final cause, multiplier or committed loss.
5. `HIT_TX_RETURN`: original ITR call returned. No post-return pointer read. This is a terminal acknowledgement of the observed **call**, not a terminal acknowledgement of health/limb application. Early returns and queued/replayed work must remain distinct from actual application.

Entry and return brackets permit an exact earlier input to be compared with later data, closing the timing obstacle for observation if confirmed live. They do **not** establish one health/limb application, final downstream scaling, duplicate-pellet policy or an authority suitable for damage writes. Additional engine-boundary evidence is still required before replacing damage. ITR's public multiplier remains unused by NVO.

## Reentrancy, threads and unsupported cases

Each thread has a16-frame LIFO stack. Nested observed calls get new IDs. Off-main-thread calls are observed on their own thread even when ITR skips its event dispatch; a later replay is another invocation and is not assumed equivalent. No cross-thread/time-window matching.

At depth overflow the incoming call passes through unchanged without a replacement return. Its enclosing frame is marked tainted, suppressing claims of exact association for callbacks until it unwinds. There is no search into older frames for a convenient matching actor. Invalid snapshots still receive a call scope so events cannot accidentally inherit a valid parent identity.

The first64 calls per load get detail rows, at most8 stage rows each (704 possible detail rows including begin/data/return). IDs, nesting, returns and stage counters continue beyond those budgets and even when the logging sink fails. This state is diagnostic; future gameplay needs its own defined application/admission policy rather than using these detail limits. Logger global bounds are unchanged.

Save/menu/quit boundaries deactivate the capture. Pending continuations are never cleared or reused; an old-session return always restores its own caller and cannot update new-session counters. No hot unload support. Installation occurs only during deferred startup, before gameplay, under the same no-concurrent-call assumption as the existing physics hooks. The code changes only guarded call routing/return continuation, not hit data, actor values, ITR event products, profiles or records.

## Open before damage

Actual application acknowledgement, downstream health/limb/critical scaling, actor impact-speed geometry, calibrated unit/mass policy, contact versus hit-data versus VATS-aim region, first-step/unknown handling, wider admission failure behavior and conditional donor damage ownership remain open. RD and Brahmin Baron findings remain assigned to separate record/ownership work. Current scope is read-only and narrowly instrumented; full Ultra review is not repeated here.
