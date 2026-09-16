# NVO Combat Packet 3D1 - SMG mapping correction

**Purpose:** give the regular 9mm Submachine Gun its intended NVO flight profile, then finish the outstanding rifle-flight checks. Your pistol result remains accepted.

This is a two-file update to packet 3D. It corrects the SMG source in `NVOFlightPreview.ini` and rebuilds its private projectile in `NVOFlightPilot.esp` from the actual vanilla SMG projectile. The native DLL remains **build 311 / 0.3.11**; seeing `phase=3D` in the log header is expected. The SMG profile's corrected original projectile identifies this revision in the log.

Keep **NVO.esm and NVOFlightPilot.esp active**. No GECK work or compilation is required. Damage replacement remains disabled.

## Give yourself the existing kit

After loading your prepared test save and waiting three seconds, use the game console:

```text
bat NVOFlightKit
```

The installed kit already grants the regular 9mm Pistol, Hunting Rifle, 9mm Submachine Gun and Service Rifle, plus standard ammunition. Run it only if you need the equipment; each run adds another kit. Use the ordinary weapons, not the older weapons whose names start with “NVO Flight”. God mode is fine.

## Short follow-up

1. Use an open area with a clear line of fire to a distant solid target. Stand roughly **four times farther back than in the last test**, aiming for about **100 metres** if practical. The fast rifle bullets need more travel before impact to provide a useful flight sample. Avoid intervening walls, roofs or cover.
2. Outside VATS, fire a **short burst of about three rounds from the 9mm SMG**, then **one Hunting Rifle shot** and **one Service Rifle shot**, pausing between weapons. Use **standard 9mm, .308 and 5.56mm ammunition** respectively. No pistol retest or stress test is needed.
3. **Reload once**, wait three seconds, and use the kit command again only if needed. Fire **one Service Rifle shot in VATS at a distant live enemy with a clear line of fire**. The last log recorded scenery on this step, so a live-target hit is still unconfirmed. If no suitable target is available, say so when reporting rather than repeating the setup.
4. Exit and tell me you finished. I will read and archive `NVOCombatCore.log` beside FalloutNV.exe. Wait for review before another launch overwrites it. If the first load was setup, mention that again.

If the console reports flight unavailable, or a weapon stops firing normally, stop and report it. No video is needed.

## What the log should establish

- The selector is ready after load and reload.
- SMG selections use original `FalloutNV.esm:17A2C6` and replacement `NVOFlightPilot.esp:000808`. Actual projectile creation and equipped standard 9mm ammunition must corroborate each selection. The runtime load-order prefix may differ from earlier logs.
- The SMG burst has clean overlapping projectile lifetimes and useful edited free-flight samples. Both rifles have edited free-flight matches before collision.
- The reload shot confirms Service Rifle selection, useful flight and a linked live-actor hit. VATS is user-reported context: build 311 does not log an explicit VATS-mode field.
- No guard failure, unmatched lifetime or leftover tracking state. Damage replacement stays off. These checks do not establish precise collision-time energy or armour/injury behaviour.

## Installation and reversal

This update requires the existing packet 3D installation. It replaces only:

- `Data/NVSE/Plugins/NVOFlightPreview.ini`
- `Data/NVOFlightPilot.esp`

The installer verifies the existing foundation, backs up both files and the current logs, replaces the two files, then checks their hashes and protected files. It may close the exact game process under your existing permission. It does not launch the game.

The completed `Installation/INSTALL-3D1.md` receipt names the backup. To reverse this update, close the game and restore **both** files from that backup's `originals` directory to their matching paths below the game root. Keep the existing build 311 DLL, physics INI, kit, NVO.esm and activation unchanged. Restoring only the INI or only the ESP can leave source/clone validation inconsistent.

Review the short follow-up before proceeding to another packet. BallistX credits and applicable notices are included.
