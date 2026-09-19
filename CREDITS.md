# NVO credits and source provenance

NVO exists because of the work shared by the Fallout: New Vegas modding community. The person who assembled and directed NVO requests **no personal credit**. Please credit the people and projects below instead.

This is the master credit record for the project. It deliberately distinguishes material incorporated into NVO from source code or mods that were only inspected. A copy in the reference folder is not proof that its code or assets ship in NVO.

Last verified: 16 September 2026. Nexus permission pages and upstream project credits can change; recheck this file before a public release.

## Material adapted into NVO

### hman101 — Alternate Start with Delayed Main Quest

- Project: [Alternate Start with Delayed Main Quest](https://www.nexusmods.com/newvegas/mods/82319), NVO donor version 1.60.
- Why credited: NVO's alternative-start records, background selection, delayed Courier/main-quest path, and related scripts are adaptations of this project.
- Permission note: the Nexus page permits modification and asset use; it prohibits uploading the original file elsewhere, conversion to another game, and commercial sale of its assets. The page does not require credit, but NVO credits hman101 because the project is foundational.
- Version note: the current page credits `tobert`/`tobert1124` for the later 1.70 update. NVO used 1.60, so that later work is not attributed as an NVO source unless it is actually adopted in the future.

### Ravuth — BallistX 5.4

- Project: [BallistX — Internal and External Ballistics](https://www.nexusmods.com/newvegas/mods/70341).
- Why credited: selected cartridge and weapon rows, G1/G7 drag tables, and the barrel-length/velocity relationship informed and were adapted into NVO's projectile profiles and native flight data.
- Permission note: the author allows modification and asset reuse with creator credit, and prohibits use of the donor assets in sold mods/files. The Nexus file-credit field names no additional creator.
- Important distinction: this is Ravuth's Fallout: New Vegas mod, not the unrelated `kodchhdayininyeri/BALLISTX` C++ library listed in the research section.

## Source interfaces and engine contracts relied on

These projects supplied ABI definitions, event contracts, data layouts, or engine research used to build NVOCombatCore. Their binaries and implementations are not bundled unless a release manifest explicitly says otherwise.

### The original NVSE and xNVSE teams — New Vegas Script Extender

- Project: [xNVSE](https://github.com/xNVSE/NVSE).
- Why credited: NVOCombatCore uses the public plugin, messaging, console, event, serialization, and loaded-mod interfaces, and checked engine-facing declarations in the source.
- Original NVSE creators: `ianpatt` (Ian Patterson), `behippo` (Stephen Abel), `scruggsywuggsy the ferret` (Paul Connelly), and `hlp` (Hugues LE PORS), with contributions from `Timeslip` and `Elminster AU`.
- xNVSE developers named by the supplied source: `korri123`/Kormakur, `cnf13`/Confused, `jazzisparis`, and `Demorome`.
- Additional contributors named upstream: `lStewieAl`, `c6`, `carxt`, `Into-The-Rough`, `Stentorious`, and `Wall_SoGB`.

### jazzisparis and LuthienAnarion — JIP LN NVSE

- Project: [JIP LN NVSE Plugin](https://www.nexusmods.com/newvegas/mods/58277) / [source](https://github.com/jazzisparis/JIP-LN-NVSE).
- Why credited: NVO adapted documented engine data layouts and contracts for ActorHitData, actors/forms, projectiles, ammunition, process slots, speed, gravity, lifetime, range, and related guarded hooks.
- Scope: NVO does not redistribute the JIP DLL or copy a JIP function implementation. The supplied source is GPLv3; retain NVOCombatCore's GPL and third-party notices.

### The Dormies, Demorome, Trooper/AVeryUncreativeUsername, and WallSoyGB/Wall_SoGB — ShowOff xNVSE

- Project: [ShowOff xNVSE Plugin](https://www.nexusmods.com/newvegas/mods/72541) / [source](https://github.com/Demorome/Showoff-NVSE).
- Why credited: NVO relies on and inspected ShowOff's projectile, explosion, destruction, timing, and decoding/event contracts.
- Upstream people explicitly credited for help or code: `lStewieAl`, `c6`, `Luthien`, `TommInfinite`, `jazzisparis`, and `karut`.
- Other upstream acknowledgements relevant to the provider project: JohnnyGuitar NVSE, JIP LN NVSE, lStewieAl's Tweaks, SUP NVSE, the xNVSE/example-plugin contributors, and `brofield` for SimpleINI.
- Scope: NVO calls the installed provider's public events and does not bundle ShowOff's implementation.

### Into the Rough contributors — itr-nvse / ITR NVSE

- Project: `itr-nvse`, supplied source licensed MIT under “Into the Rough contributors”.
- Why credited: NVO inspected ITR's pre-damage, actor-value, near-miss, event-dispatch, and float-slot contracts while defining guarded observation and pre-application boundaries.
- Scope: NVO observes or reasons from provider events; it does not bundle ITR's hooks or DLL. The exact supplied MIT notice is retained in `native/NVOCombatCore/LICENSE-ITR-MIT.txt`.

## Runtime projects and diagnostic sources

### carxt, c6, lStewieAl, and Wall_SoGB — JohnnyGuitar NVSE

- Project: [JohnnyGuitar NVSE](https://www.nexusmods.com/newvegas/mods/66927).
- Why credited: required by the alternative-start foundation and used as an installed runtime dependency; its source and releases were also inspected during diagnostics.
- Contributors/help named on the Nexus page: `jazzisparis`, `Nukem`, `korri123`, `Demorome`, `IntoTheRough`, `Stentorious`, `Wadel`, `AVeryUncreativeUsername`, `yvileapsis`, `W00Z`, `djhert`, `confused`, and `alex19EP`.

### lStewieAl — lStewieAl's Tweaks and Engine Fixes

- Project: [lStewieAl's Tweaks and Engine Fixes](https://www.nexusmods.com/newvegas/mods/66347).
- Why credited: source was inspected as corroborating engine research for projectile range/settings and compatibility. No Tweaks implementation is currently copied into NVOCombatCore.
- The Nexus page specifically credits `JazzIsParis` for groundwork/functions and `c6` for various tweaks; its broader description also thanks the NVSE team and other contributors.

## Inspected research sources — not currently incorporated

These credits acknowledge useful research and prevent future provenance loss. Listing here does **not** claim that their code, assets, or gameplay features are present in NVO.

- `Wombat` / `Woooombat` — Titans of The New West 2.0, version 2.1.51d: inspected as a candidate power-armour presentation module; no code or assets incorporated. The [September 17 assessment](reference/titans-2.1.51d/ASSESSMENT.md) records the source fingerprint, attribution and CC BY-NC-SA 4.0 notice. This repository update preserves that assessment; it is not a new upstream permission check.

- `LOW` / `LowbeeBob` — [Directional Shooting - NVSE](https://www.nexusmods.com/newvegas/mods/92443): inspected projectile-direction and controller-correction approaches. The page also credits `jazzisparis`, `Demorome`, `lStewieAl`, `carxt`, the xNVSE team, and other code sharers.
- `TommInfinite` — [SUP NVSE](https://www.nexusmods.com/newvegas/mods/73160): inspected a plugin example while looking for comparable engine sites; it did not provide the needed match and introduced no NVO dependency. The source itself marks portions from JIP LN, JohnnyGuitar, lStewieAl's Tweaks, and other libraries.
- `anhatthezoo` — AnhNVSE: source was searched for comparable engine sites during the same investigation; no matching code was adopted.
- `Ez0n3` and `Ian Patterson`/`ianpatt` — [NVSE-Plugins template](https://github.com/Ez0n3/NVSE-Plugins): reviewed as a build/example reference. No template implementation was copied into the current native plugin.
- `Emir` / `kodchhdayininyeri` — [BALLISTX C++ library](https://github.com/kodchhdayininyeri/BALLISTX): reviewed as a separate MIT-licensed ballistics library. No code from it is currently incorporated.
- `Mhillow` — [Bullet Tracers New Vegas](https://www.nexusmods.com/newvegas/mods/64198): inspected visual tracer records and assets as a possible presentation reference; not incorporated.
- `UserOfMods123` — [Improved Bullet Tracers - ESPless](https://www.nexusmods.com/newvegas/mods/98891): inspected its tracer approach and crash-related interpolation default; not incorporated. Its page requires permission for modification or asset reuse.
- `physicsgaming` — [Physics' Based Ballistics](https://www.nexusmods.com/newvegas/mods/82561), [Caliber Based Damage](https://www.nexusmods.com/newvegas/mods/82543), and [Physics' Based Spread](https://www.nexusmods.com/newvegas/mods/83049): inspected classification, configuration, projectile, damage, and spread approaches. They remain references; their independent gameplay owners/loaders are not part of NVO.
- `intotherough` — [Combat AI Tweaks](https://www.nexusmods.com/newvegas/mods/98454): retained as an external/reference AI project; its Nexus page requests credit for reuse. No implementation is copied into NVOCombatCore.
- `DwemerDynamics` — [DIALECTIC](https://www.nexusmods.com/newvegas/mods/99233): evaluated as an optional future conversation framework. It is not an NVO dependency or incorporated source, and its Nexus permissions require explicit permission for modification/asset reuse.

## Approved future donors — credit if a feature is actually adopted

These projects were inventoried or planned but have not yet supplied shipped NVO code/assets. Before adopting anything, record the exact files/records used and carry forward the following author and contributor credits.

- `Qolore7`, with `djhert` and `FinalCatalyst` — [Simple Bleeding - ESPless](https://www.nexusmods.com/newvegas/mods/92796): candidate bleeding/treatment logic. The author requires credit to themself and everyone mentioned in the description, and requires derivatives using the work to have open permissions.
- `S6S` / `Sweet6Shooter` — [New Blood](https://www.nexusmods.com/newvegas/mods/75666): candidate creature anatomy, weapon distinctions, bleeding, and impact reactions.
- `Qolore7` — [Transcendence - The Roleplaying Overhaul](https://www.nexusmods.com/newvegas/mods/90520): candidate equipment, combat-style, and progression reference. The author asks that the upstream mod be made a requirement where possible.
- `S6S` / `Sweet6Shooter` — [Vanilla SWEEP](https://www.nexusmods.com/newvegas/mods/81043): candidate individual weapon effects and balance reference. Its description additionally credits `Patchier`, `Panzermann11`, `phoenix0113`, `Hitman47101`, `Hopper31`, `Migck`, and `DoktorAkcel`, plus the project Just Enough Realism, for specific upstream work.
- `JazzIsParis` and `Xilandro` — [KEYWORDS](https://www.nexusmods.com/newvegas/mods/83088): candidate equipment classification support.
- `eezstreet`, with credit to `Imp of the Perverse` for the original idea — [Modern Ambient Temperature](https://www.nexusmods.com/newvegas/mods/71079): candidate atmospheric input for ballistics.
- `powerofthree` — [Base Object Swapper](https://www.nexusmods.com/newvegas/mods/83934): candidate equipment/world distribution support.
- `Wombat` / `Woooombat` — [Animated Greetings](https://www.nexusmods.com/newvegas/mods/96211) and [Idle Variety](https://www.nexusmods.com/newvegas/mods/85718): candidate later NPC presentation. Animated Greetings is published under CC BY-NC-SA 4.0.

## Tools and game

- `ElminsterAU` and the xEdit contributors — [xEdit](https://github.com/TES5Edit/TES5Edit): used for record inspection, cleaning, and plugin work. The bundled source files identify MPL 2.0 terms. xEdit is a development tool, not NVO authorship.
- Bethesda Game Studios and Obsidian Entertainment — Fallout: New Vegas and its data/engine, required to run the mod. No Bethesda or Obsidian ownership is claimed.

## Release rule

Every NVO release should ship this file together with `native/NVOCombatCore/THIRD-PARTY-NOTICES.md`, the applicable license texts, and the machine-readable ledger at `reference/source-credit-ledger.json`. The complete top-level reference-folder inventory is recorded in `reference/source-folder-inventory.json`; entries marked `deferred_uninspected` are not credits or approved donors. When new source is consulted or adapted, update both records before merging or distributing the result.
