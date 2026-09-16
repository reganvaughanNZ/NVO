# Packet 3D / build 311 - user playtest review

Reviewed 2026-09-15. **Partial acceptance: correct the SMG source mapping before another test.** The first load is setup, as the user specified. Session 2 is the main test; session 3 is the reload check. No game files, native code or release packages were changed during this review.

## Evidence

Archived capture: [NVOCombatCore.log](captures/2026-09-15-3D-489fa598bd90/NVOCombatCore.log), 62,315 bytes, 301 lines, last write 2026-09-15 17:02:15 +12. SHA256 `489fa598bd90b87bd8cfe285f980e7bc3bbcea56dee0661b9a047b1da11a1c90`.

Machine-readable results: [review-data.json](captures/2026-09-15-3D-489fa598bd90/review-data.json). Independent base-game record and donor audit: [source-mapping-audit.json](captures/2026-09-15-3D-489fa598bd90/source-mapping-audit.json).

## Results

| Check | Observed result |
|---|---|
| Startup and reload | Selector ready and event bound on all three loads; normal exit. |
| Regular 9mm Pistol | Correct original-to-private projectile selection, actual creation and equipped ammunition confirmed. One edited free-flight segment matched; baseline also matched. |
| Regular Hunting Rifle | Correct selection and creation; baseline matched. Its edited segment ended in collision, so no edited free-flight match in this capture. |
| Regular Service Rifle | Correct selection and creation both before and after reload. First shot collided during the unchanged initial segment. After reload, baseline matched but the edited segment ended in collision. |
| Regular 9mm SMG | Four shots retained the original projectile because our configured original projectile is wrong. All four overlapping lifetimes were observed and retired cleanly; NVO SMG flight remains untested. |
| Tracking and cleanup | No logged mismatch, rejection, read failure, unmatched event, active-address reuse, overflow, unpaired accounting, open lifetime or pending controller state at summaries. |
| Actor/VATS evidence | No direct VATS-mode field in this log and no actor hit/health contexts. The final impact was scenery, so it does not establish the requested live-target hit checkpoint. |

Four successful selections were independently matched to actual created projectile bases and actual ammunition: pistol once, hunting rifle once, service rifle twice. Their load-order prefix in this capture was `0C`; configuration continues to resolve plugin/local IDs dynamically.

The pistol's edited displacement error was 0.00761893413 game units, within tolerance 0.0433998451, with zero position error. The other edited observations ended at collision boundaries and are excluded from free-flight acceptance. Previous build 310 private-rifle regression remains accepted; this capture does not supersede those results or validate exact contact velocity/energy.

Session 2 has seven create/impact/destroy lifetimes; session 3 has one. Setup has one earlier private-rifle lifetime, excluded from the regular-weapon checkpoint. Session 2's 48 untracked movement/accounting entries belong to the original SMG fallback. `lives_without_update=1` in setup and session 2 corresponds to immediate collision during the initial segment. These counters do not indicate an unpaired call or a hook failure.

The common impact reference `001055E0` resolves in the base game to static `NVProspectorSaloon` (`0010243E`), including the final reload shot. This identifies the recorded collision, not whether the user attempted VATS or aimed at an actor behind it. No claim of a completed actor/VATS hit check is justified by this log alone.

Damage replacement remained disabled throughout.

## Confirmed preparation error and proposed correction

The error is in our packet preparation, not the user's testing. `prepare_combat_3d.py` chose pistol projectile `FalloutNV.esm:08F20F` as the 9mm SMG source. The base game's `WeapNV9mmSubmachineGun` (`0008F217`) actually references `FalloutNV.esm:17A2C6`, `AutoTracerProjectile`. The live log independently confirms that original projectile on all four SMG shots. The runtime's exact-match guard correctly preserved it.

The two originals also differ in model and in DATA properties beyond gravity/speed. Consequently, changing the INI alone is insufficient: the private SMG projectile must be regenerated from the actual original to preserve the appropriate model, flags and remaining properties. The existing loader compares the source and private clone; keep that protection.

The inspected BallistX CartridgeData has a standard 9mm row keyed by `08F20F`, but no row for `17A2C6`. Use the 9mm row for cartridge tuning while separately using `17A2C6` for engine source matching and cloning. Add a preparation check that each configured original projectile agrees with its weapon's DNAM projectile reference. Keep donor cartridge keys distinct from engine projectile identities.

Proposed next packet **3D1**: correct this mapping and regenerate the SMG clone, audit the four weapon/source relationships, then deliver a short follow-up covering the corrected SMG burst and longer-distance rifle flight. Preserve the pistol pass. Carry the unconfirmed live-target Service Rifle/VATS evidence forward explicitly. Do not broaden to additional weapons or damage authority.

Await user approval before preparing/installing the next packet. Keep the currently installed 311 artifacts and immutable installation receipts intact until then. No repeat test of the known-bad SMG profile is useful.
