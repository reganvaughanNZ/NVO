# Packet 3B1 flight-preview review - 15 September 2026

Result: **accept the pilot-matching and profile/cache reload checkpoint**. Both pilot combinations match their live weapon, ammo and projectile identities. New matched projectiles are captured after both same-process reloads. Keep version 301 installed; no repeat of this check or corrective installation is needed.

## Evidence

Archived log: `captures/2026-09-15-3B1-47c325b5c29b/NVOCombatCore.log`.

SHA256: `47c325b5c29b19a7a008f19119a99c8a3d5e40c2c3e6a741da731c32a7c3e144`.

Original timestamp: 15 September 2026, 09:34:08 local. Size: 21,461 bytes. File size and modification time were stable while reading. The adjacent analysis.json preserves parsed rows, summaries, the user's note and review checks.

User report: “I fired the weapons and reloaded the game then reloaded.” The log records one initial successful load, two additional successful loads within the same process, and an ordinary exit marker. VATS and god-mode state are not recorded; they are not inferred from this note.

| Capture | 9mm Pistol / standard 9mm | Hunting Rifle / standard .308 | Matched projectiles |
|---|---:|---:|---:|
| Initial load | 2 | 0 | 2 |
| First reload | 1 | 2 | 3 |
| Second reload | 3 | 2 | 5 |
| Total | 6 | 4 | 10 |

Each of the ten projectile creations has a matching impact and destruction. Every preview agrees with the creation's source, weapon, ammo and lifetime serial, and with the intended projectile-base ID. All sources are the player. Provider sequences are consecutive within each capture; the shared projectile refID is safely distinguished by separate lifetime serials. No capture reaches a text/sample limit.

All three preview summaries report zero skips, read failures, identity mismatches and open samples. The general observer also reports zero unmatched lifetimes, live-address reuse, overflow, read failures and outstanding lifetimes. Both profiles resolve again after each reload and new previews follow, supporting the new configuration/cache lifecycle. There are no disabled-preview or invalid-input rows.

## Speed information and its limits

| Profile | Current speed setting (engine units/s) | Setting divided by donor scale 70 (m/s, assumption) | Donor muzzle-speed preview (m/s) |
|---|---:|---:|---:|
| 9mm Pistol | 23,680 | 338.286 | 387.109 |
| Hunting Rifle | 53,000 | 757.143 | 849.771 |

Speed multiplier is 1 for all ten projectiles. The setting-derived products and donor barrel-formula previews agree with the selected source data within logged rounding. These are diagnostic settings/calculations; no proposed speed was applied and no physical-unit calibration is established.

Both projectile bases report `hitscan=1` (9mm base flags 0089; .308 flags 028D). Accordingly, all twenty impact/destruction travel samples report `mean_speed_valid=0` and the documented -1 unavailable sentinel. Some distance/lifetime counters are nonzero, but the reader deliberately does not promote hitscan counters to physical flight measurements. This is expected behaviour for the current preview, not a failure to match profiles or a reason to repeat the same test.

Raw gravity settings are 3 for the 9mm projectile and 0.3 for the .308 projectile. They are not demonstrated physical accelerations. Hitscan, time/unit conversion, vector semantics and flight ownership must be addressed before physical flight is enabled. Current speed-setting differences from donor previews do not establish a balance error.

There are no copy-hit, pre-hit or pre-health rows in this capture. The requested check allowed walls/ground, so actor damage was not required. The log does not establish damage behaviour or prove the exact objects aimed at. Earlier accepted hit-observer evidence is retained separately; no missing-hit regression is inferred here.

## Ownership and scope

All three narrow audits report no loaded BallistX.esp/BallistXAmmo.esp and no known loose PBB/CBD loader at the inspected paths. This is limited evidence about loaded names and loose-file presence, not proof of exclusive ownership, BSA contents or execution of every potential modifier. The next write-capable pilot must complete the relevant ownership audit and avoid editing shared projectile forms in a way that changes unprofiled combinations.

All relevant rows retain `flight_writes=0`, `damage_writes=0` or `damage_replacement=0`. The installed build has no NVO flight integrator or damage authority. This acceptance covers matching, bounded lifecycle tracking, correct preview arithmetic and honest unavailable-measurement reporting. Unknown-profile fallback, malformed configuration and non-hitscan travel were not exercised by this log; no blanket runtime coverage claim is made.

## Next bounded step, after confirmation

Prepare a controlled physical-flight pilot for the same two weapon/ammo combinations. Its purpose is to establish measurable travel with a verified speed/time/unit path before adding the full gravity/drag model. First inspect the creation/ownership path and isolate the pilot from other weapons sharing base records. Keep NVO damage replacement disabled, provide reversal instructions and use a small user checkpoint. Do not enable broad flight changes or proceed to armour/injuries based on this preview alone.

This review changed only workspace evidence and documentation. No game files, native code, configuration or saves were changed; no build, game launch, GECK work or assistant gameplay tests were performed. The user has not yet confirmed preparation of the next packet.
