# Packet 3B3A stress review — recorded coverage accepted, final run truncated

User reports a stress test with multiple reloads and says the last two were VATS with the private test weapons. Whether this means the last two loaded runs or last two individual shots is pending clarification. The log has no explicit VATS-mode field; do not invent that mapping.

Read and archived the game-root NVOCombatCore.log on 2026-09-15. Archive: `captures/2026-09-15-3B3A-stress-d68774aa6256/`, including machine-readable analysis.json. SHA256 d68774aa6256672caa76b50ce1f78157c50cabc54fb81e918bac28d4957ccb3f; 1,619,818 bytes; last write 11:52:04.158610 local. Version 0.3.4 / phase 3B3A.

## What the capture establishes

- Ten successful loaded captures, comprising initial load and nine same-process reloads. Capture, flight-preview, timing and damage-event readiness return every time.
- At least 3,201 projectile creations observed (highest creation serial, incremented once in OnCreate and not reset on capture reload). Broader streams include 834 valid HIT_CONTEXT rows, 392 DAMAGE_INPUT and 377 HEALTH_INPUT rows. These are diagnostic callbacks, not numbers of applied damage events.
- Thirty-three private pilot lifetimes admitted for timing. Thirty-two have complete destruction summaries; the last has only its initial no-motion observation before logging stops. Ninety-six paired movement/state rows: 33 no-motion, 31 moving and 32 collision. Eight private lifetimes per capture remains the timing cap; not every fired test shot is timed.
- All 31 valid moving observations agree with configured speed within 0.0003682%. Actual positional displacement agrees with the recorded distance increment within 0.0001% relative tolerance. Both private profiles retain the same settings as the prior accepted capture; installed NVOFlightPilot.esp still hashes f5fd916841ebf5aafae5c467a7e17dd67fdf1faf1abc9368f66e936f146244ab.
- Init thread 12708 and update thread 11924 differ. The sampled return path continues to execute under the recorded combat load. All available timing summaries show zero invalid, overlapping, retired-during-update or nesting-limit cases. Completed pilot shots have no pending update, blocked state or per-shot step cap. No timing-disabled/overlap/unavailable diagnostic rows appear.
- No reported invalid hit context, invalid damage event, live-address reuse, table overflow, memory-read failure or flight-preview identity mismatch in the available summaries. This is not a claim that every callback after the log cutoff succeeded.

## Reload-boundary events

The broader projectile stream has 20 unmatched impact/destruction callbacks. Every visible unmatched row is among the first four event rows after a successful reload, involves NPC-source IDs and weapon 0007EA24, and lacks a captured creation in that new session. Counts in the summaries agree with these rows. These are not missing private-pilot lifetimes. Capture reset and immediate post-load projectile callbacks plausibly explain them; the log does not prove precisely whether each represents a loaded projectile or engine cleanup.

Several reload summaries still contain open ordinary projectile lifetimes (up to five in final pre-load summaries), which are cleared on capture suspension. Reloading while combat projectiles exist does not establish a leak. The private timing summaries are all closed before the recorded reloads, so a timing continuation spanning reload remains unexercised. Preserve these distinctions in future ownership/write work; do not fabricate creation metadata for unpaired callbacks.

## Logging cutoff and VATS limits

`NativeLog.cpp` has a fixed process-wide limit of 8,192 rows. It appends `END native log process limit reached` after the last allowed row and suppresses later writes. Reload resets individual capture budgets but not this process-wide limit. The archive contains exactly 8,192 normal rows plus that footer. This explains the abrupt end; it does not indicate a crash. It also suppresses exit lifecycle and final summaries, so this log cannot prove clean shutdown or absence of a later failure.

The ninth run has eight completed private-9mm timing samples, 35 steps (19 moving). The tenth run contains eight admitted private-.308 samples, seven completed and one cut off after startup; 19 steps including four moving observations. If the user's last-two statement refers to these runs, this is useful user-attributed partial VATS coverage. If it means only the final two shots of the entire test, the cap may have hidden them. Await clarification; do not mark comprehensive VATS flight/damage behaviour accepted from this log. Earlier general event and preview caps also intentionally suppress detail while lifecycle bookkeeping continues, as verified in NativeObserver.cpp.

Performance, smoothness and an end-of-run crash cannot be measured from this file. The user has not reported those symptoms in this message. No assistant gameplay or runtime instrumentation was performed in this review.

## Decision

Keep the prior bounded movement-timing acceptance. Accept the additional recorded combat-load and repeated-reload evidence with the stated unpaired post-load callbacks and truncation. No repeat of the full stress test is requested. Keep installed 304, NVO.esm, private ESP/INI and all gameplay settings unchanged.

Before future long tests, preserve bounded space for reload/exit summaries and critical diagnostics, or rotate bounded capture logs; merely raising an unlimited logging budget is not the solution. An explicit VATS-state marker would remove dependence on recollection of shot order. Include only the necessary logging changes in the next separately authorized packet. Gravity/drag remains the proposed next feature, with velocity-write ownership and units verified before enabling native flight. No new packet has been prepared or installed by this review.
