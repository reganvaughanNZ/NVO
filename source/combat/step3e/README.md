# NVO Combat Packet 3E - three more standard-ammunition weapons

**Purpose:** extend the accepted flight system to the ordinary **10mm Pistol, .357 Magnum Revolver and .44 Magnum Revolver**, using their standard ammunition. Each gets a private projectile with donor barrel/velocity/drag tuning. Your previous four-weapon checkpoint remains accepted.

This updates the existing preview INI and pilot ESP and adds one console kit file. The DLL remains **build 311 / 0.3.11**; `phase=3D` in its log header is expected. Nine profiles should load: seven regular weapons and two legacy private test combinations.

Keep **NVO.esm and NVOFlightPilot.esp active**. No GECK work or compilation is required. The assistant has not run the game; your check is next.

## Get the kit

Load your prepared test save and wait three seconds. In the game console, run:

```text
bat NVOFlightKit3E
```

The kit gives the exact supported version of each weapon and 100 standard rounds for each. It adds inventory each time it runs; use it again only if needed. Use the ordinary weapon names above and standard **10mm Round**, **.357 Magnum Round** and **.44 Magnum Round** ammunition. God mode is fine.

## Four-shot checkpoint

1. Stand well back from an unobstructed solid target, roughly **100 metres** if practical. The distance used for the successful 3D1 scenery shots is suitable.
2. Outside VATS, fire **one 10mm Pistol shot**, **one .357 Magnum Revolver shot** and **one .44 Magnum Revolver shot**, pausing between weapons.
3. **Reload once**, wait three seconds, and use the kit again only if needed. Fire **one .44 Magnum Revolver shot in VATS at a distant live enemy with a clear line of fire**. If no suitable target is available, report that rather than repeating the setup.
4. Exit and report completion. Mention if an initial load was setup. I will read and archive `NVOCombatCore.log` beside FalloutNV.exe. Wait for review before another launch overwrites it.

No repeat of the previous weapons, video or stress test is needed. If flight reports unavailable or a weapon fails to fire normally, stop and report it.

## Expected evidence

The selector should be ready after each load. All four selections must be corroborated by actual projectile creation and the equipped standard ammunition. Each new weapon should have an unchanged baseline followed by verified edited free-flight segments before collision. The final shot should have a linked live-actor hit after reload. VATS context comes from your report; build 311 does not log a direct VATS flag.

| Profile | Stock weapon | Standard ammo | Original projectile | Private projectile local ID |
|---|---|---|---|---|
| 10mm Pistol | FalloutNV.esm:00434F | FalloutNV.esm:004241 | FalloutNV.esm:02CD5F | NVOFlightPilot.esp:00080A |
| .357 Magnum Revolver | FalloutNV.esm:08F216 | FalloutNV.esm:08ED02 | FalloutNV.esm:08F20C | NVOFlightPilot.esp:00080B |
| .44 Magnum Revolver | FalloutNV.esm:08F215 | FalloutNV.esm:02937E | FalloutNV.esm:03BF0C | NVOFlightPilot.esp:00080C |

Runtime load-order prefixes may differ. The kit uses the canonical base-game weapons, avoiding other records that happen to share their display names.

## Special ammunition and damage scope

This packet adds only the three standard rounds above. Hollow points, handloads and other variants still retain their existing behaviour when the exact ammunition combination is not profiled. The expanded standard coverage does not imply those variants are supported. Their dedicated profiles and coordinated damage/penetration rules will be separate packets. NVO damage replacement remains disabled; vanilla damage, ammunition effects and critical handling continue through the existing engine path.

## Installation and reversal

Requires the accepted 3D1 installation. The installer verifies the foundation, backs up existing files and logs, and changes exactly these paths:

- `Data/NVOFlightPilot.esp` - adds three private PROJ records; preserves the previous ten private records.
- `Data/NVSE/Plugins/NVOFlightPreview.ini` - appends three profiles; preserves all six existing profiles.
- `NVOFlightKit3E.txt` - new game-console batch beside FalloutNV.exe.

The completed `Installation/INSTALL-3E.md` receipt names the backup. To reverse, close the game, restore **both** the ESP and preview INI from that backup's `originals` directory, and remove the newly added `NVOFlightKit3E.txt`. Keep the existing DLL, physics INI, older kits, NVO.esm and activation unchanged. Restore the record/configuration pair together.

BallistX credits and applicable notices are included. Donor tuning and the 70 units/metre assumption are retained design inputs, not independently calibrated measurements. Exact contact-time energy and armour/injury authority remain later work. Await review before another packet.
