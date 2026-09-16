# Packet 3B3 first gameplay review — 15 September 2026

**The user completed the requested firing/reload sequence. The timing diagnostic did not capture movement updates because its thread restriction rejected them.** This is an NVO observer limitation, not a reason to repeat the test unchanged or alter bullet speed.

## Evidence

Read directly from the game-root `NVOCombatCore.log`, twice with matching bytes and stable modification time, then archived at `captures/2026-09-15-3B3-300ef3ba390a/`. Archive contains the original log and structured `analysis.json`.

- SHA256: `300ef3ba390a0f91766a632b8d13e082eae25340ddc0bd6b96c152c462b8f1bf`.
- Size: 18,364 bytes. Last write: 2026-09-15 11:12:30.471337 local.
- User reports entering through `coc` from the main menu without character creation, spawning the test guns and shooting a Goodsprings water tank.
- NVO version 303 initialized with `new_game` in session 1. The same process then reports `pre_load_game`, `load_game`, a successful `post_load_game` in session 2, and normal `exit_game`.
- Session 1: two private 9mm shots and two private .308 shots. Session 2: one of each. All six impacts identify target reference `00106B5E`, consistent with the user's report of one target; this review did not independently resolve that form's name.
- Six creations, six impacts and six destructions; all tracked identities and matching private ammunition/base records. Zero reported unmatched lifetimes, reused live addresses, capacity overflow, read failures or open lifetimes. Both timing installations report ready. The twelve legacy travel rows contain two terminal samples for each of six shots, not twelve shots.

## Why the new measurement is absent

`FLIGHT_TIMING_SUMMARY` reports:

| Session | Accepted lifetimes | Steps logged | Foreign-thread skips | Invalid reads | Nesting limit |
|---|---:|---:|---:|---:|---:|
| 1, before reload | 4 | 0 | 9 | 0 | 0 |
| 2, after reload | 2 | 0 | 6 | 0 | 0 |

`FlightTiming.cpp:291` records the capture-initialization thread in `gThread`. `Before`, line 105, rejects a tracked update whenever `GetCurrentThreadId() != gThread`. The 15 counted rejections demonstrate that the wrapper was reached for tracked projectiles on another thread. They do not identify that thread's specific engine role or prove that every engine update passed through this boundary.

The filter runs before sampling and before substituting the return continuation. Consequently, none of these six shots exercised the new before/after sampling or return-continuation path. A ready message, clean exit and zero invalid reads must not be presented as acceptance of that unexecuted path.

The user's main-menu `coc` route produced the required lifecycle initialization, and the later actual reload succeeded. Nothing in this log implicates the entry shortcut as the cause of the timing rejection. Do not ask the user to repeat character creation to work around the observer.

## Decision and next bounded correction

Accept the user's test sequence, lifecycle initialization, private identity matching and reload coverage. **Do not accept packet 3B3's movement-speed measurement or its sampled return path.** Leave version 303, configuration and projectile speeds unchanged during this review. Native flight/damage authority remains disabled.

The next correction should support observations on the thread executing each projectile update, while preserving synchronous ownership and bounded data. It must review cross-thread destruction/reload and event attribution, rather than merely removing the thread check. In particular, existing thread-local impact markers cannot identify callbacks delivered on another thread; use synchronized per-lifetime event counters or another verified correlation mechanism. Keep engine calls outside observer locks, skip retired identities before post-call reads, retain call-scoped continuations through suspension, and log actual update thread IDs. Recheck the compiled entry/return path, then deliver one corrected diagnostic for the user's next check.

No changes to native code, installed files, game state or settings were made for this review. Do not repeat the same test with the current DLL. Await user confirmation before preparing/installing the correction; this remains Step 3 diagnostic work, not permission to begin drag, damage, Directional Shooting or Stewie integration.
