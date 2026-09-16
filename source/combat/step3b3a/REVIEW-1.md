# Packet 3B3A test review — accepted for movement timing

Reviewed 2026-09-15 after the user reported finishing. Read the log directly and archived it before any new launch. This turn changes review/checkpoint documents only; no new DLL, installation, GECK work or assistant gameplay.

Evidence: `captures/2026-09-15-3B3A-4f2f5370f3a4/NVOCombatCore.log` and `analysis.json`.

SHA256: `4f2f5370f3a4a170be395bd38da18c001083d63a59ed6d6bd7aae6ee1a994c9e`. Size 82,112 bytes; last write 2026-09-15 11:33:00.103235 local. Header identifies 0.3.4 / phase 3B3A. Normal exit_game lifecycle is present.

## Result

The corrected thread handling captures movement successfully. Ten complete private-pilot lifetimes: one shot per weapon before reload, four per weapon after reload. Both sessions initialize successfully. There are 71 paired FLIGHT_STEP/FLIGHT_STEP_STATE observations: 51 moving, 10 startup no-motion, 10 collision. All shots target ref 00106B5E, matching the user's previous water-tank test target. No extra repeat is needed.

| Profile | Shots | Valid moving updates | Measured/configured speed range | Maximum absolute percentage difference |
|---|---:|---:|---:|---:|
| Private 9mm | 5 | 36 | 0.999993634–1.00001012 | 0.001012% |
| Private .308 | 5 | 15 | 0.999998048–1.00000237 | 0.000237% |

Recomputed distance delta / actual timestep and its ratio to the configured speed from the logged numbers. Moving-step distance and positional displacement also agree within 0.0001% relative tolerance. These are observed engine-unit speeds for the two private profiles, not an independent validation of the assumed 70 game units per metre or muzzle-vector direction.

## Timing and lifecycle evidence

- Update thread 21028 differs from capture initialization thread 9436. All 71 sampled updates now complete on that thread; the sampled entry/return path is exercised. Earlier 303 skipped these entries before sampling.
- Every lifetime begins with one zero-motion update, followed by moving updates and a collision update. Lifetime stays unchanged inside the missile method; gaps advance between calls while gap_distance stays zero. The prior slower terminal distance/lifetime average is consistent with the startup interval and terminal sampling, not a need to increase configured speed. Keep speeds unchanged.
- Session 1: two creates, impacts and destroys; 14 timing updates. Session 2 after successful same-process reload: eight creates, impacts and destroys; 57 timing updates. No unmatched/reused-live/overflow/read failures or open lifetimes/samples at either boundary.
- No invalid timing samples, overlap lifetimes, nesting-limit hits, identity-retired returns, incomplete returns or per-shot caps. All ten final summaries have pending_update=0 and blocked=0. Shared impact_callbacks=1 on each destroyed lifetime.
- All impacts_in_window=0: the logged impact notices occur after the collision observation. Collision is identified through projectile state/contact changes and correctly excluded from free-flight speed comparison. This does not exercise delivery of impact/destruction callbacks during an outstanding sampled call.
- No current-hit or damage-event contexts were required for this scenery test. Native flight and damage writes remain disabled.

## Acceptance boundaries

Accept this bounded diagnostic: movement timing and configured-speed consistency for both test weapons, sampled entry/return execution on the actual update thread, full shot lifecycles and recovery after a completed-shot reload. No crash is indicated by this capture and normal exit is recorded.

Do not extend this acceptance to concurrent same-projectile updates, sequential migration between update threads, reload with in-flight continuations, destruction during update, unusual nested calls, native flight writes, physical metre calibration, drag/gravity, VATS or actor damage/armour. Those edge paths were not exercised here. This is sufficient to stop repeating the current wall-shot diagnostic; relevant additional coverage belongs to the feature that needs it.

## Proposed next packet, awaiting approval

Prepare a bounded native gravity-and-drag pilot for these same two private profiles using the selected BallistX data and fixed atmospheric conditions. Its purpose is to make bullets drop and lose velocity in flight. Before introducing writes, verify the vector/velocity update boundary, units and ownership against the supplied engine/extender sources, preserving the existing dispatchers. If the boundary cannot be supported, report the blocker rather than enabling it. Keep unrelated weapons, damage authority and the later armour/injury work outside this packet.

Keep 304 installed and both NVO.esm and NVOFlightPilot.esp enabled. Ask before preparing/installing the next packet; no further test of unchanged 304 is requested. The reviewed log is archived, so another launch can no longer overwrite this evidence.
