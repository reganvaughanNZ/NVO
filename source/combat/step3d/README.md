# Packet 3D - four regular weapons and a ready-made kit

Purpose: apply the verified flight system to the ordinary **9mm Pistol, Hunting Rifle, 9mm Submachine Gun and Service Rifle**, using standard 9mm, .308 and 5.56mm ammunition. Build **311 / 0.3.11** adds explicit per-shot selection and configurable drag profiles. Your gameplay check is required before this expansion is accepted.

## Give yourself the kit

Keep **NVO.esm and NVOFlightPilot.esp active**. No GECK editing or script compilation is needed for this packet. After loading your test save and waiting three seconds, open the game console and run:

```text
bat NVOFlightKit
```

This grants one of each regular weapon, 300 standard 9mm rounds, 100 standard .308 rounds and 200 standard 5.56mm rounds. New Vegas console batch files have a **.txt** extension; this is `NVOFlightKit.txt` beside FalloutNV.exe. You run it inside the game, not by double-clicking a Windows .bat file. Running it again adds another kit.

Use the regular weapon names above, with standard ammunition selected. The older weapons named **NVO Flight - ...** remain available for regression checks, but this checkpoint uses the regular weapons. The older `bat NVOFlightPilot` command still grants that earlier kit.

## One compact checkpoint

1. Load your prepared test save, wait three seconds, and run `bat NVOFlightKit`. God mode is fine.
2. Stand well back from a solid target, such as the Goodsprings water tank. Outside VATS, fire **one 9mm Pistol shot, one Hunting Rifle shot and one Service Rifle shot**, pausing briefly between weapons. Then fire a **short burst of about three rounds** from the 9mm Submachine Gun. Keeping the burst short preserves detailed samples for all four weapons.
3. Reload the original test save once, wait three seconds and run the kit command again if needed. Fire **one Service Rifle shot in VATS at a distant live target**. This checks selection after reload and the new 5.56 profile in VATS.
4. Exit and report completion. I will read `NVOCombatCore.log` beside FalloutNV.exe directly. Wait for review before another launch overwrites it.

If the console reports that flight is unavailable, or a weapon fails to fire normally, stop and report it. No video or additional stress test is needed for this checkpoint.

## Expected results

The log should identify build311, six explicit profiles (four regular weapons and two retained test combinations), and `FLIGHT_SELECTOR_READY ready=1`. Each regular standard-ammo shot should show `FLIGHT_SELECT` and then a created projectile with the selected private base, actual matching ammunition and unchanged weapon/source identity. A selection return alone is not proof that the engine used it.

For shots with enough travel, the unchanged first segment and later `PHYSICS_ACTUAL` samples should match. The SMG uses the same cartridge coefficient as the pistol but its own donor barrel length and muzzle speed. The Service Rifle uses the donor 5.56 G7 coefficient of0.151. Exact impact speed/energy and damage replacement are not accepted by this test. Reload must clear tracking and resolve the profiles again without duplicate selection.

## Reversal and tuning

The installer backs up every replaced file and the current log. The completed `INSTALL-3D.md` receipt names the exact backup. With the game closed, restore the five replaced files from that backup (DLL, matching PDB, both flight INIs and NVOFlightPilot.esp), and remove the newly installed NVOFlightKit.txt if it did not previously exist. NVO.esm, other extenders and load-order activation are preserved. No save edits or automatic inventory grants are performed.

To disable an ordinary weapon's selection, set `flight_enabled=0` in that weapon's section in `Data/NVSE/Plugins/NVOFlightPreview.ini` and reload. To disable the native flight system, set `[Physics] enabled=0` in NVOFlightPhysics.ini and reload; the ordinary weapons then use their original projectiles. The legacy private test weapons still have their original physical test-projectile records.

Drag model and coefficient are now cached per projectile from the profile. Barrel/velocity edits also require matching private projectile speed data; the loader deliberately rejects inconsistent records instead of silently mixing the two. The preparation tool regenerates those four records from the donor rows. The configured 70 units/metre and donor barrel/cartridge values remain tuning assumptions, not independently calibrated physical measurements.

Installation is not a gameplay pass. The assistant compiles and checks source/records/binary identity; the user performs the game test.
