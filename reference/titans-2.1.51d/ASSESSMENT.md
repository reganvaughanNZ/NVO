# Titans of the New West 2.1.51d: NVO donor assessment

Reviewed 17 September 2026. Recommendation: add as a **candidate power-armour presentation and equipment integration module**. Selective adaptation is worthwhile; merging the complete plugin unchanged would introduce overlapping gameplay owners. No donor files were installed, no plugin was merged, and no game or GECK test was run.

This replaces the earlier information-only assessment in `source/combat/step4d/TITANS-ASSESSMENT.md`. It does not alter that packet's frozen source/evidence or the live combat checkpoint. Consult `STATUS.md` for the current combat checkpoint.

Only this NVO-authored assessment is published here. Donor scripts, assets, archive listings and plugin inventories mentioned below remain local. Recorded findings and dependency versions describe the September 17 review, not a new compatibility check.

## Download and available source

- Archive: `Titans of The New West-78688-2-1-51d-1771136133.7z` (local download).
- SHA256: `d546a14ecbb9034de50a948ada55d1a90e8dc4d40e2d8f4a371a77d99253f50e`.
- Archive listing: 2,484 files, including 1,770 KF animations, 160 NIF meshes, 104 DDS textures, 320 WAV sounds, one ESP, configurations and loose scripts. No DLL or C++ source is included.
- The ESP contains **61 SCPT records with readable embedded SCTX source**, extracted into scripts (`scripts`, local archive). These are useful source even without a separate C++ repository. Source text availability is not proof that a complete rebuild reproduces the shipped bytecode.
- ESP masters: FalloutNV, DeadMoney, HonestHearts, OldWorldBlues, LonesomeRoad and GunRunnersArsenal. **Neither TTW nor RD is a master.** Optional TTW paths remain in scripts/assets.
- Evidence: archive manifest (`archive.json`, local archive), file listing (`archive-list.txt`, local archive), plugin inventory and embedded source (`plugin-inventory.json`, local archive). Only the ESP, text and configuration files were extracted into the workspace. Animation/mesh counts describe the archive, not visual or collision validation.

## What to use and who owns it

| Feature | NVO integration proposal |
|---|---|
| Bulky armour models, textures, stance and locomotion | Retain selected presentation assets and their required animation setup as a separable module. Verify first/third-person alignment and actual hit behaviour before enabling it for combat tests. |
| Weapon handling and fitted unarmed/launcher models | Adapt the existing animation categories and model switching together. Confirm muzzle position, reload/fire timing and NVO projectile identity remain correct. New poses do not authorize changing cartridge or damage profiles. |
| Terrain footsteps, mechanical sounds, landing feedback | Retain selected audio/visual feedback; use configurable volumes and optional camera shake. Landing feedback must not independently apply combat damage or crowd-control effects. |
| Pip-Boy bracer, backpack hiding, equip/unequip restoration | Useful existing work, but keep the necessary state restoration and menu/POV transitions. Check reload, hotkeys, rapid swaps and nonstandard Pip-Boys. |
| Armour configuration and exceptions | Reuse the data-driven design. NVO's authoritative identity stays owning-plugin plus local FormID. The donor's EditorID filenames and presentation keywords are not sufficient protection/coverage evidence. |
| Protection, limb injury, resistance and impact reactions | NVO owns the resolved hit and resulting protection/injury/reaction decisions. Adapt or remove overlapping donor gameplay paths instead of stacking them. |
| Powered assistance and environmental functions | Later explicit equipment capabilities, distinguishing powered suits from NCR salvaged armour. Select strength assistance, underwater behaviour or recycling individually after gameplay design; do not inherit blanket defaults. |

The donor's script/assets architecture does not by itself justify another custom DLL. Existing extenders can run presentation logic; NVOCombatCore remains the planned combat authority. Keep resource files, presentation scripts and NVO protection profiles separate so changes do not require rebuilding everything.

## Findings from the actual code

