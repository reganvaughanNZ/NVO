# Combat packet 2A: observe hit events

**Purpose:** capture what the working extenders report for bullets, shotgun pellets, melee and explosions before developing NVO's damage replacement. Packet 1 startup was accepted in your playtest.

This is the first checkpoint within Step 2. It uses JIP and ShowOff's native events through loose scripts. **It does not implement or validate NVOCombatCore's own native hit hooks.** That remains Step 2B. The native foundation project is still source only; a compatible C++ build toolchain was not found in the inspected locations.

Prepared for your test. The assistant has not compiled, run or tested these scripts, installed files, or edited your ESM. No GECK changes are required for this packet: xNVSE and JIP compile the loose scripts when you launch the game.

## Install this packet

1. Close Fallout New Vegas. Extract `NVO-Combat-Packet-2A.zip` outside the game folder.
2. Copy the **contents of its Data folder** into your existing game Data folder:

   `C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas\Data`

3. Launch normally with your working extenders and load a save or start a game. Keep the accepted packet 1 quest as it is.

The resulting loader path must be `Data\NVSE\Plugins\scripts\ln_NVOCombatDiagnostics.txt`, with no extra `Data\Data` directory. Copy all seven supplied files. Do not paste them into ALTStartQscript or the bootstrap quest. No DLL or ESM is included. Existing donor damage/flight loaders should retain their current state for this comparison.

**First check:** open the console yourself and look for:

```text
NVO diagnostics 2A: capture armed, limit 300 event rows. This packet does not change damage.
```

It should appear once per new game/save load, not repeatedly during play. There are no message boxes or automatic console opening. If precompilation fails or this line never appears, send the error text before trying later steps. Compiler details are in the game-root `nvse.log` and `jip_ln_nvse.log`.

## Your short capture

In one short session, use a normal single-projectile gun, a shotgun, a melee weapon and an explosive. Take a few incoming hits too. Note which weapons you used and, where practical, head versus torso shots. NPC-to-NPC combat can be captured in the same session. Robot and VATS examples are useful if convenient; they are not proof of NVO injury rules, which do not exist yet.

Then send **NVOCombatDiagnostics.log**, from:

```text
C:\Users\regan\Desktop\Steam Install Folder\steamapps\common\Fallout New Vegas\Data\NVSE\Plugins\NVOCombatDiagnostics.log
```

**Copy that log before reloading or starting another game. Each successful initialization replaces it.** Reload once afterwards to check for one fresh initialization message and a new log starting at row 1. A quiet reload only needs a few shots to check for obvious handler multiplication; an exact event count per shot is not assumed.

Capture stops at 300 event rows and reports that once in the console. It counts events, not shots: a projectile can produce CREATE, IMPACT and HIT rows, and a shotgun can consume several rows per shot. Distant combat can also use the allowance. If necessary, change `MaxRecords` in `Data\Config\NVOCombatDiagnostics.ini` and reload; the maximum is 2000. There are no actor scans or per-frame logging loops. Registered callbacks keep a small disabled guard after reaching the limit.

## What the log establishes

- **CREATE:** projectile reference/base, source, weapon and the source's current ammo at creation.
- **IMPACT:** projectile reference/base, struck reference, source, weapon and projectile damage/distance/lifetime readings.
- **HIT:** target/reference base, attacker, hit weapon/object, raw body-region code, current source ammo and engine health/limb/base-weapon damage readings.
- **EXPLOSION:** explosion reference/base, actor target, source and the explosion-event damage reading.

The engine penetration flag is a diagnostic field, not NVO's planned armour calculation. Damage values are event readings, **not measured health loss**; do not add HIT, IMPACT and EXPLOSION values together. Projectile and explosion events can describe different stages of the same attack. Null IDs, unknown regions and unmatched events are retained for review. Environment impacts need not have an actor target.

Ammo fields are source snapshots, not guaranteed projectile-carried ammo. Melee and explosions may have no meaningful ammo. Projectile reference IDs help correlate creation with impact within a capture, but references can be recycled and we do not assume every hit exposes the same object ID. No events are merged or discarded on the assumption that similar rows are duplicate damage. Body-region codes will be interpreted against the actor's body-part data, not as internal-organ coordinates.

## Suspend or reverse

Set `Enabled=0` in the INI and reload: the loader removes its own callbacks and leaves the previous log intact. While playing, this console command stops further capture immediately:

```text
player.AuxVarSetFlt "*_NVODiagEnabled" 0
```

For full removal, close the game and remove only the seven files listed in `manifest.json`. Optionally remove the generated log. Keep the extenders, NVO.esm and other mods' scripts. The packet uses temporary, globally named diagnostic auxiliary variables and no saved injury state. Exit clears its runtime callbacks; it makes no health, damage, equipment, projectile-flight or save-file changes.

**Stop here and report the capture result.** We will review it before agreeing to Step 2B: custom native registration/build and hit-hook diagnostics. BallistX flight and NVO damage replacement remain later checkpoints.
