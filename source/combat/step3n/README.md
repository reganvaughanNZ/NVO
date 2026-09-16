# Packet 3N — disabled calculator and Baron retirement sources

The standalone C++ armour model compiled with MSVC x86, C++17, /W4 /WX and passed45 offline checks. It also exercised4000 seeded conservation/condition cases and10000 repeated previews. No production DLL was rebuilt or installed. Native320, flight settings, user health GMSTs and difficulty remain unchanged.

## What was implemented

`native/NVOCombatModel` is an isolated pure calculation module with no NVSE hooks, engine mutation API, logging or runtime configuration reader. It validates typed measurements and verified context, separates head/body coverage, supports layers/condition, distinguishes authored Ball/AP/HP/Pellet resistance, and calculates bounded transmitted blunt energy, HP/limb previews and per-instance wear. Laser, plasma, timed flame and blast select distinct dose responses. Mechanical targets cannot receive biological wound/payload eligibility. Missing/nonfinite/mixed-unit/overflow inputs reject the entire preview without partial output.

All fixture numbers are synthetic. The current stopping-energy thresholds and linear condition/shield rules are an authored approximation, not validated armour simulation or final game balance. No actual laser/plasma energy data, incidence model, ongoing burn/bleed effects or gameplay application exists in this module. The tests do not prove runtime projectile adapters, live VATS behaviour, deduplication or saved injuries. Those gates remain open. The installed flight system still only changes its explicit bullet pilot profiles; other weapons retain engine behaviour.

## What you compile in GECK

Open START-HERE.html for one-click copies and exact instructions. Four original scripts:

1. `ALTRichKidHit`: harmless return, keeping old parameter and variable declarations for saved references.
2. `ALTBackRichKidUDF`: unregister only this retired callback instead of registering it; preserve wealth, 5000 caps, gear, dialogue and spawn behaviour.
3. `ALTQscript`: remove the background53 registrations; unregister the retired callback in the existing GetGameLoaded branch after the NVSE version check. This runs for any background, so a changed/saved background cannot retain the effect. No new state variable or broad event removal.
4. `NVOStartPreview`: remove only the old caps/damage claim from the Baron preview.

Also update `ALTRichKid` message description using the supplied text. Do not change its Editor ID/title. Do not create duplicate scripts, new quests or delete the old callback record.

`RemoveEventHandler "OnHit" ALTRichKidHit` is verified against supplied xNVSE command declarations/implementation. The callback identity must match; with no filters it removes this callback's OnHit registrations across filters/priorities, not other callbacks. Repeated removal with no handler is harmless in the inspected implementation. We deliberately do not invent a RemoveEventHandlerAlt command. A compiled harmless callback remains the safety mechanism until old registrations are cleared. Source verification is not a claim that your GECK compilation has already succeeded.

Current exact source was extracted from installed NVO.esm, including the existing reserved declarations. No other background logic was rewritten. The source audit records original compiled hashes and variable indices/types. After SAVED, `tools/review_saved_combat_3n.py` checks the user's actual file for original identities, matching source, changed compiled bytes, preserved variables, description, master/health settings and unexpected changes. It does not decompile bytecode or independently prove game execution.

## Checkpoint and reversal

Compile/save the four originals and edit the one message, save NVO.esm, close GECK, then reply SAVED. No combat playtest yet. The assistant will read the file directly and stop if GECK created duplicates or changed referenced variable slots. A compact runtime retirement check can follow that review; do not mark the Baron ability removed until the actual compiled records have been verified.

The pre-edit ESM is backed up at `source/combat/step3n/baseline/NVO.esm`, with a hash in PACKET-RESULT.json. To reverse this packet's GECK edits, close GECK/New Vegas and restore that backup to Data/NVO.esm **only if you have made no other edits since it**. Otherwise ask for a selective reversal. No DLL/config rollback is necessary. The packet does not change save files; no replacement Baron benefit is chosen yet.

Broader start consistency remains queued for the later background pass. The next combat task stays within the established gates: supported inputs/contact/region, admission before substitution, one application owner, and targeted review before separately authorized activation. Do not start another packet before this saved-record checkpoint.
