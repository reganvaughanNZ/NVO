# NVO Combat Packet 3F — Hunting Rifle ammunition

**Purpose:** verify that the existing native selector follows the actual .308 round when you switch between standard, armour-piercing (AP) and hollow-point (HP) ammunition, then load a save. This is an ammunition-identity and flight checkpoint before NVO armour/damage work.

The ordinary Hunting Rifle receives two additional exact ammunition profiles. All three rounds deliberately share the accepted standard .308 velocity and drag settings for this checkpoint. They are separately identifiable in the log. This does **not** claim AP and HP have identical real-world trajectories. Existing ammunition damage/DT effects remain with the engine; NVO damage replacement stays disabled.

Keep **NVO.esm and NVOFlightPilot.esp active**. RD.esm remains a required NVO master. No GECK work or compilation is needed. The DLL remains **build 311 / 0.3.11 / phase3D**; **11 loaded profiles** identifies this update.

## Get the kit

Load your prepared test save and wait three seconds. In the game console, run:

```text
bat NVOFlightKit3F
```

It gives one ordinary Hunting Rifle and **40 rounds each** of standard .308, .308 AP and .308 HP. Each run adds another kit; regrant only if needed. It does not change your stats, quests, health or god mode. God mode is fine.

## Five-shot check

1. Use the ordinary **Hunting Rifle** from the kit and a distant solid target with clear line of fire. Your previous successful long-range test distance is suitable, roughly 100 metres if practical.
2. Outside VATS, fire **one standard .308 shot → one AP shot → one HP shot → one standard .308 shot** at that target. Use your normal ammunition-switch control, allow the reload/switch animation to finish, and confirm the selected ammo label before each shot. Avoid JSP Hand Load and other variants.
3. Switch back to **HP**, let the switch finish, and **make a test save**. **Load that save once**, wait three seconds, and confirm HP is still selected. This means loading a save, not just reloading the rifle. If the ammo changed, report what you see before selecting HP again.
4. Fire **one HP shot in VATS at a distant live enemy** with a clear line of fire. Mention if it misses; no repeated setup or stress test is needed.
5. **Exit and report completion.** I will read `NVOCombatCore.log` beside FalloutNV.exe. Wait for review before another launch overwrites it. Mention any setup loads, extra shots or unexpected ammo selection.

If a flight-unavailable message appears or the rifle stops firing normally, stop and report it. No video or repeat of earlier weapon tests is required. This packet has not been gameplay-tested by the assistant.

## Expected result

The selector should load 11 profiles and switch exact ammo/projectile identity in the order above. All three combinations should have matching baseline and edited free-flight segments, without stale selection or duplicate projectile tracking. The final HP shot should produce a linked live-actor hit after loading the save. VATS use comes from your report; build 311 does not log a direct VATS flag.

| Round | Stock AMMO | Profile | Private projectile local ID |
|---|---|---|---|
| .308 Round | FalloutNV.esm:06B53C | hunting-rifle | NVOFlightPilot.esp:000807 |
| .308, Armor Piercing | FalloutNV.esm:13E442 | hunting-rifle-ap | NVOFlightPilot.esp:00080D |
| .308, Hollow Point | FalloutNV.esm:13E443 | hunting-rifle-hp | NVOFlightPilot.esp:00080E |

All three use stock weapon FalloutNV.esm:004333 and source projectile FalloutNV.esm:08F20A. Runtime load-order prefixes may differ. Other rifles, JSP loads and unclassified rounds retain their existing fallback behaviour.

Damage differences alone do not prove NVO penetration or final health loss. Later packets will define variant-specific flight tuning and coordinated damage ownership. The existing unit-scale, first unchanged segment and contact-energy limitations remain.

## Installation and reversal

Requires accepted packet 3E. Changes exactly these paths:

- `Data/NVOFlightPilot.esp` — appends two private PROJ records; preserves all 13 previous private records.
- `Data/NVSE/Plugins/NVOFlightPreview.ini` — appends AP and HP profiles; preserves all nine previous profiles.
- `NVOFlightKit3F.txt` — new game-console batch beside FalloutNV.exe.

The installation receipt names the verified backup. To reverse, close New Vegas, restore **both** the ESP and preview INI from that backup's `originals` folder to the matching game paths, and remove the newly added `NVOFlightKit3F.txt`. Restore the record/configuration pair together. Keep the existing DLL, physics INI, older kits, NVO.esm, RD.esm and activation unchanged. This returns to accepted 3E.

BallistX credits and applicable notices are included. Source snapshots, record audits and transaction records accompany this update. Await review before another packet.
