# Combat packet 1 credits and provenance

Packet 1 contains original NVO startup code and a passive native bootstrap project. It does not contain adapted donor combat implementations, donor plugins or donor assets. Donor names below identify the approved sources for subsequent packets, not features already merged into NVO.esm.

Original NVO code supplied in this packet may be used, modified and redistributed with attribution to NVO. Retain applicable third-party notices when later donor material is incorporated. NVO's accepted design calls for open reuse permissions.

## Approved combat references

| Donor | Credit / source | Reuse note from planning |
|---|---|---|
| BallistX 5.4 | Ravuth — https://www.nexusmods.com/newvegas/mods/70341 | Modification/use with credit permitted; commercial sale restriction applies to donor assets. |
| Caliber Based Damage 3.0.1 | physicsgaming — https://www.nexusmods.com/newvegas/mods/82543 | Author states fully open permissions. |
| Physics' Based Ballistics 1.1.2 | physicsgaming — https://www.nexusmods.com/newvegas/mods/82561 | Author states open permissions. |
| Physics' Based Spread 1.0.0 | https://www.nexusmods.com/newvegas/mods/83049 | Reference identified; retain exact author notices when code is adapted. |
| Simple Bleeding 1.4.1 | Qolore7 — https://www.nexusmods.com/newvegas/mods/92796 | Credit the author and other credited contributors; derivative mod must have open permissions. |
| New Blood 2.75 archive | S6S / Sweet6Shooter — https://www.nexusmods.com/newvegas/mods/75666 | Author gives open adaptation permission. |
| Combat AI Tweaks 1.0.1 | https://www.nexusmods.com/newvegas/mods/98454 | Author permits reuse with credit; native plugin remains an external dependency. |
| Transcendence 1.3.0.1 | Qolore7 — https://www.nexusmods.com/newvegas/mods/90520 | Author permits inclusion/expansion and asks for an upstream requirement where possible. |
| Vanilla SWEEP 2.35 archive | S6S / Sweet6Shooter — https://www.nexusmods.com/newvegas/mods/81043 | Author gives open adaptation permission; supplied plugin has TTW masters. |
| KEYWORDS | https://www.nexusmods.com/newvegas/mods/83088 | Classification support, no code copied in this packet. |
| Modern Ambient Temperature | https://www.nexusmods.com/newvegas/mods/71079 | Optional later integration, no code copied in this packet. |
| Base Object Swapper | https://www.nexusmods.com/newvegas/mods/83934 | Later distribution support, no binary bundled. |
| Animated Greetings | https://www.nexusmods.com/newvegas/mods/96211 | Later presentation reference, no assets bundled. |
| Idle Variety | https://www.nexusmods.com/newvegas/mods/85718 | Later presentation reference, no assets bundled. |

Before incorporating a donor feature, carry its exact applicable author/contributor credits and file notices into that delivery. A folder label of open source is not substituted for those notices. Permission observations above came from the preceding planning inspection; this packet has not contacted any author.

## Extender interfaces

xNVSE and its contributors: https://github.com/xNVSE/NVSE. The native foundation uses the public Query/Load registration ABI. The interoperability field order and version constants were checked against the local headers pinned in sdk-reference.json. No xNVSE game-hook implementation is bundled.

JIP LN, JohnnyGuitar and ShowOff remain externally installed dependencies. The startup script queries their registered plugin names using xNVSE; it does not include or redistribute their binaries.

Existing Alternative Start attribution remains in the workspace root CREDITS.md.
