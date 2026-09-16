# Packet 3B2 review — 15 September 2026

**Accept physical travel, identity matching and reload continuation. Exact speed calibration remains unresolved.** Keep 302 installed. No repeated test of the same setup is needed now.

Read the latest game-root log directly. Stable during reading, 15636 bytes, modified 2026-09-15T10:08:46.022843 local, normal exit recorded. SHA256 `135b1dd786ea48a5f96720fcb4246b65481e81b7068fd73fc8dbb00c56a2e105`. Archived at `captures/2026-09-15-3B2-135b1dd786ea/NVOCombatCore.log`, with parsed evidence in analysis.json.

The log matches the user's report: two shots with each pilot weapon before reload, then one with each after reload/wait. All six impact events report target reference 001760D6. This confirms reference identity, not exact hit point, range or object type. VATS and god-mode state are not explicitly logged.

## Confirmed

Version 302, four profiles, kit ready on both loads. Six player projectiles have the intended weapon/ammo/projectile-base identities, each with one creation, impact and destruction. Reused projectile IDs remain distinct by lifetime serial. Event sequences are continuous. Both summaries report zero unmatched lifetimes, live-address reuse, overflow, read failures and open lifetimes. Preview summaries report zero skips, read/identity failures and open samples. Reload re-resolves profiles and captures both weapons again.

All private projectiles report hitscan=0, gravity_setting=0, speed_multiplier=1, and expected speed settings: 27097.6 units/s for 9mm and 59484 units/s for .308. Twelve valid travel rows represent six independent shots: impact and destruction repeat the same terminal counters for each.

## Calibration remains open

| Capture / shot | Profile | Lifetime ms | Distance units | Mean / configured speed | Counter time excess ms |
|---|---|---:|---:|---:|---:|
| 1 / 1 | pilot-9mm | 125 | 2953.64 | 87.20% | 16.000 |
| 1 / 2 | pilot-9mm | 141 | 2980.74 | 78.01% | 31.000 |
| 1 / 3 | pilot-308 | 78 | 3747.49 | 80.77% | 15.000 |
| 1 / 4 | pilot-308 | 78 | 3688.00 | 79.49% | 16.000 |
| 2 / 5 | pilot-9mm | 125 | 2953.64 | 87.20% | 16.000 |
| 2 / 6 | pilot-308 | 63 | 2795.75 | 74.60% | 16.000 |

Counter time excess is logged lifetime minus distance/configured speed, calculated from rounded log values. Five shots show approximately 15–16 ms extra, one 31 ms. This is consistent with a possible movement/impact sampling phase difference, but does not establish its cause. Do not interpret the lower averages as proof that the bullets really move 13–25% too slowly, and do not increase speed to compensate.

The means are valid ratios of engine counters, not verified instantaneous velocity or muzzle-speed measurements. Intermediate movement/timestep data is absent. The next task should first inspect counter updates and determine whether aligned movement/time observation is needed before adding drag. The independent 70 units/metre convention remains unverified; the table uses engine units.

No copy-hit or ITR damage callbacks were emitted. This surface-capable flight check does not establish actor damage; zero contexts are not evidence of a regression. The narrow loaded-name/loose-loader audit is clear with its previous BSA/execution limits. Native flight and damage writes remain off; isolated PROJ records provide the movement. No drag, native gravity, damage authority or injury claims follow from this capture.

No gameplay test, code edit, build or installation occurred during this review. Ask before continuing with the timing investigation; decide whether another small diagnostic packet is necessary after reading the relevant engine/provider code. Avoid repeating the same test without improved measurement.

Workflow: when the user reports a completed test, read and archive the current log directly from the known game directory. Ask for an attachment only if direct access fails or another file is needed.
