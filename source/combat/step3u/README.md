# Packet 3U — contact-speed coverage

Purpose: provide usable, explicitly bounded speed evidence for verified bullet movement segments that the older exact-point estimator could not use. Native324 / NVO 0.3.24. **Damage replacement remains OFF. The pre-damage review remains HOLD.** No GECK changes.

## What changed

- **Close-range first-step contacts:** use the actual observed engine translation divided by its parent update timestep and the authored 70 units/metre scale. Require the movement reset observation, identity, projectile policy and endpoint/accounting checks. This is a segment mean, not an assumed muzzle velocity or retroactive drag correction.
- **Off-curve surface contacts:** retain a speed interval for the whole verified NVO movement step. The surface point cannot select a false exact time/speed. The old point tolerance, point estimator and admission results are unchanged.
- **Post-collision terrain correction:** a read-only snapshot at the existing terrain hook records the contact and proposed endpoint before the engine may raise Z. A later mismatch can be explained only by that snapshot, the same contact, the strict greater-than-30-unit rule and matching final Z/accounting. A vertical mismatch alone proves nothing. The clamp itself is preserved.
- The existing hit observer receives the range only when projectile/lifetime/source/weapon/ammo/target and contact still match. No new damage API or hook was added.

The normal capacity probe remains off. Logs remain bounded: 32 collision lifetimes, 64 hit queries; no extra console chatter. Source and configuration remain modular. Laser, plasma, flame, explosive and thrown-weapon rules are still separate work.

## Evidence and limits

The actual C++ diagnostic/cache/join code was replayed offline against 21 contacts from three pinned historical logs. Eighteen now supply segment-speed evidence, including three first-step actor contacts. The previous four exact-point candidates remain exactly four; these are different evidence categories.

One old SMG contact lacks a logged per-step reset observation. A separately labelled prospective replay supplies that new observation and succeeds, but is not historical proof. Two other historical contacts retain `movement_unverified`: their final Z changes by about 887 and 54 units. They are consistent with a terrain correction, but the old logs did not capture the required pre-clamp snapshot. The new live observation must establish it; neither old contact was silently accepted.

Focused failure checks cover missing/nonfinite inputs, unsupported flags, altered movement/velocity, repeated terrain samples, identity/contact changes, callback ordering, reload and cache capacity. A separate fine-step numerical trajectory checks the speed intervals over 384 combinations of drag profile, density, timestep, BC and direction, including an interior apex. These are offline checks, not thousands of game tests or a formal numerical-error proof.

**Still unknown:** instantaneous physical contact time; why every surface point is offset from the centre-flight curve; contacts before any usable movement sample. The last category stays unavailable. The new interval is conditional on contact belonging to the verified step, not a proof of its exact point on that step. No energy/armour consumer can treat it as an authoritative scalar. The offline Packet3S energy contract is unchanged and does not silently accept these new producer kinds.

## Your short checkpoint

After the assistant confirms installation, start the game normally. Keep NVO.esm and the existing NVOFlightPilot.esp active. No GECK compile, new game or new test kit is required. The existing `bat NVOFlightKit3F` supplies ordinary test weapons if needed; use standard ammunition.

1. Fire one ordinary 9mm pistol shot into a living target at close range. Aim normally so a VATS miss does not obscure the close-range case.
2. Fire one hunting-rifle shot into distant sloping ground/terrain.
3. Fire one hunting-rifle VATS torso shot at a living target. Note whether it visibly hits or misses; either is useful evidence.
4. Reload your save once, then fire one 9mm pistol shot at a nearby wall. Wait a few seconds and quit normally.

God mode for ammunition is fine for this observer check. Do not repeat a long stress test or try to force the old rare terrain error. Reply **finished** with any shot that missed or behaved oddly. The assistant will read the existing game-root NVOCombatCore.log directly. If a contact has no movement sample, that is an explicit coverage limit, not an invitation to keep firing indefinitely.

Expected: one NVO [0.3.24] startup banner, no new popup; normal combat behaviour; new `IMPACT_SPEED`, `IMPACT_TERRAIN` and `IMPACT_HIT_SPEED` rows with damage replacement 0. Close-range eligible contacts report `observed_engine_segment`; applied-flight contacts report `owned_step_speed_range`. `explained_clamp=1` is accepted only with the new proof. A test without a terrain clamp does not validate that branch.

## Reversal

Only NVOCombatCore.dll and its matching PDB are replaced. INSTALL-3U-result.json records the verified backup of the normal native323 pair. Close New Vegas and restore those two files together from that backup, or ask the assistant to do it. No ESM, ESP, save, INI or load-order rollback is required. Do not use the older 3R1 installation backup: that contains the diagnostic capacity-probe build.

Next: review this checkpoint, then ask before continuing. Do not enable damage until the exact damage boundary, application/ownership, contact producer and remaining Ultra317 findings are resolved.
