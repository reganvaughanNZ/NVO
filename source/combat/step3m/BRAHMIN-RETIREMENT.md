# Brahmin Baron — retire the caps damage ability

User decision, 2026-09-16: remove the ability and choose a replacement later. Do not port caps-based damage, damage taken or instant kills into the new damage system. This is an approved design disposition; the installed compiled records are **not yet changed** by this contract packet.

## Actual existing behaviour

`ALTRichKidHit` takes target/attacker, computes `floor(player caps * 0.001)`, then directly calls `target.DamageAV health` or `target.Kill attacker`. `ALTBackRichKidUDF` registers it twice for OnHit, filtered for player victim and player attacker. `ALTQscript` repeats the registrations for background53 on game restart/load. Removing only one registration site would leave a route back to the ability.

The current record inventory and complete source text are in `CURRENT-BARON-RECORDS.json`, extracted from installed NVO.esm. The exact source and compiled-subrecord hashes should be rechecked when preparing the retirement, because the user may save GECK edits between packets.

## Bounded removal for the next implementation packet

1. Preserve original record identities. Do not create new duplicate scripts or delete the function record while older saves/handlers may still reference it.
2. Replace the original callback with a harmless function preserving its two reference arguments and existing declared variables. This protects already-registered callbacks, even before unregistering them. No health write, kill or replacement perk is added.
3. Remove both OnHit registrations from the original background UDF and original ALTQscript, preserving unrelated startup/load registrations and all existing variable indices/types.
4. Add a safe, one-time-per-loaded-session retirement of the two known registrations using the installed extender's verified removal interface. If this is unavailable, the inert callback is the safety mechanism; document residual no-op registration rather than falsely claiming all handlers were removed. Do not unregister other OnHit handlers.
5. Update every actual description/preview mentioning the caps ability, keeping the wealthy start, 5,000-cap grant, wealth setting, outfit/weapon/location and unrelated dialogue intact. Do not implement an unchosen replacement.
6. User compiles the **original** scripts and saves NVO.esm. Read back compiled/source records and validate no DamageAV/Kill remains in the retired function and no registration can restore it. A file of source text alone is not runtime removal.

The packet must provide full scripts with copy buttons and exact original Editor IDs, plus an ESM backup and reversal instructions. No fragile line-number edits. Runtime cleanup must be repeat-safe after reload; a test save must not re-enable the effect. Do not flag finding317-02 closed until the installed compiled records and relevant saved-session path have been checked.

## Later background pass

Review all starts together after the combat and medicine rules are sufficiently settled. Each gets a consistent description, coherent inventory, faction relations, proficiency, useful non-stacking mechanics and clear challenge level. Keep permanent identity consequences such as exile/outlaw status where intended. Courier work remains optional, accessed through the Mojave Express flier. Powerful starts should gain equipment/experience advantages without disabling vulnerable body regions or hidden damage multipliers.

For the Baron, consider a trade/contact/contract benefit later; no selection is made here. Background revisions are separate from this combat packet and do not authorize importing additional donor systems now.
