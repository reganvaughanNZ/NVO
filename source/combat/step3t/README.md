# Packet 3T — distance and projectile-clock audit

Purpose: settle which distance convention and timestep NVO should use before contact energy reaches armour. This is an offline audit with executable checks, using existing source and recorded tests. No DLL, ESM, INI or game setting was changed. Normal native323 / NVO 0.3.23 remains installed, damage replacement OFF, Ultra gate HOLD.

## Decision

Keep **70 engine units per NVO simulation metre** as the explicit authored world scale. Use the **incoming BulletProjectile update timestep once**. The inspected parent code handles its VATS adjustment before passing this argument onward. A later Turbo-related movement adjustment must not be used as the denominator for the displacement already built with the original argument. No new speed or difficulty multiplier is justified.

This confirms the current clock choice and conversion consistency. It does not turn the game's environment into a physically measured world, certify every VATS branch in the installed process, or establish instantaneous contact speed.

## Evidence

- Four immutable captures: the earlier 3B3A VATS test, 3G2, 3Q and 3R.
- **455 paired physics/engine updates:** identical parent timestep in every pair.
- **475 consecutive lifetime pairs:** the next observed lifetime exactly matches a float32 addition of the preceding engine timestep. The lifetime increment occurs after the observed virtual update returns, explaining why before/after lifetime inside that call is unchanged.
- **29 baseline movement conversions:** displacement, timestep and the authored scale round-trip to the logged initial speed. Maximum relative discrepancy is about 3.7e-9 from text rounding.
- **427 applied movement steps:** the actual unchanged C++ integrator reproduces logged final speed and displacement. Maximum discrepancy is under 0.000001 m/s for speed and 0.000008 engine units for displacement.
- Eight alternate timestep partitions across the two donor drag profiles agree within 0.001 metre and 0.001 m/s at the same total simulated time. Analytic gravity-only checks and a deliberately wrong-clock example also pass.

The compiled x86 harness uses /W4 /WX and passed all assertions: four per replayed step plus 33 additional numerical assertions. This is not 1,741 separate gameplay tests. Log-rounding and partition budgets are offline comparison tolerances; no contact-geometry tolerance was relaxed.

## Limits kept visible

One 3Q physics row has no matching timing-return row because the independent timing observer reached its 64-row limit. It stays unpaired in RESULT.json. No observation is invented to cover it.

The captures do not log per-update VATS mode or global time factor. 3B3A's VATS label and 3Q shot 7 come from the user's test description. The known 3Q VATS shot contacts during the unchanged first movement segment, so it does not prove integrated VATS flight. Every observed later movement timestep equals the parent timestep; actual Turbo clock divergence is not claimed from these captures. The clock-divergence check is synthetic.

The parent clock branch was inspected in a previously captured, hash-verified decoded engine snapshot. It was not freshly read from a running process. Existing native guards cover the movement wrapper and missile update, but do not independently fingerprint the whole upstream parent/VATS clock body. Preserve that compatibility requirement for the eventual damage admission path.

## Your action

**None for this packet.** No GECK compilation, installation, console command, recording or repeat firing test. The assistant did not launch or close the game. There is no game rollback because no installed files changed.

## Next packet, after approval

Resolve contact-speed coverage: first-segment/close-range contacts and cases where the reported collision point does not fit the current path model. Use existing captures first. Do not substitute muzzle speed or widen geometric tolerance merely to create accepted hits. Once that producer is reliable, return to armour inputs and the authoritative damage/application review. Energy weapons, blast, flames and thrown weapons still need their own rules.

Technical details: CONTRACT.md. Reproducible evidence: RESULT.json, REPLAY-ROWS.json and the per-capture PAIRS files. Workspace audit command: configured Python running tools/audit_combat_3t.py. Runtime engine snapshots remain local and are not included in the release.
