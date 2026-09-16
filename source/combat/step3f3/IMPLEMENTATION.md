# Packet 3F3 implementation and review boundary

## Corrected field interpretation

The earlier review proposed observing Projectile + 0x14C based on the generic name `range` in JIP/ShowOff headers. Saved runtime code shows that field being checked in the passing-sound path at 0x009BF0BB, followed by a sound call and the played-sound flag at +0x148. It is not the firing range selected for this diagnostic.

Projectile + 0xD4 is named `fRange` by Stewie's layout and used as range by ITR's near-miss handler. The authenticated saved engine route initializes it at 0x009BDD10 and conditionally multiplies it at 0x009BDDB5-0x009BDDC0. The referenced setting at 0x011CE5F4 is `fCombatIronSightsRangeMult` in both JIP and Stewie setting maps. The saved capture hash and source hashes are pinned in ENGINE-FINDINGS.json. No engine binary is distributed.

This establishes the appropriate observation field and a conditional aiming-related multiplier. It does not establish a universal VATS multiplier, current multiplier value, or exact reason any earlier bullet was destroyed. New range-versus-travel observations must corroborate those conclusions. Existing snapshots still read base projectile range at base + 0x6C.

## Narrow code change

FlightPreview.cpp adds optional reads of +0xD4 (instance firing range), +0xC8 (raw projectile flags) and +0x90 (impact byte) only after existing snapshot/lifetime/identity checks. A cached creation observation is stored in NVO's sampled-shot state. Current and initial values are reported at creation, first impact and destruction; no extra update hook, actor scan, timer or engine call is added.

Read failures do not gate creation, physics tracking, existing sampling or retirement. Invalid range values are represented by zero with validity bit 1 unset; flags and impact reads use bits 2 and 4. Only range values finite and between zero and 1e12 are considered numerically valid. Zero is not interpreted as an active positive limit. Raw flags are not presented as a decoded aiming mode.

FLIGHT_RANGE includes session/lifetime and projectile/source/weapon/ammo/base identity, current and launch validity masks, base/current/launch range, the current-to-base ratio with ratio_known, range_changed, absolute age/travel, signed range_minus_travel, range_reached, current/launch raw flags and impact state. range_reached means only that logged travel meets a positive valid instance range; `cause=unverified` explicitly prevents equating it with a proven destruction reason. The first-impact row can have impact_seen=0 because that field describes prior observed callbacks; phase=impact identifies the current callback.

Rows use the existing first-32-sampled-lifetimes cap, with at most three attempts each (96 per load), and the unchanged process-wide detail cap. FLIGHT_RANGE_SUMMARY uses the existing summary reserve and reports observation attempts, optional-read failures and log-write failures. No new console messages. Per-frame physics logging, limits and file ownership are unchanged.

FlightPhysics.cpp, FlightTiming.cpp, NativeObserver.cpp, CurrentHit.cpp, DamageEvents.cpp, NativeLog.cpp and all headers are unchanged from native 313. All nine physics bridges are compared in the compiled objects. Plugin.cpp changes version/header only; CMake updates the version. Damage authority remains off. The terrain correction, integrator, collision handling, profile ownership, range settings, ammunition effects, ESP and INIs are unchanged.

## User checkpoint

Use one ordinary Hunting Rifle with standard .308. Record one hip-fired shot outside VATS, then try the original distant VATS miss. Wait 15 seconds after each attempt finishes, so destruction can be logged. If needed, up to two additional reproduction attempts; no full weapon cycle or forced reload. Report shot order and whether each was a hit/miss. The test may still not exercise the failed-terrain condition; do not mark that correction accepted without its correction/accounting evidence.

## Reversal

Close New Vegas and restore both NVOCombatCore.dll and NVOCombatCore.pdb from the installation backup's originals/Data/NVSE/Plugins directory. This restores native 313. Keep the existing records, profiles, activation and saves. The installer records the exact backup, preserves the previous log, verifies protected files, and rolls back the two-file transaction if a write/check fails.
