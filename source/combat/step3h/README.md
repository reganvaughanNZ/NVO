# Packet 3H: hit entry and return diagnostics

Native version **318 / 0.3.18**. Purpose: observe a complete hit input before ITR's damage event, then follow that synchronous call through existing events and its return. Damage replacement is disabled. No GECK work is required.

Follow **START-HERE.html** for the three-hit check. Use the existing Hunting Rifle/standard .308 kit. One save reload checks the new call-scope lifecycle; the last hit uses fists. No long-distance misses or stress test is required.

New log rows in the game-root **NVOCombatCore.log** begin `HIT_TX`. A successful hook guard emits `HIT_TX_HOOK_READY`; each loaded capture emits `HIT_TX_READY`. `HIT_TX_BEGIN` carries the source, target, weapon, carrier, creation-ammunition/lifetime match and a unique transaction ID. `HIT_TX_STAGE` distinguishes ITR pre-hit, copy input and ITR pre-health. `HIT_TX_RETURN` acknowledges the original provider returning, **not committed health loss**. Readiness requires the user's live log review; compilation alone does not establish it.

The guarded observer wraps six existing ITR calls. The installed ITR DLL and its behavior are retained. Native flight, tolerance, profiles and records are unchanged. Required NVO.esm, NVOFlightPilot.esp and their masters remain enabled. RD/startup record repairs are a separate packet.

See Installation/CONTRACT.md and Installation/IMPLEMENTATION.md for scope, limitations and reversal. The completed Ultra foundation review remains the baseline; this packet addresses its first interface finding with diagnostics. It does not close the damage gate or rerun the full audit.
