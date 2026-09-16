# Packet 3B1: native flight preview

Status update, 15 September 2026: the pilot-matching and reload checkpoint is accepted in REVIEW-1.md. Keep version 301. The initial test instructions below are retained for reference; no repeat is needed. Physical flight is not yet implemented or validated.

Purpose: check BallistX pilot selection and initial-speed inputs against real shots before changing flight. NVOCombatCore **0.3.1 / plugin version 301** reads a small loose INI and observes the existing projectile callbacks. Flight, damage, armour, spread, health and save data remain unchanged.

## Installation and GECK

The assistant installs this packet using the existing session authorization. Only these three files belong in the game:

- `Data/NVSE/Plugins/NVOCombatCore.dll`
- `Data/NVSE/Plugins/NVOCombatCore.pdb`
- `Data/NVSE/Plugins/NVOFlightPreview.ini`

No GECK record or script changes are required. Keep the current xNVSE, JIP, ShowOff and ITR versions. Do not activate standalone BallistX, CBD or PBB loaders. The preparation JSON from packet 3A remains source material; the native reader consumes the INI only. This packet adds no extender dependency, engine hook or script opcode.

The installation receipt and backup location are recorded in INSTALL-3B1.md after deployment. The release's manifest describes packaging-time state; the receipt establishes what was actually installed. Source, configuration, credits, full matching PDB and build evidence accompany the compiled ZIP.

## Short user check

1. Launch normally and load your test save. Wait about three seconds. `GetPluginVersion "NVOCombatCore"` should return **301**.
2. Outside VATS, fire two shots with the ordinary **9mm Pistol**, using **standard 9mm** ammunition, toward a wall or ground some distance away.
3. Fire two shots with the ordinary **Hunting Rifle**, using **standard .308** ammunition. Maria, Paciencia and other variants are outside these two initial profiles.
4. Reload the save within the same running game, wait about three seconds and make one more shot with either pilot combination. This checks the new profile/cache reset; the old hit-observer reload check is already accepted.
5. Exit and send **NVOCombatCore.log beside FalloutNV.exe**, before launching again. A short note naming the weapons/ammo is sufficient; no recording is needed unless something visible goes wrong.

God mode is acceptable for this flight-input check: it does not measure incoming HP loss. Leave the current combat/health settings as they are. The HTML guide provides a version-command copy button and optional item commands if you need the ordinary pilot weapons/ammo. Adding test items is optional and is the user's action.

## Expected log

- `FLIGHT_PREVIEW_READY ... profiles=2 ... flight_writes=0` after loading.
- `FLIGHT_PROFILE` rows resolve filename/local IDs. `live_match=pending` means a matching shot has not yet been observed, not that flight is enabled.
- `FLIGHT_PREVIEW ... phase=create` identifies the actual weapon, JIP-captured projectile ammo and projectile base. The source stored on the live projectile must agree with the creation callback.
- The donor muzzle-speed previews are about **387.109 m/s** for the 9mm Pistol and **849.771 m/s** for the Hunting Rifle, at the donor reference temperature of 288.15 K. These are proposed values from donor tuning, not measured weapon specifications or applied speeds.
- `FLIGHT_TRAVEL` records differences in engine lifetime/distance counters at first impact and destruction. Hitscan or insufficient lifetime produces `mean_speed_valid=0` and a -1 speed sentinel. That is an honest unavailable measurement, not automatically an error.
- Reload creates a new capture, resolves the profiles again and clears old samples. A new matched shot should produce another preview.

`base_speed_setting * speed_multiplier` is a setting-derived value, not a measured velocity vector. The `/70` conversion is explicitly marked `assuming_donor_scale`: BallistX's units-per-metre convention has not yet been independently validated for a new flight integrator. The engine-counter average is not initial muzzle velocity. The current vanilla/modded speed is not expected to equal the donor preview while NVO flight is disabled.

Unlisted weapons, ammo and projectile combinations get a bounded `FLIGHT_PREVIEW_SKIP` diagnostic and retain engine behaviour. Names alone do not select a profile. Missing/malformed configuration or unsupported layouts disable only the flight preview and produce a log reason plus at most one console-only notice per process. No message box or automatically opened console is used. Send a disabled/mismatch log instead of installing new extenders or changing settings to force a match.

## Configuration and bounds

INI schema 1 has a `[Preview]` section followed by one to eight uniquely named profiles. Keys are case-sensitive. The parser requires complete fields, rejects duplicates/unknown keys, accepts only bounded nonnegative decimal values and limits the file to 8 KiB. Plugin keys are filenames plus six hexadecimal local-ID digits; runtime indices are resolved from the guarded loaded-mod table. `enabled=0` disables the preview. The file is reread once per successful load/new-game capture, so restart is unnecessary for later tuning checks.

The first at most 32 matches per capture get creation/first-impact/destruction samples. Only copied scalars and lifetime serials are cached; no saved actor/projectile pointers are polled later. Matching and cleanup continue after text limits. Other hit-observer limits are unchanged. The narrow owner audit reports loaded BallistX plugin names and presence of two known loose PBB/CBD loaders; it does not prove execution, inspect BSA contents or rule out other modifications. Actual flight ownership remains disabled pending a fuller audit at the write stage.

## Reversal

Close the game. Restore both previous DLL and matching PDB from the installation backup's `originals/Data/NVSE/Plugins` directory. Restore a previous NVOFlightPreview.ini if the receipt says one existed; otherwise remove only the new NVOFlightPreview.ini. Keep backups outside NVSE/Plugins. No ESM, save or dependency restoration is needed for this packet.

## Completion boundary

This delivery is complete when compiled and installed; acceptance of its runtime observations awaits the user's log. Build/static checks do not certify gameplay. Do not proceed to flight writes until the pilot matches and available speed context have been reviewed. Armour/injury, all-pellet damage, robot/NPC-to-NPC and identified VATS/committed-damage validation retain their later checkpoints.
