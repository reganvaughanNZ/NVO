# Pending health diagnosis

User handoff: the user has chosen to handle health through game settings and asked the assistant to continue. Further health diagnosis is paused by that instruction. No health fix is claimed or applied by the assistant.

User report: **Mercenary background, Endurance 7, displayed health 596**. Starting/current level and base health are not yet known. Asked for `player.getlevel` and `player.getbaseav health`. No health values have been changed.

The screenshots show category menus displaying, a name-entry prompt and the character reaching gameplay. A still of a black Pip-Boy screen cannot establish whether the display remains blank or was captured during its animation. The full HP bar alone does not show its numeric value; 596 comes from the user's report.

Read-only findings from the installed plugins:

- ALTBackMercenaryUDF gives metal armour, the preorder grenade rifle and ten 40mm grenades, plus a spawn marker, wealth category and dialogue wording. It contains no direct health increase.
- The scanned NVO script sources contain no direct player health increase associated with this start. The generic start routine resets/restores health; the pilot start damages health. This does not rule out all effects, perks or saved-state modifiers.
- No matching health-scaling GMST override was found in the installed NVO.esm.
- The installed FalloutNV.esm player base record has health 100. The base-game GMST values read are fAVDHealthEnduranceMult = 20, fAVDHealthEnduranceOffset = 0 and fAVDHealthLevelMult = 5. These are source-record values, not measurements of current runtime actor values.
- ALTLevelQscript advances the player until the chosen start level is reached. The user's actual resulting level must be checked before attributing health solely to the background.
- NVOCombatBootstrapScript does not modify health, and the inspected installed NVO.esm does not yet contain its script/quest records.

596 is not explained by the Mercenary equipment script alone. Do not force a lower health value to mask the unknown cause. Compare the reported level, base health and current health first, then inspect relevant modifiers or runtime settings only if necessary.

The broader combat health/balance changes are still planned. Packet 1 and this dependency repair do not implement them.
