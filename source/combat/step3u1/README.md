# Packet 3U1 — anonymous world-contact classification

Purpose: fix Packet3U's rejection of valid terrain/world contacts without weakening actor identity checks. Native325 / NVO0.3.25. Damage replacement remains OFF; Ultra317 remains HOLD. No GECK, ESM, ESP, INI, weapon or ammunition change.

## Change

Collision targets now have one of three internal meanings:

- `Invalid`: target data could not establish a supported identity. This includes a nonnull form pointer with form ID zero.
- `World`: the collision entry and all geometry fields read successfully, while the raw target pointer itself is null, the stored form ID is zero and body region is -1.
- `Reference`: a nonnull readable target form with a nonzero form ID.

World classification comes from the raw target pointer, not from target ID zero by itself. `CurrentHit::ReadForm` remains unchanged. Actor hit pairing requires Reference classification, a nonzero hit target, and the existing lifetime/projectile/source/weapon/ammo/target/point checks. Target kind also must remain unchanged through collision, terrain proof and callback. The VATS torso/left-arm disagreement remains visible and is not remapped.

No hook, allocation, world scan or movement write was added. Existing caps remain 32 retained collision lifetimes and 64 hit queries. Point tolerance, flight equations, terrain threshold and supported projectile flags are unchanged.

## Evidence before installation

The reader harness compiles the actual `ReadImpact` function. It verifies complete null-target geometry becomes World; readable nonnull/nonzero becomes Reference; readable nonnull/zero becomes Invalid; unread pointer/form/geometry and missing contact head remain unavailable. It does not load the DLL or game.

The completed six-shot3U recording is replayed first. Because that old log did not record raw pointer presence, its three zero-ID contacts deliberately remain ambiguous/unavailable. A separately labelled prospective null-pointer fixture using the same recorded movement and terrain values makes all three world contacts available and explains exactly the two recorded terrain clamps. This predicts the fix; it is not a claim that native325 has already read those pointers in-game.

The broader contact-speed replay retains its numerical, cache, reload, callback and identity checks. World contacts cannot pair to actor hit queries. Nonnull zero-ID forms, target-kind changes and terrain-kind changes are rejected.

## Short live checkpoint

After installation, keep NVO.esm and NVOFlightPilot.esp active. No GECK work or new game is needed. Standard ammunition only; `bat NVOFlightKit3F` remains available if required.

1. Fire one 9mm pistol shot at distant sloping ground.
2. Fire one 9mm pistol shot at another distant patch of sloping ground.
3. Fire one close 9mm pistol shot into a living target, aimed normally.
4. Reload the save once, fire one 9mm pistol shot at a nearby wall, wait a few seconds, and quit normally.

Reply **finished** and note a miss or anything unusual. No video, stress test, VATS shot or attempt to force a terrain clamp is required. The assistant will read the existing game-root log directly.

Expected: world contacts report `target_kind=1`; reference/actor contacts report `target_kind=2`. World contacts can report `owned_step_speed_range`, including `explained_clamp=1` only if the same pre-clamp terrain proof matches. Actor hits remain paired only to Reference. One startup banner per process, no new popup, damage replacement0.

## Limits and reversal

Historical zero-ID contacts remain ambiguous; only the new log can validate the raw-pointer classifier. A run without a terrain clamp validates world classification but not the clamp branch. Exact contact time, precise point association, VATS body-region authority and contacts before a usable movement sample remain unresolved.

Only NVOCombatCore.dll and its matching PDB are replaced. The install transaction records a verified native324 backup. Restore both files together from that backup with New Vegas closed, or ask the assistant. Saves, records, scripts, load order and configurations need no rollback.

Next: review the live checkpoint, then ask before continuing. Do not activate damage from this packet.
