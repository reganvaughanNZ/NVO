# Packet 3B2: isolated physical-flight calibration

Purpose: measure actual bullet travel for the 9mm pistol and hunting rifle before adding an NVO flight integrator. Version **0.3.2 / 302**. The previous 3B1 matching and reload checkpoint passed, but both original projectile records were hitscan. This packet gives isolated test copies finite-speed projectiles. No new native hook or damage replacement is enabled.

## What changes

NVOFlightPilot.esp contains six new records: two weapons, two ammunition types and two projectiles. Names begin **NVO Flight -**. It has one master, FalloutNV.esm, and no overrides, scripts, quests, placed objects, distribution lists or new assets. NVO.esm is unchanged. Original weapons continue using their original projectiles. The copies use the base game's weapon records, rather than inheriting every mod's weapon-specific override or perk/list membership; they are calibration equipment, not balanced playable replacements.

Only private PROJ hitscan, gravity and speed fields are changed. Hitscan is off, gravity is zero, and speeds are 27097.6367 and 59484 engine units/second (about 387.109 and 849.771 m/s under BallistX's assumed 70 units/metre). Stock projectile range and other fields are retained. Weapon damage and critical-data subrecords are copied unchanged. Ammunition and weapon projectile links point exclusively to the private records. There is no NVO drag, weather, damage scaling or three-second deletion rule. The engine advances these projectiles; the native DLL measures them. This is a controlled calibration step toward the planned native integrator, not completion of Step 3.

## Your check

1. Launch normally and load an existing test save. Wait three seconds. Plugin version is **302**. The installer enables NVOFlightPilot.esp; if your mod manager rewrites the activation list, enable that plugin there too.
2. In the console run **bat NVOFlightPilot**. This adds the two NVO Flight weapons and 40 rounds for each. It runs only when you enter it; there is no automatic equipment grant. The DLL rebuilds this batch with the current load indices after each successful capture initialization.
3. Outside VATS, equip **NVO Flight - 9mm Pistol** with its matching **NVO Flight - 9mm Round**. Fire two shots at a visible wall or solid ground roughly 50-100 metres away. Repeat with **NVO Flight - Hunting Rifle** and its matching **NVO Flight - .308 Round**. Avoid shooting straight into empty sky: we need a visible impact.
4. Reload your original test save in the same running game. Wait three seconds, run **bat NVOFlightPilot** again if the test equipment is absent, and fire one shot with each NVO Flight weapon. This specifically checks the new records and travel measurements across reload.
5. Exit and send **NVOCombatCore.log beside FalloutNV.exe**, before launching again. Brief weapon/target notes are enough. God mode is acceptable; this check does not assess HP damage. No GECK compiling is required.

If the kit is unavailable, send the log. Do not use a stale batch from another load order or substitute the ordinary weapons for these named copies. The regular weapons are still included as optional baseline profiles, but repeating the old preview test is not required.

## Expected evidence and limits

FLIGHT_PREVIEW_READY should report four profiles. FLIGHT_PILOT_KIT should report ready=1. The pilot-9mm and pilot-308 creation rows should show hitscan=0, gravity_setting=0 and the configured speed. FLIGHT_TRAVEL should have positive time/distance for sufficiently distant impacts and mean_speed_valid=1. We will compare the engine-counter average with the configured speed, including frame/impact timing effects. It is not a direct muzzle-vector measurement or independent proof that 70 units equal a metre.

The existing flight_writes=0 log fields refer to native memory writes. This packet DOES change flight through its two private PROJ records, as isolated_record_flight_pilot=1 in the header explains. Damage replacement remains 0. Disabling the INI observer does not turn the ESP's physical projectiles back into hitscan. Disabling the pilot ESP removes access to the calibration copies; the original weapons never depend on it.

The observer retains the existing version/layout guards, bounded cache (first 32 matches per capture), lifecycle cleanup and no retained projectile pointers. The new native side effect is writing the reserved game-root NVOFlightPilot.txt console batch at capture initialization. Failed or unavailable initialization clears it when the path can be written. It refuses file reparse points and multi-link targets before truncation. Console notices run outside the observer lock. No new event interfaces, callbacks, serialization or engine object writes are introduced.

The narrow donor-loader audit is unchanged: loaded BallistX names and known loose PBB/CBD loader paths only, not proof about BSA content or every mod. If another mod alters these private records, the logged state should expose the discrepancy; this packet cannot enforce flight ownership against arbitrary other mods. Normal flight is engine-owned even if diagnostic hooks are unavailable.

## Files and reversal

Installed: DLL, matching PDB, NVOFlightPreview.ini, Data/NVOFlightPilot.esp and a reserved initially empty NVOFlightPilot.txt in the game root. The installer appends only NVOFlightPilot.esp to the existing plugins.txt activation list. Source, record-generation tool, record audit, credits and build evidence accompany the release. Installation receipt supersedes the manifest's packaging-time status. Existing extenders, NVO.esm, settings, saves and other activation entries are preserved.

To reverse: close the game, disable NVOFlightPilot.esp, restore the previous DLL/PDB/INI from the installation backup, and remove the newly added pilot ESP and generated batch (or restore their prior versions if the receipt records any). The backup contains the original plugins.txt; restore it only if you have made no later activation changes, otherwise remove just the pilot entry. Load your pre-pilot test save to leave the temporary test equipment behind. Do not merge the pilot into NVO.esm yet.

## Verification and next boundary

Compiled and statically inspected by the assistant; all gameplay is for the user. Static record checks validate unique new IDs, private WEAP-AMMO-PROJ links, master dependency, HEDR record/group count, permitted field changes and unchanged weapon damage/critical bytes. These checks do not certify runtime flight. Await the user's log before adding native gravity/drag or adapting original weapons. Armour and injury rules remain later packets.

Record-layout reference: [xEdit FNV definitions](https://raw.githubusercontent.com/TES5Edit/TES5Edit/dev-4.1.6/Core/wbDefinitionsFNV.pas). BallistX's two cartridge/barrel rows and formula are credited in CREDITS-BALLISTX.md and the retained 3A provenance. No new extender downloads are needed.