1. **There is substantial useful structure.** `TNWEquip`/`TNWUnequip` handle transitions; `TNWQuestActors` processes one cached actor per quest iteration and stops after the pass; `TNWArmorLoop` checks processing level and unregisters when armour is absent. Profiles and cached configuration avoid embedding all armour definitions in one script. This is a focused architecture review, not a claim that all 61 scripts are audited or bug-free.
2. **Stat updates remain writes even with improvements off.** TNWArmorStatsUpdate (`scripts/043_060C90D1_TNWArmorStatsUpdate.txt`, local archive) sets DR, DT, item health and object effects, including branches that restore previously captured values. `Stats:bENABLE=0` gates improved values; it does not mean the updater never writes. Establish ownership and remove these writes from an NVO presentation adaptation after planning any required migration.
3. **Explosion damage is modified directly.** TNWOnExplosionHit (`scripts/053_060D680C_TNWOnExplosionHit.txt`, local archive) calls `SetExplosionHitDamage` with a class-dependent reduction when enabled. That handler must not also reduce damage after NVO resolves the same explosion.
4. **Perks and actor values are separate integration points.** TNWEquip (`scripts/028_0606BC6F_TNWEquip.txt`, local archive) and TNWQuestActors (`scripts/033_0602DB2F_TNWQuestActors.txt`, local archive) add Adamantium Skeleton, Ignore Crippled Limbs and Water Running donor perks to NPCs; TNWPostLoadGame (`scripts/047_06043D6D_TNWPostLoadGame.txt`, local archive) installs player perks. Their exact entry-point conditions and all supporting effects need an implementation-stage audit. Merely seeing an added perk does not prove its effects are unconditional.
5. **A profile's `Effect=0` is not a universal gameplay-off switch.** The included armour README (`extracted/config/TNW_Armors/_README.txt`, local archive) explicitly distinguishes that value from some other bonuses. The settings reader (`scripts/026_060662E1_TNWModSettingsUpdate.txt`, local archive) also separates `Stats`, `Gameplay`, `Sounds` and animation options. Its missing-INI fallback for `Stats:bENABLE` is **0**; do not claim the archive enables every improved stat by default. Underwater gravity and recycling have their own defaults.
6. **Scale and gravity need ownership.** Equip sets actor scale to 1.10/1.12/1.14 by presentation class. Unequip restores cached base height or 1.0. Player/NPC armour loops repeatedly write gravity, including 1.0 outside swimming. That can conflict with future movement donors. Retain/restore owned state rather than assuming the neutral value belongs to NVO. Larger meshes or actor scale do not establish anatomical coverage, hitboxes or penetrable material thickness.
7. **Global extender changes are present.** `ln_tnw_titans.txt` enables JIP's `uNPCPerks`; the supplied Tweaks INI enables 3D armour sounds and makes melee/non-melee damage ignore character scale. These settings require an explicit owner. Scale should not accidentally become a second damage multiplier.
8. **Startup and merge glue need adaptation.** The loader uses intrusive `MessageBoxEx` dependency warnings. NVO's implementation should use the established once-per-process console diagnostics. `TNWProcessItems` looks up `Titans of The New West.esp` by filename; MCM expects that plugin and the animation JSON refers to donor keywords/AuxVars. An ESP merge alone would not redirect these external references or preserve all assets automatically.
9. **Performance is unmeasured.** Per-actor armour callbacks use intervals and footstep callbacks can run every frame for active actors. Retain event-driven transitions, cache mappings and cap unnecessary work. Later assess multiple armour wearers, cell unload and reload; no FPS or stability guarantee follows from static inspection.

## Dependencies and permissions

The [author's page](https://www.nexusmods.com/newvegas/mods/78688) lists the NVSE extenders, Stewie's Tweaks, and optional MCM support. The downloaded loader checks xNVSE 6.4+, JIP 57.3, JohnnyGuitar 518, kNVSE 30 and ShowOff 180. The available game-root `nvse.log` reports xNVSE 6.4.8, JIP 5730, JohnnyGuitar 525, kNVSE 37 and ShowOff 184. These recorded versions meet those checks; they do not prove the entire mod is ready to install. No Stewie/Tweaks DLL was found in the inspected Plugins directory or that log's loaded-plugin list. Having its source in donors is separate from installing its runtime.

The archive lacks the main `TNW_Titans.ini`. The author's installation instructions call for the separately downloaded Titans INI. Script fallbacks allowed this source review without it. Obtain/review that INI before a standalone installation or use an explicitly authored configuration for an NVO adaptation. No additional download is needed to complete this assessment.

Credit **Wombat / Woooombat, Titans of The New West 2.0, version 2.1.51d**. The author specifies [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/): retain attribution, identify changes, use noncommercially and preserve ShareAlike requirements for adaptations. Keep donor notices distinct; do not relabel these resources as NVO's native-code license. This workspace extraction is for review and contains no adapted donor code yet.

## Proposed placement in the plan

After the current armour diagnostic checkpoint, prepare a separate **power-armour presentation prototype** when approved. Start with one verified T-51b suit/helmet and the player plus one NPC, with donor damage/stat modification paths excluded. Keep normal clothing unaffected and verify equip/unequip, reload, Pip-Boy, body scaling and weapon alignment. No armour-protection claim follows from this visual prototype.

Add physical protection through the existing Step 4 armour profiles and NVO's coordinated result. Add any reaction/handling behaviour with Step 6; tune Brotherhood/Enclave/NCR starts at Step 8. Energy and flame protection must use their own later profiles, not the donor's general resistance values. This candidate does not advance damage authority or replace the existing review/test gates.

No changes were made to NVO.esm, NVOCombatCore, installed game files, load order, or the pending combat packet.
