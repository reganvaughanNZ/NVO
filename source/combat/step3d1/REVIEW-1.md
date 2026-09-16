# Packet 3D1 / native build 311 - checkpoint accepted

Reviewed 2026-09-15. **Accept the corrected SMG and the outstanding regular-rifle flight/reload checkpoint.** The user explicitly identifies the final shot as VATS. No repeat of this test is needed.

## Archived evidence

[NVOCombatCore.log](captures/2026-09-15-3D1-f193402750e4/NVOCombatCore.log): 384,331 bytes, 1,646 lines; last write 2026-09-15 17:46:19 +12. SHA256 `f193402750e45853f534b1ed484d617614fb52bc3dfb2c18f9be9a325220df6c`.

[review-data.json](captures/2026-09-15-3D1-f193402750e4/review-data.json) contains the per-step comparisons, shot summaries and linked final hit. Two loaded sessions, one reload, nine projectile lifetimes and normal exit.

## Results

| Regular weapon | Shots | Verified edited free-flight segments |
|---|---:|---:|
| 9mm Pistol | 1 | 13 |
| 9mm Submachine Gun | 4 | 69 |
| Hunting Rifle | 1 | 7 |
| Service Rifle | 3 | 13 |
| Total | 9 | 102 |

Every selection is corroborated by actual creation with the expected private projectile base, weapon, source and equipped ammunition. There are no selection or preview fallbacks. All four SMG shots use the corrected original `0017A2C6` and private replacement `0C000808`. Three projectiles coexist during the burst, with clean retirement and no live-address reuse.

All nine unchanged initial segments verified. All 120 controller calls are paired with returns, local-Z handling and movement accounting. There are 111 edited segments: 102 verified free-flight segments and nine collision-ending segments excluded from free-flight acceptance. Every shot has at least one verified edited segment before impact.

Maximum logged edited-vector error: 0.00682887815 game units. Largest error/tolerance fraction: 0.1618737224, comfortably inside the existing tolerance. Two baseline observations have a small nonzero position error of 0.00000762939453 game units; this also passes the existing position tolerance. Exact zero is not required by the native contract. No native tolerance was changed during review.

The maximum difference between intended movement and the logged pre-contact position candidate is 0.00746826962 game units. This capture does not reproduce the earlier large collision-boundary Z discrepancy, but it does not establish its cause or justify removing the existing contact-energy limitation.

## Final VATS shot and reload

Session 2 contains two Service Rifle shots. The final one is lifetime 9, matching the user's VATS report. It has a verified baseline and one verified edited free-flight segment, followed by collision with live actor `FF001992`.

The linked hit context identifies the player, Service Rifle `000E9C3B`, standard 5.56 ammunition `00004240`, carrier `FF001993`, lifetime 9, and reported body region 0. The capture includes one pre-hit and one pre-health callback for that encounter. The log has no explicit VATS-mode field; VATS context comes from the user. This completes the requested limited live-target/VATS check without claiming general VATS coverage.

The hit-context damage value and later pre-health delta belong to different engine stages. They do not establish final health loss or damage duplication. NVO damage replacement stayed disabled throughout.

## Lifecycle and scope

No logged guard rejection, displacement mismatch, unmatched lifetime, read failure, overflow, unpaired accounting, detail cap or pending/open tracking state at reload or exit. The selector is ready and bound on both loads. Session 1 has four movement and four accounting calls outside tracked lifetimes; their identities are not logged, and they are not assigned to a particular projectile in this review. The corresponding unpaired counter remains zero, and all nine tracked lifetimes are fully accounted for.

Accept the limited four-weapon, standard-ammunition expansion together with the prior 3D pistol evidence. Keep 3D1 installed. Precise contact-time velocity/energy, engine-unit calibration, additional ammunition, shotguns, energy weapons and damage/armour authority remain separate work. The existing initial unchanged flight segment remains a pilot limitation.

No native source, game files or release packages were changed during this review. Ask before the next packet. A proposed small next batch is standard-ammunition profiles for the 10mm Pistol, .357 Magnum Revolver and .44 Magnum Revolver, with a matching kit; audit the donor rows and actual source projectiles before implementing that expansion.
