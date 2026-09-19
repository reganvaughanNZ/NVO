# Packet 4I1 — callback survival and bounded recovery

Prepared native 0.3.29/329; **not installed or live accepted**. Installed native328 passed copy association, but its third hit after reload had no ITR pre-hit/pre-health callbacks despite native copy, contact and health-change observations. The cause is not yet established. This packet repairs missing registrations when possible and separates registry evidence from actual callback emission. It does not claim to fix provider suppression before a live check.

## Changes and purpose

- Keep the same ITR event names, callback signatures, public API and priority1. Remove the remove/readd cycle. An idempotent `SetNativeEventHandler` adds or revives a missing/removed callback without duplicating an active one.
- Observe registration at binding, then main-loop calls2,32,64. The latter checks cover the provider's approximately31-loop listener-refresh interval; they do not force its private state.
- After a current, untainted native transaction with valid initial data and at least one copy-stage observation lacks either callback, queue a scalar notice. A copy-stage count includes refused copy observations; this hint does not certify an accepted copy or usable damage. At most three notices per session request a main-loop check. No registry call occurs inside the hit. A missing callback is a diagnostic observation, not proof that a particular event was required (zero damage and weapon hits can legitimately omit a stream).
- Log each stream's first actual emission separately. Successful registration never implies provider emission. Callback and row counts survive later checks.
- Cancel pending/in-flight checks on lifecycle change using a generation and valid-epoch flag. Main-thread and reentrancy guards, saturating scheduling, fixed counters and existing row limits bound work.

At most7 checks/session: initial+3 scheduled+3 gap checks; a gap coincident with a scheduled check is coalesced. Each check makes at most4 pure registry queries and2 idempotent Set calls. Normal ticks only inspect scalar state under the existing lock. No allocations, array scans, synthetic damage events, private ITR state reads or new engine hooks are added. This is a work bound, not measured performance evidence.

## Reading the log

`DAMAGE_EVENT_REGISTRY` includes session/generation/check/loop, trigger transaction and callback counts. Each stream has:

| Field/value | Meaning |
| --- | --- |
| before/after=`present` | Public `IsEventHandlerFirst` positively observed this exact callback active at priority1. |
| before/after=`unverified` | The query returned false; an absent callback or a competing handler can cause it. Never interpret as proven absence. |
| set=`added_or_revived` | xNVSE reported creating or reviving the registration at that call. |
| set=`unchanged_or_refused` | Existing duplicate or another refusal. This is not automatically an error or absence. |

`DAMAGE_EVENTS_CAPTURE` means the monitor is enabled; it replaces the earlier over-broad READY label. `DAMAGE_EVENT_EMISSION stream=pre_hit/pre_health` is actual receipt of that stream once per session. Argument validity remains separately logged; receipt is not proof of committed damage. `DAMAGE_EVENT_SUMMARY` includes bounded check/request counts. If both registrations remain present but no callbacks arrive, the provider-emission problem remains unresolved; do not repeatedly reinstall this packet or enable damage.

## Boundaries

No ESM/ESP, scripts, load order, donor binary/configuration, flight/movement, armour reader, material model or damage rules change. No new dependency. Existing xNVSE6.4.8+/major6 and the inspected ITR2.2.2 build remain required. Event API prefix extends through byte44 on x86; older API versions are not newly supported. Main-thread identity is captured at plugin initialization; the normal supported loader/main-loop thread is assumed.

All damage, wear and stagger authority stays disabled. Exact speed, coherent impact armour, component/application identity and committed damage are separate unfinished work. The4H model remains offline. Copy associations accepted in4I are retained. Native wrapper assembly and hook sites remain unchanged.

## Validation and next user check

`Evidence/VERIFICATION.json` records actual standalone checks, source preservation and x86 DLL/PDB inspection. Synthetic registry fixtures model the inspected xNVSE contracts; they do not execute xNVSE or establish live provider behavior. No game was accessed/launched/closed, no DLL loaded, and nothing installed during preparation.

After separate installation approval, use a living armoured human, a 9mm pistol and standard ammunition. Land one torso hit, reload the saved setup, wait about two seconds of unpaused gameplay, then land two more torso hits. One reload, three landed hits total; no VATS, GECK, video or stress test. Report completion for log review. Acceptance requires actual pre-hit/pre-health streams associated with the native copied hits in both sessions, not registration alone.

Proposed deployment is only the reviewed DLL/PDB pair, with fresh installed-state validation and backup. Reversal restores both backed-up native328 files together while the game is closed; no save conversion is required. Installation/reversal are not performed by this packet's build or check tools.
