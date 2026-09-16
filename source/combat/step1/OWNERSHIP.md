# Combat ownership and donor entrypoints

This is a selective-adaptation inventory. Donor archives are not an install list. No donor has been enabled, disabled, merged or deleted in packet 1.

Only **NVOCombatBootstrapQ** initializes this packet's quest controller. Do not also place its source in an NVSE scripts folder: quest source and ScriptRunner source are different entrypoints.

| Subsystem | Planned owner | Donor entrypoints to keep out of the NVO combat profile when its replacement is introduced |
|---|---|---|
| Flight and direct ballistic damage | NVOCombatCore, adapted from BallistX | BallistX.esp / BallistXMain and Physics' Based Ballistics `gr_PBBmain.txt` |
| Weapon damage classification | NVO profiles and native resolver | CBD `ln_CBDredux.txt` and `CBDMainFunction.txt` |
| Additional ammunition distribution | A later explicit NVO equipment packet | BallistXAmmo.esp, `gr_BallistXAmmo.txt`, `ln_BallistXAmmo.txt` |
| Spread | One NVO accuracy component | `ln_PhysicsBasedSpread.txt`, New Blood spread code, overlapping Transcendence changes |
| Bleeding and treatment | One NVO wound component | Simple Bleeding `ln_SimpleBleeding.txt` and its UDFs, New Blood bleeding handlers |
| Knockdown and fatigue | One NVO impact component | New Blood handlers, Transcendence `TransKnockdownPerkUDF`, inherited perk knockdowns |
| Damage resistance and anatomy | NVO hit resolver and selected NVO records | New Blood creature/body-part overrides, overlapping Transcendence records |
| Native AI fixes | CombatAITweaksNVSE.dll | Keep one copy of that DLL, without reimplementing its patches in NVOCombatCore |
| Morale and retreat | NVO scripts using resolved combat information | Future NVO actor events; no simultaneous legacy morale controller |
| Special weapon effects | Individually adapted NVO effects | SWEEP `SCPTSweepStartup`, effect scripts and ScriptRunner loader until individually ported |

Removing a donor ESP alone does not disable its loose startup scripts. Conversely, a UDF file is not proof that it runs: it needs a caller. The machine-readable inventory records entrypoint source references and file hashes so later packets can name exact conflicts. The observed empty loose startup directory does not rule out scripts inside archives or calls from an already compiled plugin.

## Specific adaptation findings

- BallistXMain independently writes projectile damage, tracks projectile timing through angles and deletes tracked projectiles after three seconds. Port the useful physics/data into owned native state; do not run that quest beside the NVO flight component.
- Caliber Based Damage changes weapon damage, projectile counts and damage-mod attachment values. Keep its data-driven classification approach without a second weapon-damage owner. Its base-game tuning uses ammunition cap value, not a physical energy formula.
- Physics' Based Ballistics edits projectile speed, gravity and flags. These overlap directly with BallistX. Its supplied speed values are gameplay tuning rather than a realistic velocity table.
- Physics' Based Spread temporarily edits a shared weapon form's minimum spread around player shots. The NVO adaptation must avoid leaking player-specific injury/proficiency adjustments to every actor using that form.
- Simple Bleeding's player-enable variable reads the stimpak setting. Its NPC-origin damage path also stops applying damage below a lethal threshold, unlike its player-origin path. Correct these while adapting it and retain original attacker attribution. Its generic timer names also need NVO-specific names.
- New Blood and Transcendence contain broad gameplay records in addition to their desirable combat features. Copying their full startup scripts would bring in extra registration, scaling and settings changes.
- The supplied Transcended Fatigue Overhaul.esp depends on SD_Fatigue.esp and Transcendence.esp. It is a patch, not a self-contained fatigue implementation.
- The supplied Vanilla SWEEP.esp lists Fallout3.esm, TaleOfTwoWastelands.esm, YUPTTW.esm and Fallout 3 DLC among its masters. Its filename does not establish standalone New Vegas compatibility. Selected features require their own dependency closure and remapped references.
- Combat AI Tweaks' supplied config has randomized melee lunge and a low-health target bonus. The later NVO AI packet will use conservative settings. JohnnyGuitar versions exposing the same combat timers must have those settings coordinated with the AI plugin.
- The current Data directory contains older `NVOCombat` UDFs and a legacy NVOCombat.log. They are not the new native project or evidence of a running new combat core. The new DLL uses the distinct name **NVOCombatCore**.

No step in this packet requires removing mods from an existing playthrough. Introduce donor replacements through a dedicated NVO testing profile at their own checkpoints, retaining the current profile and saves for reversal.
